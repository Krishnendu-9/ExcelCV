# Known issues

Read this before deploying ExcelCV anywhere other than your own machine.

---

## 1. Login and password-reset throttling trusts spoofable headers and can lock out any account

**Status: unfixed, deliberately.** The right fix depends on how the app is deployed:
which proxy sits in front of it, how many hops there are, and whether the server can be
reached without going through that proxy. No production deployment exists yet, so any
choice made now would be a guess. A wrong guess either stays spoofable or makes every
user share one throttle bucket (see [Why there is no safe default](#why-there-is-no-safe-default)).
Fix this when the deployment topology is decided, and before the app is exposed to the
public internet.

**Code:** `_client_fingerprint()`, `_login_throttle_keys()`, `_reset_throttle_keys()`,
`check_login_throttle()`, `record_login_failure()` and `check_password_reset_throttle()`
in [src/auth_utils.py](../src/auth_utils.py); the sign-in and forgot-password handlers in
[src/ui/auth_page.py](../src/ui/auth_page.py).

### What is wrong

**1. The client identity comes from headers the client controls.**
`_client_fingerprint()` uses the first non-empty value of `CF-Connecting-IP`,
`True-Client-IP`, `X-Real-IP`, then the *leftmost* entry of `X-Forwarded-For`. With no
proxy in front of the app, the client sets all of these. Behind a proxy that appends to
`X-Forwarded-For`, the leftmost entry is still whatever the client sent. Sending a new
value with every request gets a fresh `client:` bucket every time, so the per-client
limit does not limit anything.

**2. Anyone can lock any account, and keep it locked indefinitely.**
One login bucket is keyed by email address alone (`email:<address>`) and shared by every
client. Five failed attempts (`AUTH_LOGIN_MAX_ATTEMPTS`) within 10 minutes
(`AUTH_LOGIN_WINDOW_SECONDS`), from anyone, lock that address for 15 minutes
(`AUTH_LOGIN_LOCK_SECONDS`). The sign-in handler checks the lock *before* it checks the
password, so the owner's correct password is refused as well. Failures are not counted
while the lock holds, so an attacker waits for it to lapse and sends five more: five
requests every 15 minutes keep an account locked for as long as they like. All they need
is the email address.

**3. Anyone can block password resets for any address.**
The reset throttle also has an email-only bucket: three requests
(`AUTH_RESET_MAX_ATTEMPTS`) for an address within 30 minutes
(`AUTH_RESET_WINDOW_SECONDS`) block further requests for it. An attacker who spends those
three requests stops the owner from requesting a reset, which is the owner's way back in
while issue 2 keeps their sign-in locked.

**Related:** the counters are dictionaries in each server process's memory. They reset
when the process restarts, and they are not shared between processes or replicas.

### Proposed fix

1. **Identify the client from the connection unless a proxy is configured.** Default to
   `st.context.ip_address`. Streamlit takes it from Tornado's `remote_ip` and does not
   enable Tornado's `xheaders`, so it is the TCP peer address and no header can change it
   (checked against Streamlit 1.52). Read a forwarding header only when the deployment says
   to, for example a `TRUSTED_PROXY_HOPS=N` setting, ideally with a `TRUSTED_PROXY_CIDRS`
   list to check that the peer really is one of your proxies. For `X-Forwarded-For`, take
   the entry N hops from the right (the address your outermost trusted proxy saw), never
   the leftmost.
2. **Stop hard-locking accounts on email alone.** Keep the hard lock for the
   `email+client` bucket. For the email-only bucket, slow attempts down progressively
   instead of locking. Issue a signed "known device" cookie after a successful sign-in
   (the app already signs cookies with `SESSION_SECRET`) and exempt that browser from the
   account-level limit, so an attacker cannot lock the owner out of a browser they have
   used before.
3. **Key reset throttling on email+client**, with only a soft per-email limit: a delay, or
   a cap high enough that spending it cannot block the owner.
4. **Move throttle state out of process memory**, into a SQLite table or Redis, as soon as
   more than one process or replica runs.

### Deployment facts the fix depends on

- **What sits in front of the app:** nothing, a reverse proxy (nginx, Caddy), Cloudflare,
  a cloud load balancer, or a hosting platform's own proxy, and how many hops in total.
- **What each proxy does with the headers:** whether it overwrites a header (for example
  nginx `proxy_set_header X-Real-IP $remote_addr`) or appends to it (`X-Forwarded-For`),
  and whether it removes the ones it does not set.
- **Whether the server can be reached directly**, bypassing the proxy. If it can, no
  header can be trusted unless the peer address is checked against the proxy's address
  ranges (Cloudflare, for example, publishes its ranges).
- **Whether many legitimate users share one address:** office NAT, carrier-grade NAT on
  mobile networks, universities. This decides how strict a per-address limit can be.
- **How many server processes or replicas run**, which decides whether in-memory counters
  are good enough.

### Why there is no safe default

"Trust no headers" is right when users connect to the app directly. Behind a proxy,
though, `st.context.ip_address` is the proxy's address, so every user would share one
`client:` bucket, and five failures from anyone would lock everyone out. "Trust the
header" is right behind a proxy that sets it, and is today's spoofable behaviour
anywhere else. Part 1 of the fix therefore needs an explicit deployment setting, not a
default, which is why this waits for a real deployment.

### Before the fix

If you deploy behind a reverse proxy you control, configure it to **remove** any
`CF-Connecting-IP`, `True-Client-IP`, `X-Real-IP` and `X-Forwarded-For` headers the
client sent and set exactly one of them itself. Make sure the app cannot be reached
except through that proxy. That closes the spoofable-header problem without code
changes. The account lock and the blocked resets (problems 2 and 3 above) remain until
the fix lands.

---

## 2. The Gemini rate limit counts user actions, not API calls

**Status: unfixed, deliberately.** The right fix trades availability during outages
against a bounded call rate, and which matters more depends on the API key a deployment
uses: free tier or paid, and which models it has quota for. No deployment has chosen a
key yet.

**Code:** `_enforce_gemini_rate_limit()` and the model loop in `analyze_cv_with_gemini()`
in [src/gemini_client.py](../src/gemini_client.py); `generate_cover_letter_draft()` and
`_generate_json()` in [src/cover_letter/generator.py](../src/cover_letter/generator.py).

### What it is

`GEMINI_MAX_REQUESTS_PER_WINDOW` (default 20 per 60 seconds, per user) is charged once
per analysis or cover letter. Each of those then works through a fallback chain of
models from `preferred_models()`: four built-in models, plus `GEMINI_MODEL` when it is
set to a model not already in that list. A model can be tried twice:

| Path | Models failing with | API calls for one charged request |
|---|---|---|
| Analysis | timeouts, 500, 503 (retried once per model) | 2 per model, then 2 for an auto-picked model: 10, or 12 with a distinct `GEMINI_MODEL` |
| Analysis | quota errors, 429 (not retried, but the loop moves to the next model) | 1 per model, then 1: 5, or 6 with a distinct `GEMINI_MODEL` |
| Cover letter | any error, 429 included (every error is retried once) | 2 per model: 8, or 10 with a distinct `GEMINI_MODEL` |
| Either | nothing (the first model succeeds) | 1 |

So the real call rate can reach 10 to 12 times the configured limit, and it is highest
exactly when the API is already failing. A five-resume comparison is charged five times,
one per resume; the comparison runner skips the remaining resumes after the first quota
error, which limits the damage there. Model listing for the auto-pick runs once per
process and is cached.

### When it starts to matter

On a healthy API nearly every request succeeds on the first model, and the limit is
accurate. It matters during a Gemini outage or slowdown, and when the key is close to
its quota: the fallback chain then multiplies traffic, and on a paid key spend, at the
moment the provider can least absorb it, for every active user at once.

### What the fix depends on

- **Which models the key can use, and their quotas.** Gemini quotas are per model, so
  moving to another model after a 429 can succeed; that is why the chain exists. If the
  key only has quota on one or two models, the rest of the chain is wasted calls.
- **Free tier or paid.** On the free tier the cost is quota and 429s; on a paid key every
  retry is billed.
- **Availability versus a bounded rate.** The options are to charge the limiter per API
  attempt instead of per request, to stop the cover-letter chain on the first quota
  error (analysis already skips retries on 429), or to cap total attempts per request
  (for example 3). Each makes requests fail more often during outages in exchange for a
  call rate the configured limit actually describes.

---

## 3. Anyone can register any number of accounts

**Status: unfixed, deliberately.** The right controls depend on whether the deployment is
public, whether it has working email, and on the trusted-client-address question in
[§1](#1-login-and-password-reset-throttling-trusts-spoofable-headers-and-can-lock-out-any-account),
none of which is settled.

**Code:** `create_user()` in [src/auth_utils.py](../src/auth_utils.py); the Create Account
form in [src/ui/auth_page.py](../src/ui/auth_page.py).

### What it is

Registration takes a name, any email address and a password of at least 8 characters.
Nothing checks that the address belongs to the person registering (there is no
verification email), and nothing limits how many accounts one client creates (sign-in is
throttled; sign-up is not). Every Gemini limit in the app is per user, so each new
account brings its own 20 requests per minute, multiplied by the fallback chain in
[§2](#2-the-gemini-rate-limit-counts-user-actions-not-api-calls). Google sign-in requires
Google to report the email as verified, but Google accounts are cheap to create too.

### When it starts to matter

As soon as the app is reachable from the public internet with an API key whose quota or
budget you care about: a script can register accounts in a loop and spend from all of
them in parallel. On a private or invite-only deployment it does not matter.

### What the fix depends on

- **Whether the deployment is public.** For a private one, an invite list or an allowed
  email domain may be enough.
- **Working outgoing email.** Verification needs SMTP, which is optional today (an empty
  `SMTP_USER` disables email).
- **A trusted client address.** A sign-up throttle per address needs the proxy-aware
  client identity from §1, or it can be bypassed the same way the login throttle can.
- **Whether a captcha or similar check is acceptable** for the audience.
- A global budget (one counter for the whole app) would bound total spend whatever the
  number of accounts, but one abusive user could then exhaust it for everyone, and it
  needs shared state once more than one process runs.

---

## 4. Sign-in checks for AI features live in the UI layer

Analyze CV, Compare Resumes and Cover Letter require sign-in by not rendering their
forms for guests. That is sound in Streamlit, where the rendered page is the only way to
trigger an action: a guest has nothing to submit. If these features are ever exposed any
other way, for example behind an HTTP API, the check must move into the functions that
call Gemini, `analyze_cv_with_gemini()` and `generate_cover_letter_draft()`.

---

## 5. Dormant: AI bullet suggestions

**Status: dormant.** `suggest_cv_bullets()` in
[src/gemini_client.py](../src/gemini_client.py) still works and is guarded (input caps
and the rate limit), but nothing calls it. While it is dormant, nothing user-facing should
advertise it.

### How it went dormant

- The resume builder had an "AI Suggest" button on each work-experience entry. It sent
  the job title, company and existing bullets, showed four suggestions, and a "Use"
  button added one as a new bullet.
- Commit `3e0f3fb` (2026-05-08) appended new `_experience_section()` definitions to
  [src/ui/cv_builder_page.py](../src/ui/cv_builder_page.py) without the button. Python
  uses the last definition, so the button disappeared then.
- Commit `88f3f1a` (2026-05-17) deleted the shadowed old definition and the import.
- No commit message says it was removed on purpose, the new card kept the code that
  clears suggestion state, and project notes described the feature until 2026-05-25, so
  it looks accidental.

### What restoring it would take

- **UI** in `_experience_section()`: a suggest button per position; a list of
  suggestions with "Use" buttons that add a bullet through an `on_click` callback
  (writing to a widget's key after the widget is drawn raises a Streamlit error); and
  clearing suggestions in `_remove_position()` and `_clone_position()`. Roughly 50 lines.
  Suggestion state would not leak into saved CVs: saving uses an allow-list of keys,
  `_persistable_dynamic_keys()`.
- **The function**: make the JSON fallback accept a bare array
  (`_extract_json_from_text()` only recovers objects, so an array wrapped in prose fails
  with a raw parse error), and pass the position's Description with the bullets as
  context.
- **Decisions**: where the button sits in the current card design; what happens when the
  existing bullets exceed the 2,000-character context cap (today: rejected with a
  message); and whether four suggestions per click, each click charged one rate-limit
  slot, is the right use of the budget.
- **A check in a browser**: the card layout is driven by CSS keyed to container names,
  which unit tests do not see. This is why it was not restored blind.
- Rough size (an estimate): half a day including tests and that visual check.

---

## 6. Dormant: report enrichments that are built but not shown

**Status: dormant.** `analyze_cv_with_gemini()` in
[src/gemini_client.py](../src/gemini_client.py) builds seven extra structures into every
analysis. Since commit `ddb486d` the report page shows none of them. Six have no reader
anywhere in `src/` or `app.py`; Interview Prep is shown only on a page nothing links to.
While they are dormant, nothing user-facing should advertise them as report features.

**Code:** `build_recruiter_snapshot()`, `build_priority_action_plan()`,
`build_interview_prep_questions()`, `build_learning_roadmap()` and
`build_portfolio_checklist()` in [src/services/career_tools.py](../src/services/career_tools.py);
`build_jd_skill_matrix()` and `generate_section_rewrite_recommendations()` in
[src/services/scoring.py](../src/services/scoring.py). All seven are called from
`analyze_cv_with_gemini()`.

### Where the data goes

Each structure is stored in the analysis dict under its key. For a signed-in user the
whole dict is saved to the `Analysis.result` JSON column, and opening the analysis from
My Analyses loads it back. The report page's **Download JSON Export** serialises the whole
dict (`json.dumps(analysis)` in `_render_download_buttons()`), so all seven are in it.
The PDF and Markdown exports, `build_report_pdf_bytes()` and `build_report_md()`, include
none of them.

Two of them still shape what the report shows, before they are stored:
`_derive_deterministic_insight_fallbacks()` turns the skill matrix's Found, Partial and
Missing rows into Strengths and Missing Skills entries, and the first four rewrite
rationales into "Improve experience bullets: …" Suggestions. Deleting those two builders
would change the Insights lists.

### The structures

| Key | What it holds | Shape |
|---|---|---|
| `jd_skill_matrix` | Up to 24 job-description skills, each marked Found, Partial or Missing in the CV, with the CV line that best evidences it. Empty without a CV or a job description. | list of `{skill, status, confidence, evidence}`: status `Found` / `Partial` / `Missing`, confidence `High` / `Medium` / `Low`, evidence cut to 140 characters or "No direct evidence found in resume text." |
| `rewrite_recommendations` | Up to 8 experience bullets rewritten: bullets without a number (or, if there are none, lines with a repeated verb) get the first synonym for a repeated verb and the placeholder "by [X%], improving [outcome] by [Y]." | list of `{section, before, after, rationale}`; `section` is always "Experience / Projects" |
| `recruiter_snapshot` | A verdict from the final score (Strong Fit at 80 or more, Potential Fit at 65 or more, otherwise Needs Improvement) and one sentence naming the top strength and top gap. The strength and gap come from the model's raw `strengths` and `missing_skills`, not from the lists the report shows. | `{verdict, summary}` |
| `priority_action_plan` | Up to 8 fixed actions, each triggered by a threshold: parse rate under 80, Quantifying Impact under 70, Spelling & Grammar under 90, Repetition under 80, missing sections, missing skills, missing keywords. If none fire, one "Maintain Current Resume Quality" item. Priority, impact and effort are fixed per action, not computed. | list of `{title, priority, impact, effort, action}`; the middle three are `High` / `Medium` / `Low` |
| `interview_prep` | Up to 8 templated questions: one per missing skill (up to 5), one per strength (up to 3), then a fixed behavioural question and, with a job description, a fixed role-alignment question, while there is room. | list of `{type, question, why}` |
| `learning_roadmap` | One entry per missing skill, or per missing keyword when there are no missing skills, up to 6. The target and plan are the same text for every entry. | list of `{skill, target, plan}` |
| `portfolio_checklist` | Four checks (Experience section, Skills section, contact details, header links), each listed as done or to do, plus "Apply top suggestions before final submission" when there are suggestions. | `{completed, missing}`, two lists of strings |

### How they stopped being shown

- Commit `04be65f` (2026-04-23) added a card for each of the seven to the report's
  Insights group.
- Commit `ddb486d` (2026-05-11, "Analyze page restructure done") deleted the six card
  renderers and the Portfolio Checklist card, leaving Insights with Strengths, Missing
  Skills, Missing Keywords and Suggestions. The builders and the dict keys stayed. The
  commit message does not say whether removing the cards was intended, and the history
  does not show it.
- Interview Prep also has its own page, `?page=interview-prep`, rendered by
  `render_static_page()` in [src/ui/static_pages.py](../src/ui/static_pages.py) from the
  latest analysis in the session. The footer linked to it until commit `2a26cbb`
  (2026-05-18, "restructure CV builder") removed the link. Nothing links to it now, so it
  is reachable only by typing the URL. It does not require sign-in.

### What restoring them would take

- **The renderers are in history.** `git show ddb486d^:src/ui/report.py` contains the six
  card renderers; the Portfolio Checklist card used `_build_list_card()`, which still
  exists. The renderers read the same field names the builders return today, and every
  CSS class they use is still in the current stylesheets. Since `ddb486d` the builders'
  output shapes have not changed; `650e0d7` changed which skills the matrix lists and how
  it decides their status.
- **Fix the recruiter snapshot first.** It is built from the model's raw lists
  (`parsed | {"match_score": match_score}` in `analyze_cv_with_gemini()`), so restored as
  it is, its top strength and gap would disagree with the Insights lists on the same page.
  Pass it the merged lists.
- **Decisions**: the action plan, the roadmap and the interview questions are built from
  the same missing skills, missing keywords and suggestions the Insights lists already
  show, and the portfolio checklist repeats Sections and ATS Essentials checks, so decide
  which cards add enough to justify the length. Decide whether the Insights percentage
  (`insights_score`, over four areas today) should count the restored cards; before
  `ddb486d`, pending portfolio items counted as Insights issues. For Interview Prep, choose
  between a report card, a link to its page, or both.
- **A check in a browser**: `report.py` has changed in five commits since `ddb486d`,
  including a layout and theme update (`ae1f60a`), so how the old cards sit in today's
  layout can only be judged by looking.
- No size estimate: the code exists, but the work is mostly the decisions and the visual
  check above, and neither can be sized from the code.
- When a card is restored, update the matching guard in
  [tests/test_feature_claims.py](../tests/test_feature_claims.py); it skips itself for any
  structure that has a reader again.
