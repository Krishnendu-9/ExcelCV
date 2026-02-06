# CV Review Metrics Documentation

This document explains how each metric and score is calculated in the AI CV Reviewer application.

## Overview

The CV review system analyzes resumes against job descriptions using Google Gemini AI and programmatic calculations. Metrics are organized into four main categories: Content, Sections, ATS Essentials, and Tailoring.

---

## Content Metrics

The Content category evaluates the quality and readability of resume content. It includes the following sub-metrics:

### 1. ATS Parse Rate (0-100)

**Description**: Measures how well Applicant Tracking Systems (ATS) can extract and parse information from the resume.

**Calculation Method**:
- **Programmatic Component (Base Score)**:
  - Text length analysis:
    - ≥800 characters: 85 points (Good text extraction)
    - ≥400 characters: 70 points (Moderate text extraction)
    - ≥100 characters: 50 points (Poor text extraction)
    - <100 characters: 20 points (Very poor text extraction)
  - Section detection: +10 points if standard sections are detected (Experience, Education, Skills, Summary, Objective, Contact)

- **AI Analysis Component**: The AI model analyzes:
  - Text-based vs scanned document quality
  - Formatting clarity and consistency
  - Structural organization
  - Font readability and standard formatting usage

- **Final Score**: Average of programmatic base score and AI-provided parse rate

**Status Thresholds**:
- **80-100**: Excellent (Green badge - "Excellent")
- **60-79**: Good (Yellow badge - "Good")
- **0-59**: Needs Improvement (Red badge - "Needs Improvement")

**Why It Matters**: ATS systems must be able to extract and parse your resume content to evaluate your qualifications. Low parse rates result in automatic rejection before human review.

---

### 2. Quantifying Impact (0-100)

**Description**: Evaluates how well achievements and experiences are quantified with numbers, metrics, and measurable results.

**Calculation Method**:
The AI analyzes the resume for:
- Presence of numbers/metrics in achievement statements
- Use of percentages, dollar amounts, timeframes, quantities
- Specific, measurable results (e.g., "increased sales by 25%", "managed team of 10", "reduced costs by $50K")
- Frequency of quantified statements throughout the resume

**Score Calculation**:
- Higher scores indicate more frequent and meaningful use of quantifiable metrics
- Scores consider both quantity and relevance of metrics used

**Status Thresholds**:
- **70-100**: "ok" status (No issues - Green badge)
- **50-69**: "warn" status (Review - Yellow badge)
- **0-49**: "error" status (Review - Red badge)

**Why It Matters**: Quantified achievements provide concrete evidence of your impact and make your resume more compelling to both ATS systems and hiring managers.

---

### 3. Repetition (0-100)

**Description**: Measures word and phrase repetition frequency in the resume.

**Calculation Method**:
The AI analyzes:
- Frequency of repeated words and phrases
- Overuse of certain terms or action verbs
- Redundancy in job descriptions and bullet points
- Word diversity and vocabulary variety

**Score Calculation**:
- **Higher scores = Less repetition** (better variety)
- Score decreases with increased repetition frequency
- Analysis considers both exact word repetition and semantic repetition

**Status Thresholds**:
- **80-100**: "ok" status (No issues - Green badge)
- **60-79**: "warn" status (Review - Yellow badge)
- **0-59**: "error" status (Review - Red badge)

**Why It Matters**: Excessive repetition makes resumes appear unprofessional and reduces readability. Variety in language demonstrates strong communication skills.

---

### 4. Spelling & Grammar (0-100)

**Description**: Evaluates spelling accuracy and grammatical correctness throughout the resume.

**Calculation Method**:
The AI checks for:
- Spelling errors and typos
- Grammatical mistakes (subject-verb agreement, tense consistency, etc.)
- Punctuation errors
- Professional writing standards

**Score Calculation**:
- Starts at 100 and deducts points for each error found
- Weighted by error severity and frequency
- Context-aware analysis (technical terms, company names, etc. are considered)

**Status Thresholds**:
- **90-100**: "ok" status (No issues - Green badge)
- **70-89**: "warn" status (Review - Yellow badge)
- **0-69**: "error" status (Review - Red badge)

**Why It Matters**: Spelling and grammar errors create a poor first impression and suggest lack of attention to detail. Many resumes are rejected based on these errors alone.

---

## Sections Metrics (0-100)

**Description**: Evaluates the presence and completeness of standard resume sections.

**Calculation Method** (programmatic in backend; optional AI blend):
- **Backend:** `_calculate_sections(cv_text)` in `gemini_client.py` checks CV text for section-related keywords:
  - **Contact**: contact, email, phone, mobile, address, @, linkedin
  - **Experience**: experience, work history, employment, professional experience, career
  - **Education**: education, academic, degree, university, college, bachelor, master, phd
  - **Skills**: skills, technical skills, competencies, expertise
  - **Summary/Objective**: summary, objective, profile, about me, professional summary
- **Score:** 20 points per section found (max 100). Details include `has_contact`, `has_experience`, `has_education`, `has_skills`, `has_summary` and `missing_sections` list.
- If the AI also returns `sections_metrics.score`, the final score is the average of programmatic and AI.

**Why It Matters**: Standard sections ensure ATS systems can properly categorize and extract information. Missing sections reduce parseability and professional appearance.

---

## ATS Essentials Metrics (0-100)

**Description**: Evaluates ATS-friendly formatting and structural requirements.

**Calculation Method** (programmatic in backend; optional AI blend):
- **Backend:** `_calculate_ats_essentials(cv_text)` in `gemini_client.py`:
  - **Section headers present**: CV text checked for standard section keywords (experience, education, skills, summary, objective, contact, work, employment).
  - **Text-based**: Assumed true when we have extracted text.
  - **Score:** Base 60 + 25 if section headers found + 10 for text-based + up to 5 for word count ≥ 200; capped at 100.
  - **Details:** `standard_formatting`, `keyword_density`, `section_headers_present`, `text_based`, `issues` list.
- If the AI also returns `ats_essentials_metrics.score`, the final score is the average of programmatic and AI.

**Why It Matters**: ATS systems rely on standard formatting and structure to parse resumes. Non-standard formats often result in parsing failures and automatic rejection.

---

## Tailoring Metrics (0-100)

**Description**: Measures how well the resume is tailored to the specific job description.

**Calculation Method** (programmatic in backend; optional AI blend):
- **Backend:** `_calculate_tailoring(cv_text, job_desc)` in `gemini_client.py`:
  - Extracts significant words (3+ letters, alphabetic) from job description and CV; removes common stop words.
  - **Keyword match rate**: (JD keywords found in CV) / (total JD keywords) × 100.
  - **Skill match / alignment**: Same overlap used for a single alignment score 0–100.
  - **Details:** `keyword_match_rate`, `skill_match_rate`, `experience_relevance`, `alignment_score`.
- If no job description is provided, score defaults to 80. If the AI also returns `tailoring_metrics.score`, the final score is the average of programmatic and AI.

**Why It Matters**: Tailored resumes significantly increase chances of passing ATS screening and impressing hiring managers. Generic resumes are often rejected in favor of tailored applications.

---

## Category Scores

Each main category (Content, Sections, ATS Essentials, Tailoring) receives an overall score:

- **Content Score**: Average of ATS Parse Rate, Quantifying Impact, Repetition, and Spelling & Grammar scores
- **Sections Score**: Based on Sections Metrics score
- **ATS Essentials Score**: Based on ATS Essentials Metrics score
- **Tailoring Score**: Based on Tailoring Metrics score

**Category Score Color Coding**:
- **80-100**: Green (Excellent)
- **60-79**: Yellow (Good)
- **0-59**: Red (Needs Improvement)

---

## Overall Match Score (0-100)

**Description**: The overall compatibility score between the resume and job description.

**Calculation Method**:
Weighted combination of:
- Skills Alignment (from subscores)
- Experience Alignment (from subscores)
- ATS Readiness (from subscores)
- Category metrics influence

**Interpretation**:
- **80-100**: Excellent fit (Strong candidate)
- **60-79**: Good fit (Competitive candidate)
- **0-59**: Needs improvement (Requires resume updates)

---

## Data Sources

1. **AI Analysis (Google Gemini)**: Provides semantic analysis, content quality assessment, and alignment evaluation
2. **Programmatic Calculations**: Text extraction quality, length analysis, structural detection
3. **Hybrid Approach**: Combines AI insights with programmatic validation for more accurate scoring

---

## Implementation Reference (Where the Numbers Come From)

This section maps each value on the report page to its source and code location, for developers and project documentation.

### Data flow

1. The app sends CV text and job description to the Google Gemini API.
2. The AI returns a single JSON object (scores, lists like suggestions, missing_skills, missing_keywords, etc.).
3. The raw JSON is parsed and normalized in **`src/gemini_client.py`**.
4. Content sub-metrics (Quantifying Impact, Repetition, Spelling & Grammar) are computed programmatically on the backend; AI values are used only when present and are averaged with programmatic scores.
5. The UI (**`src/ui_components.py`**) reads the final `analysis` dict and displays it.

**Main files:**

| File | Responsibility |
|------|----------------|
| `src/gemini_client.py` | API call, prompt, parsing, score normalization, ATS Parse Rate programmatic logic, status rules |
| `src/ui_components.py` | `issue_count()`, Content score formula, sidebar rendering |
| `app.py` | Calls `analyze_cv_with_gemini()`; stores analysis in session state; passes it to `render_report_page()` |

### "Your Score" (e.g. 72/100)

- **Source:** AI (Gemini). Prompt asks for `match_score` (0–100).
- **Backend:** `gemini_client.py` reads `parsed["match_score"]`, clamps to 0–100, integer. Stored as `analysis["match_score"]`.
- **UI:** `score = analysis.get("match_score", 0)` in `render_report_page()`.

### "X issues" (e.g. 16 issues)

- **Source:** Application logic only (not from the AI).
- **Formula** (in `ui_components.py`, function `issue_count()`):

  ```
  issues = 0
  issues += len(analysis["missing_keywords"])
  issues += len(analysis["missing_skills"])
  issues += number of non-empty strings in analysis["suggestions"]
  if analysis["match_score"] < 70: issues += 1
  return max(issues, 0)
  ```

### Content category score (e.g. 86%)

- **Source:** AI provides the four sub-metrics; the app computes the category score.
- **Formula** (in `ui_components.py`): **Content score = average** of: `ats_parse_rate`, `quantifying_impact.score`, `repetition.score`, `spelling_grammar.score` (integer average). Displayed next to the "Content" heading.

### Content sub-items (ATS Parse Rate, Quantifying Impact, Repetition, Spelling & Grammar)

- **Quantifying Impact, Repetition, Spelling & Grammar** are now **computed programmatically** in `gemini_client.py` so scores and status are always based on real logic:
  - **Quantifying Impact:** `_calculate_quantifying_impact(cv_text)` – counts lines/bullets that contain numbers, %, $, or measurable language; score 40–100 from proportion quantified. Details describe how many bullets are quantified.
  - **Repetition:** `_calculate_repetition(cv_text)` – word frequency and unique-ratio; higher score = less repetition. Penalizes heavily repeated words. Details suggest words to vary.
  - **Spelling & Grammar:** `_calculate_spelling_grammar(cv_text)` – heuristic formatting check (double spaces, spacing after punctuation, excessive all-caps). No external spell-check library; score 0–100 with details for issues found.
- If the AI also returns scores for these metrics, the backend **averages** programmatic and AI scores and uses AI details when present; otherwise programmatic details are used.
- **ATS Parse Rate** remains programmatic + optional AI blend (see above).
- **Status (No issues / Review / Error):** Derived in `gemini_client.py` via `_get_metric_status(score, ok_min, warn_min)` using **metric-specific thresholds** (backend and frontend match):

  | Metric | ok (No issues) | warn (Review) | error (Review) |
  |--------|----------------|---------------|----------------|
  | ATS Parse Rate | score ≥ 80 | score ≥ 60 and &lt; 80 | score &lt; 60 |
  | Quantifying Impact | score ≥ 70 | score ≥ 50 and &lt; 70 | score &lt; 50 |
  | Repetition | score ≥ 80 | score ≥ 60 and &lt; 80 | score &lt; 60 |
  | Spelling & Grammar | score ≥ 90 | score ≥ 70 and &lt; 90 | score &lt; 70 |

  UI maps: `ok` → "No issues", `warn`/`error` → "Review", `lock` → "Locked".

### Sections %, ATS Essentials %, Tailoring %

- **Source:** Backend programmatic logic (with optional AI blend). No metric is shown on the frontend without a computed score.
- **Sections:** `_calculate_sections(cv_text)` – checks for Contact, Experience, Education, Skills, Summary/Objective via keywords; 20 points per section; details include `missing_sections`.
- **ATS Essentials:** `_calculate_ats_essentials(cv_text)` – section headers, text-based flag, simple keyword density; score 0–100 with `issues` list in details.
- **Tailoring:** `_calculate_tailoring(cv_text, job_desc)` – keyword overlap between JD and CV (3+ letter words, stop words removed); alignment score 0–100.
- If the AI returns a score for any of these, the backend averages it with the programmatic score. UI reads `analysis["sections_metrics"]["score"]`, etc. No "Unlock Full Report" or paywall; the app is fully free.

### Summary table (source and location)

| Metric / label | Source | Where computed / read |
|----------------|--------|------------------------|
| Your Score (match_score) | AI | gemini_client (parse); ui_components (display) |
| X issues | App | ui_components.issue_count() |
| Content % | AI + App | ui_components (average of 4 content scores) |
| ATS Parse Rate score | AI + App | gemini_client (_calculate_ats_parse_rate + AI) |
| ATS Parse Rate status | App (from score) | gemini_client _get_metric_status; UI label |
| Quantifying Impact | Backend (programmatic + optional AI) | gemini_client _calculate_quantifying_impact; status from _get_metric_status(70, 50) |
| Repetition | Backend (programmatic + optional AI) | gemini_client _calculate_repetition; status from _get_metric_status(80, 60) |
| Spelling & Grammar | Backend (programmatic + optional AI) | gemini_client _calculate_spelling_grammar; status from _get_metric_status(90, 70) |
| Sections % | Backend (programmatic + optional AI) | gemini_client _calculate_sections; ui_components (display) |
| ATS Essentials % | Backend (programmatic + optional AI) | gemini_client _calculate_ats_essentials; ui_components (display) |
| Tailoring % | Backend (programmatic + optional AI) | gemini_client _calculate_tailoring(cv_text, job_desc); ui_components (display) |

---

## Notes

- **Fully free:** There is no "Unlock Full Report" or paywall; all metrics are computed and shown without restriction.
- **No display without logic:** Sections, ATS Essentials, and Tailoring (and all content metrics) have programmatic backend logic; the frontend only shows categories that have a computed score from the backend.
- All scores are normalized to 0-100 scale
- Status thresholds may vary slightly between metrics based on industry standards
- Scores are calculated in real-time during analysis
- Metrics are mode-dependent (General Review vs ATS Scan modes may produce different scores)
- The AI model analyzes up to 6000 characters of CV text and 4000 characters of job description

---

## Future Enhancements

- Optional spell-check library integration for Spelling & Grammar
- Enhanced repetition detection with synonym analysis
- Industry-specific metric weighting
- Comparative scoring against industry benchmarks
- Historical tracking and improvement recommendations

