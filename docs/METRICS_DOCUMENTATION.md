# CV Review Metrics Documentation

Last verified against the repository on **2026-11-06**.

This document explains how each metric and score is calculated in the ExcelCV application.

## Overview

Every score on the report page is computed in code from the CV text and job description. Google Gemini is called for every analysis, but its numbers do not reach the report page; see [What the AI model contributes](#what-the-ai-model-contributes).

- **Metric computations** live in [`src/services/scoring.py`](../src/services/scoring.py) as `calculate_*` functions (`calculate_ats_parse_rate`, `calculate_quantifying_impact`, `calculate_repetition`, `calculate_spelling_grammar`, `calculate_bullets_consistency`, `calculate_sections`, `calculate_sections_order`, `calculate_contact_info`, `calculate_ats_essentials`, `calculate_tailoring`, `calculate_file_name_quality`). The Quantifying Impact, Repetition and Spelling & Grammar statuses are derived via `get_metric_status(score, ok_min, warn_min)` in the same module.
- **Final weighted score** ("Your Score") is computed by `calculate_final_score_breakdown` ([`src/services/scoring.py`](../src/services/scoring.py)). [`src/gemini_client.py`](../src/gemini_client.py)'s `analyze_cv_with_gemini` runs every metric, calls the model, and assembles the `analysis` dict.
- **Report UI groups** are four: **Content**, **Sections**, **ATS Essentials**, **Insights**. Tailoring is not a UI group; it contributes as the **JD Alignment** component (weight 0.25) inside the final weighted score. See [`docs/report_page.md`](report_page.md) for the report-page layout.
- **`issue_count()`** for the score card lives in [`src/ui/common.py`](../src/ui/common.py).

> **Note on legacy names.** Earlier revisions of this doc referenced `_calculate_*` helpers inside `src/gemini_client.py` and an `src/ui_components.py` module. The scoring helpers now live in `src/services/scoring.py` as public functions with no leading underscore. `src/ui/ui_components.py` is only a re-export facade; the report page is rendered by `src/ui/report.py`. Earlier revisions also described scores as AI-assisted; none are.

---

## What the AI model contributes

`analyze_cv_with_gemini` asks Gemini for a JSON object containing `match_score`, `strengths`, `missing_skills`, `suggestions`, `missing_keywords`, `subscores` and a score for every metric below. Almost all of it is discarded:

| Model output | What happens to it |
|--------------|--------------------|
| `match_score` | Discarded. "Your Score" is `calculate_final_score_breakdown`'s `final_score`. |
| `content_metrics`, `sections_metrics`, `ats_essentials_metrics`, `tailoring_metrics` | Discarded. Every metric is computed in code. |
| `strengths`, `missing_skills`, `suggestions`, `missing_keywords` | Not shown. The report's Insights lists are built in code by `_derive_deterministic_insight_fallbacks` from the metrics, the tailoring details, the JD skill matrix and the rewrite recommendations. |
| `subscores` (`skills_alignment`, `experience_alignment`, `ats_readiness`) | Kept. Each falls back to the final score when the model omits it or its JSON cannot be parsed. They are printed in the downloadable PDF and Markdown reports. The report page reads them only as stand-ins when a stored older analysis lacks a Sections or ATS Essentials score. |

The model's own `strengths` and `missing_skills` also supply the top strength and top gap in `recruiter_snapshot`, which is stored in the `analysis` dict but not displayed anywhere.

The analysis still requires the model call to succeed: if every Gemini model fails, `analyze_cv_with_gemini` raises an error and no report is produced.

---

## Content Metrics

The Content category evaluates the quality and readability of resume content. Its sub-metrics are computed in code only.

### 1. ATS Parse Rate (0-100)

**Description**: Estimates how well an Applicant Tracking System could extract text from the resume, from the amount of text extracted.

**Calculation Method** — `calculate_ats_parse_rate(cv_text)`:
- Base score from extracted text length:
  - ≥800 characters: 85
  - ≥400 characters: 70
  - ≥100 characters: 50
  - <100 characters: 20
- +10 if any of experience, education, skills, summary, objective or contact appears in the text; capped at 100.

**Status Thresholds** (detail card badge):
- **80-100**: "Excellent" (green)
- **60-79**: "Good" (amber)
- **0-59**: "Needs Improvement" (amber)

**Why It Matters**: ATS systems must be able to extract and parse your resume content to evaluate your qualifications. Low parse rates result in automatic rejection before human review.

---

### 2. Quantifying Impact (0-100)

**Description**: Measures the share of experience and project bullet points that contain a number or measurable result.

**Calculation Method** — `calculate_quantifying_impact(cv_text)`:
- Extracts bullet points from the experience and project sections, rejoining lines that PDF extraction split.
- A bullet counts as quantified if a digit remains after dates and years are removed, or if it says "million", "billion" or "trillion". Words like "improved" or "reduced" without a number do not count.
- **Score** = 40 + 0.6 × (percentage of bullets quantified), capped at 100. 40 when no bullets are found.
- Details list up to 15 bullets that lack a number.

**Status Thresholds**:
- **70-100**: "ok" (No issues)
- **50-69**: "warn" (Review)
- **0-49**: "error" (Review)

**Why It Matters**: Quantified achievements provide concrete evidence of your impact and make your resume more compelling to both ATS systems and hiring managers.

---

### 3. Repetition (0-100)

**Description**: Flags action verbs and descriptive words used too often. Higher scores mean less repetition.

**Calculation Method** — `calculate_repetition(cv_text)`:
- Counts only words that have synonym suggestions in `WORD_SYNONYMS` (such as "developed", "managed", "led"), excluding "-ing" forms. Domain terms such as "data" or "system" are ignored.
- A word is flagged when it appears 3 or more times.
- **Score** = 100 − 12 for each use beyond the second of every flagged word, clamped to 0–100. 100 when the CV has fewer than 20 words.
- Details name the most repeated words with up to three synonyms each.

**Status Thresholds**:
- **80-100**: "ok" (No issues)
- **60-79**: "warn" (Review)
- **0-59**: "error" (Review)

**Why It Matters**: Excessive repetition makes resumes appear unprofessional and reduces readability. Variety in language demonstrates strong communication skills.

---

### 4. Spelling & Grammar (0-100)

**Description**: A formatting-consistency heuristic. Despite the name, it does not check spelling or grammar; there is no spell-check library.

**Calculation Method** — `calculate_spelling_grammar(cv_text)`, starting from 100:
- **Double spaces** between words: −2 each, at most −15. Runs of three or more spaces are ignored as PDF column alignment.
- **All-caps words** of 4+ letters, excluding known acronyms and section headers: if there are more than 3, −1 each, at most −10.
- **Inconsistent bullet characters** (more than two kinds) and **bullets without ending punctuation** (more than two) are listed in `issues_list` but do not change the score.

**Status Thresholds**:
- **90-100**: "ok" (No issues)
- **70-89**: "warn" (Review)
- **0-69**: "error" (Review)

**Why It Matters**: Inconsistent formatting creates a poor first impression and suggests lack of attention to detail.

---

## Sections Metrics (0-100)

**Description**: Evaluates the presence and completeness of standard resume sections.

**Calculation Method** (computed in code only):
- **Backend:** `calculate_sections(cv_text)` in `src/services/scoring.py` checks CV text for section-related keywords:
  - **Contact**: contact, email, phone, mobile, address, @, linkedin
  - **Experience**: experience, work history, employment, professional experience, career
  - **Education**: education, academic, degree, university, college, bachelor, master, phd
  - **Skills**: skills, technical skills, competencies, expertise
  - **Summary/Objective**: summary, objective, profile, about me, professional summary
- **Score:** 20 points per section found (max 100). Details include `has_contact`, `has_experience`, `has_education`, `has_skills`, `has_summary` and `missing_sections` list.
- The model's `sections_metrics` value is discarded.

**Why It Matters**: Standard sections ensure ATS systems can properly categorize and extract information. Missing sections reduce parseability and professional appearance.

---

## ATS Essentials Metrics (0-100)

**Description**: Evaluates ATS-friendly formatting and structural requirements.

**Calculation Method** (computed in code only):
- **Backend:** `calculate_ats_essentials(cv_text, file_name="", file_size_bytes=0)` in `src/services/scoring.py`:
  - **Section headers present**: CV text checked for standard section keywords (experience, education, skills, summary, objective, contact, work, employment).
  - **Text-based**: Assumed true when we have extracted text.
  - **Score:** Base 60 + 25 if section headers found + 10 for text-based + 5 for word count ≥ 200; capped at 100.
  - **Details:** `standard_formatting`, `keyword_density`, `section_headers_present`, `text_based`, `issues` list, plus `file_format`, `email_check` and `header_links`. Keyword density, file format, email and links are reported but do not change the score.
- The model's `ats_essentials_metrics` value is discarded.

**Why It Matters**: ATS systems rely on standard formatting and structure to parse resumes. Non-standard formats often result in parsing failures and automatic rejection.

---

## Tailoring Metrics (0-100)

**Description**: Measures how well the resume is tailored to the specific job description.

**Calculation Method** (computed in code only):

`calculate_tailoring(cv_text, job_desc)` in `src/services/scoring.py` returns `(alignment_score, details)`. The score is a weighted mix of three rates, then scaled down if the job description is too short to judge against.

- **Early exits:** no job description → 80; no CV text → 0; a job description that yields no usable terms → 70.

1. **Collect job-description terms** from four sources (all lower-cased):
   - *Tech phrases*: a fixed list of multi-word patterns such as "machine learning", "ci/cd", "rest api", "data pipeline".
   - *Requirement phrases*: comma-separated items after cues such as "must have:", "requiring", "experience with", "knowledge of" and "with"; up to 30, each at most five words.
   - *Single terms*: words of 3+ characters (letters, digits, `+`, `#` and `.` are allowed, so "c++" and "node.js" count), minus stop words and generic job-ad words such as "experience", "required" and "team".
   - *Role baseline terms*: when the job description names a known role (project / program / delivery manager; DevOps / SRE; cloud engineer / architect / administrator; data engineer / analyst / scientist), a fixed list of skills that role is expected to have, up to 16.

   Job titles ("cloud engineer", "blockchain developer") are never counted as terms, and a single word that is only part of a multi-word phrase is not counted on its own. A term matches if it appears verbatim in the CV; a multi-word term also matches if at least max(2, half its words rounded up) of its words appear. Multi-word matches with some words missing are listed in `partial_skills`.

2. **Component rates** (each 0–100):
   - **Keyword match rate** = matched ÷ (matched + missing), over tech phrases, requirement phrases and single terms. 70 if there are none.
   - **Skill match rate** = matched ÷ (matched + missing), over the same three sources plus the role baseline terms. Falls back to the keyword match rate if there are none.
   - **Experience relevance** = round(0.6 × skill match + 0.4 × keyword match). It is derived from the other two rates, not measured separately, and uses the skill match rate after the role-baseline adjustment in step 3.

3. **JD signal count** = (distinct non-stop-word terms of 3+ characters) + 2 × (tech phrases) + (requirement phrases). It is returned as `jd_specificity.signal_count` and controls two separate adjustments:
   - **Below 8, and only when a known role was recognised:** skill match = round(0.8 × skill match + 0.2 × share of role baseline terms found in the CV). A title-only job description is then judged partly on the skills that role normally needs.
   - **Below 6:** the specificity guardrail in step 5.

4. **Raw alignment** = 0.35 × keyword match + 0.45 × skill match + 0.20 × experience relevance, truncated to an integer and clamped to 0–100. Returned as `raw_alignment_score`.

5. **Specificity guardrail.** When the signal count is below 6, the raw alignment is multiplied by a factor of 0.55 + min(0.30, 0.06 × signal count): 0.55 at 0 signals, rising by 0.06 per signal to 0.85 at 5. At 6 or more signals the factor is 1.0. The final score is round(raw alignment × factor). The factor only scales the score down; it is not a floor. `jd_specificity.status` is `low` whenever the factor applies (below 0.9) and `good` otherwise.

**Why a short job description scores lower.** A job description that is only a title, such as "Cloud Engineer", has 2 signals ("cloud", "engineer"), so its score is multiplied by 0.67. A title says almost nothing about what the job needs, so even a CV that covers all of it is weak evidence of fit. In the specificity test in `tests/test_scoring_core.py`, a cloud-engineering CV scores a raw 62 against "Cloud Engineer", which the guardrail reduces to 42. The guardrail lowers the short description's own score. It does not guarantee a lower score than a detailed description gives: against the test's detailed Cloud Engineer description (21 signals, factor 1.0), the same CV scores 36, because that description asks for Terraform, monitoring and incident response, which the CV lacks.

**Details returned:** `keyword_match_rate`, `skill_match_rate`, `experience_relevance`, `raw_alignment_score`, `alignment_score`, `matched_keywords`, `missing_keywords`, `required_skills`, `matched_skills`, `missing_skills`, `partial_skills`, `role_baseline` (`matched`, `missing`), and `jd_specificity` (`status`, `signal_count`, `factor`, `details`). The early exits return a reduced set: `keyword_match_rate`, `skill_match_rate`, `experience_relevance`, `alignment_score`, `matched_keywords` and `missing_keywords`, plus `required_skills`, `matched_skills` and `missing_skills` when no usable terms were found.

- The model's `tailoring_metrics` value is discarded. The score feeds the **JD Alignment** component of `calculate_final_score_breakdown`.

**Why It Matters**: Tailored resumes significantly increase chances of passing ATS screening and impressing hiring managers. Generic resumes are often rejected in favor of tailored applications.

---

## Category Scores

The report sidebar shows four categories, computed in `render_report_page` (`src/ui/report.py`):

- **Content**: unweighted average of ATS Parse Rate, Quantifying Impact, Repetition and Spelling & Grammar, plus Bullets Consistency when present.
- **Sections**: the Sections Metrics score.
- **ATS Essentials**: the ATS Essentials Metrics score.
- **Insights**: the share of four insight areas that are clean: Strengths present, and no Missing Skills, Missing Keywords or Suggestions. Each clean area is worth 25.

Tailoring has no category; its score appears only as the JD Alignment component of the final score.

**Category Score Color Coding** (`get_score_color_class`):
- **80-100**: green
- **60-79**: yellow
- **0-59**: red

---

## Final Score ("Your Score", 0-100)

**Description**: The overall score shown on the report page's score card.

**Calculation Method** — `calculate_final_score_breakdown`: a weighted sum of component scores, rounded and clamped to 0–100. Content Quality is the average of the content sub-metrics, as in the Content category.

| Component | With a job description | Without a job description |
|-----------|-----------------------|---------------------------|
| Content Quality | 0.30 | 0.35 |
| JD Alignment (Tailoring) | 0.25 | — |
| Sections | 0.15 | 0.25 |
| ATS Essentials | 0.15 | 0.25 |
| Contact Completeness | 0.15 | 0.15 |

Every page that runs an analysis (single analysis and comparison) rejects a blank job
description before scoring, so the app always uses the first column. The second is
reachable only by calling `calculate_final_score_breakdown` or `analyze_cv_with_gemini`
directly with no job description; `tests/test_scoring_core.py` covers it, and
`tests/test_jd_required.py` fails if a page stops requiring a job description.

The breakdown is returned as `analysis["score_breakdown"]` (`mode`, `components`, `formula`) and shown under the score.

**Score ring color**: green at 80 or more, amber at 60–79, red below 60.

---

## Data Sources

1. **Programmatic calculations** (`src/services/scoring.py`): every score, status, category and the final score; the Insights lists.
2. **Google Gemini** (`src/gemini_client.py`): the three subscores in the downloadable PDF and Markdown reports. See [What the AI model contributes](#what-the-ai-model-contributes).

---

## Implementation Reference (Where the Numbers Come From)

This section maps each value on the report page to its source and code location, for developers and project documentation.

### Data flow

1. `analyze_cv_with_gemini` validates the inputs and sends the CV text and job description to the Google Gemini API.
2. The model returns a JSON object, parsed in **`src/gemini_client.py`**. Only its `subscores` are kept.
3. Every metric is computed in code from the CV text and job description; the model's values for them are discarded.
4. `calculate_final_score_breakdown` computes the final score, stored as `analysis["match_score"]`; the Insights lists are built in code.
5. The report page (**`src/ui/report.py`**, `render_report_page`) reads the final `analysis` dict and displays it.

**Main files:**

| File | Responsibility |
|------|----------------|
| `src/gemini_client.py` | API call, prompt, response parsing; `analyze_cv_with_gemini` runs the metrics and assembles the `analysis` dict |
| `src/services/scoring.py` | All `calculate_*` metrics, `get_metric_status`, `calculate_final_score_breakdown` |
| `src/ui/common.py` | `issue_count()`, `get_score_color_class()`, shared UI helpers |
| `src/ui/report.py` | Sidebar + detail-card rendering for the report page (category scores computed here) |
| `src/services/reporting.py` | The downloadable PDF and Markdown reports, both including the model's subscores |
| `app.py` | Routes to `render_report_view()`; stores analysis in session state |

### "Your Score" (e.g. 72/100)

- **Source:** Application logic. It is the `final_score` of `calculate_final_score_breakdown`; see [Final Score](#final-score-your-score-0-100).
- **Backend:** `analyze_cv_with_gemini` stores it as `analysis["match_score"]`. The prompt also asks the model for a `match_score`, but that value is never used: `calculate_final_score_breakdown` always returns a `final_score`.
- **UI:** `score = analysis.get("match_score", 0)` in `render_report_page()`, shown in the score ring.

### "X issues" (e.g. 16 issues)

- **Source:** Application logic only. The lists it counts are built in code.
- **Formula** (in `src/ui/common.py`, function `issue_count()`):

  ```
  issues = 0
  issues += len(analysis["missing_keywords"])
  issues += len(analysis["missing_skills"])
  issues += number of non-empty strings in analysis["suggestions"]
  if analysis["match_score"] < 70: issues += 1
  return max(issues, 0)
  ```

### Content category score (e.g. 86%)

- **Source:** Application logic, from the content sub-metrics.
- **Formula** (in `src/ui/report.py` `render_report_page`): **Content score = unweighted average** of `ats_parse_rate`, `quantifying_impact.score`, `repetition.score`, `spelling_grammar.score`, plus `bullets_consistency.score` when present (so it's a 4- or 5-way average). Mirrors the "Content Quality" component in `calculate_final_score_breakdown`. Displayed next to the "Content" heading.

### Content sub-items (ATS Parse Rate, Quantifying Impact, Repetition, Spelling & Grammar, Bullets Consistency)

- All five content sub-metrics are computed in code in `src/services/scoring.py`; see [Content Metrics](#content-metrics) for the formulas:
  - **ATS Parse Rate:** `calculate_ats_parse_rate(cv_text)` – text length plus a section-keyword bonus.
  - **Quantifying Impact:** `calculate_quantifying_impact(cv_text)` – share of experience bullets containing a number; score 40–100.
  - **Repetition:** `calculate_repetition(cv_text)` – action verbs used 3+ times; higher score = less repetition. Details suggest synonyms.
  - **Spelling & Grammar:** `calculate_spelling_grammar(cv_text)` – deductions for double spaces and excessive all-caps words. No spell-check library.
  - **Bullets Consistency:** `calculate_bullets_consistency(cv_text)` – flags experience bullets outside the 15–45-word band (too short / too long); score = 100 − 55 × (share flagged). Fewer than two bullets gives 75 with `status="ok"` and a neutral message.
- The model's `content_metrics` values are discarded.
- **Status (No issues / Review):** Quantifying Impact, Repetition and Spelling & Grammar statuses come from `get_metric_status(score, ok_min, warn_min)` in `src/services/scoring.py`. The report page applies the ATS Parse Rate thresholds itself. Bullets Consistency sets its own status: `warn` when up to 40% of bullets are out of range, `error` above that.

  | Metric | ok (No issues) | warn (Review) | error (Review) |
  |--------|----------------|---------------|----------------|
  | ATS Parse Rate | score ≥ 80 | score ≥ 60 and &lt; 80 | score &lt; 60 |
  | Quantifying Impact | score ≥ 70 | score ≥ 50 and &lt; 70 | score &lt; 50 |
  | Repetition | score ≥ 80 | score ≥ 60 and &lt; 80 | score &lt; 60 |
  | Spelling & Grammar | score ≥ 90 | score ≥ 70 and &lt; 90 | score &lt; 70 |

  UI maps: `ok` → "No issues", `warn`/`error` → "Review", `lock` → "Locked".

### Sections %, ATS Essentials %, Tailoring %

- **Source:** Computed in code only. No metric is shown on the frontend without a computed score.
- **Sections:** `calculate_sections(cv_text)` – checks for Contact, Experience, Education, Skills, Summary/Objective via keywords; 20 points per section; details include `missing_sections`.
- **ATS Essentials:** `calculate_ats_essentials(cv_text, file_name, file_size_bytes)` – base 60, plus bonuses for section headers, text-based input and word count ≥ 200; capped at 100. Details include `issues` and report keyword density, file format, email and header links, which do not affect the score.
- **Tailoring:** `calculate_tailoring(cv_text, job_desc)` – weighted mix of keyword match, skill match and experience relevance, scaled down when the job description is short or generic; see [Tailoring Metrics](#tailoring-metrics-0-100).
- UI reads `analysis["sections_metrics"]["score"]`, etc. No "Unlock Full Report" or paywall; the app is fully free.

### Summary table (source and location)

| Metric / label | Source | Where computed / read |
|----------------|--------|------------------------|
| Your Score (match_score) | App | services/scoring.calculate_final_score_breakdown; ui/report (display, score ring) |
| X issues | App | ui/common.issue_count() |
| Content % | App | ui/report `render_report_page` (4- or 5-way average) |
| ATS Parse Rate score | App | services/scoring.calculate_ats_parse_rate |
| ATS Parse Rate status | App (from score) | ui/report (thresholds 80 / 60) |
| Quantifying Impact | App | services/scoring.calculate_quantifying_impact; status from get_metric_status(70, 50) |
| Repetition | App | services/scoring.calculate_repetition; status from get_metric_status(80, 60) |
| Spelling & Grammar | App | services/scoring.calculate_spelling_grammar; status from get_metric_status(90, 70) |
| Bullets Consistency | App | services/scoring.calculate_bullets_consistency |
| Sections % | App | services/scoring.calculate_sections; ui/report (display) |
| Sections Order | App | services/scoring.calculate_sections_order |
| ATS Essentials % | App | services/scoring.calculate_ats_essentials; ui/report (display) |
| Contact Completeness | App | services/scoring.calculate_contact_info |
| File Name Quality | App | services/scoring.calculate_file_name_quality |
| Tailoring / JD Alignment % | App | services/scoring.calculate_tailoring(cv_text, job_desc); used as `jd_alignment` component in calculate_final_score_breakdown |
| Insights % | App | ui/report `render_report_page` (share of clean insight areas) |
| Final weighted score | App | services/scoring.calculate_final_score_breakdown (weights: jd_aligned vs no_jd mode) |
| Skills / Experience Alignment, ATS Readiness | Gemini | gemini_client (parse); services/reporting (PDF and Markdown reports) |

---

## Notes

- **Fully free:** There is no "Unlock Full Report" or paywall; all metrics are computed and shown without restriction.
- **No display without logic:** every category and metric on the report page has a score computed in code; the frontend only shows categories that have one.
- All scores are integers on a 0-100 scale.
- Status thresholds differ by metric; see the table above.
- Scores are deterministic: the same CV and job description always produce the same report-page scores.
- Every metric and the final score are computed in code from the full CV and job description. The model's subscores also see the full text: inputs are capped by `GEMINI_MAX_CV_CHARS` (default 26,624) and `GEMINI_MAX_JD_CHARS` (default 40,000), and anything longer is rejected with a message instead of being cut

---

## Future Enhancements

- Optional spell-check library integration for Spelling & Grammar
- Enhanced repetition detection with synonym analysis
- Industry-specific metric weighting
- Comparative scoring against industry benchmarks
- Historical tracking and improvement recommendations
