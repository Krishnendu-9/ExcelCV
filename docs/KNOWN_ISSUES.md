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
except through that proxy. That closes issue 1 without code changes. Issues 2 and 3
remain until the fix lands.
