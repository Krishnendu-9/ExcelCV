# ExcelCV: GenAI-Powered CV Reviewer

ExcelCV is a Streamlit project that evaluates resumes against a job description and generates an ATS-focused, explainable report.

## What’s Implemented (Top 5 Final-Project Upgrades)
1. Explainable weighted scoring
- Final score is deterministic and transparent.
- Report now shows component-wise weighted contribution (Content, JD Alignment, Sections, ATS Essentials, Contact).

2. JD Skill Matrix (evidence map)
- Job requirements are mapped to resume evidence with `Found / Partial / Missing` status.
- Each skill row includes extracted evidence text and confidence level.

3. Rewrite Assistant (before/after)
- Generates section-level rewrite recommendations from quantification and repetition analysis.
- Gives practical “Before -> After -> Why” guidance for stronger bullets.

4. Multi-resume comparison (2 to 5 resumes)
- Compare multiple PDFs/DOCX files against the same JD.
- Ranked table includes final score, ATS parse, section score, issue count, and top missing skills.

5. Evaluation toolkit (model vs human)
- Add human reviewer score per resume.
- Tracks MAE, RMSE, correlation, and lets you download benchmark JSON.

## Additional Final-Project Enhancements
6. Recruiter Snapshot
- One-card hiring summary (`Strong Fit / Potential Fit / Needs Improvement`) with key strength and key risk.

7. Priority Action Plan
- Prioritized remediation list with impact/effort guidance for resume fixes.

8. Interview Prep
- Targeted interview questions generated from strengths and detected skill gaps.

9. Learning Roadmap
- Skill-gap closure plan with short practical targets.

10. Portfolio Checklist
- Ready/pending checklist (sections, links, contact completeness, final suggestions).

## Core Features
- Upload and analyze single resume (`PDF` or `DOCX`, max `2MB`).
- Deterministic content checks:
  - ATS Parse Rate
  - Quantifying Impact
  - Repetition
  - Spelling & Grammar
- Structure and ATS checks:
  - Essential Sections
  - Contact Information
  - File Format & Size
  - Header Links / Email checks
- Download report as Markdown and JSON.

## Workflow
### Single Resume Analysis
1. Paste job description.
2. Upload one resume (`PDF` or `DOCX`).
3. Click `Upload & analyze`.
4. Review sidebar categories + detailed report cards.

### Multi-Resume Comparison
1. Expand `Compare Multiple Resumes (2-5 files)`.
2. Paste one JD and upload 2 to 5 resumes.
3. Click `Run comparison`.

### Evaluation Toolkit
1. Open report page.
2. Add human score (0 to 100) + optional notes.
3. Track quality metrics and export benchmark JSON.

## Installation
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Create `.env`:
```env
GOOGLE_API_KEY=your-key
```
3. Run app:
```bash
streamlit run app.py
```

## Testing
Run all unit tests:
```bash
py -3 -m unittest discover -s tests -p "test_*.py" -q
```

Optional Streamlit smoke test:
```bash
$env:RUN_STREAMLIT_SMOKE = "1"
py -3 -m unittest tests.test_streamlit_runtime_smoke -q
```

## Project Structure
```text
cv-review/
  app.py
  README.md
  requirements.txt
  src/
    config.py
    gemini_client.py
    scoring.py
    evaluation.py
    pdf_utils.py
    reporting.py
    ui/
  tests/
```

## Troubleshooting
- `Missing GOOGLE_API_KEY`: add API key in `.env`.
- `DOCX support is not installed`: install dependencies from `requirements.txt` (includes `python-docx`).
- `DOCX contained no extractable text`: the file likely has non-text elements/shapes; open in Word and ensure selectable text exists.
- Gemini rate/format issues: retry request; fallback handling is already included in the app.

## Notes
This project is structured to support final-year MCA demo requirements:
- explainable logic,
- measurable evaluation,
- and extensible architecture for upcoming feature additions.
