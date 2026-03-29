# ExcelCV: GenAI-Powered CV Reviewer

ExcelCV is a Streamlit app that reviews a resume (PDF) against a job description and returns an ATS-oriented report with actionable suggestions.

## Features
- Dual-page workflow: upload page and report page
- Single standard analysis workflow (no mode switching)
- ATS readiness scoring (0-100)
- Keyword and missing skill analysis
- Content checks: parse rate, quantifying impact, repetition, spelling/grammar
- Resume structure checks: sections, ATS essentials, contact info
- Download report as Markdown or JSON

## Workflow
### Upload page
1. Paste a job description.
2. Upload a PDF resume (max 2 MB).
3. Click `Upload & analyze`.

### Report page
- Overall score and issue count
- Category breakdown in sidebar
- Detailed sections for strengths, gaps, and suggestions
- `Upload another resume` to start a new analysis

## Scoring overview
The final score is built from deterministic programmatic checks plus AI-structured feedback fields. Core weighted areas include:
- Content quality
- Job description tailoring
- Section completeness
- ATS essentials
- Contact completeness

## Installation
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Create `.env` and set:
```env
GOOGLE_API_KEY=your-key
```
3. Run:
```bash
streamlit run app.py
```

## Tests
```bash
py -3 -m unittest discover -s tests -p "test_*.py" -q
```

## Project structure
```text
cv-review/
  app.py
  README.md
  requirements.txt
  tests/
  src/
    config.py
    gemini_client.py
    pdf_utils.py
    reporting.py
    scoring.py
    ui/
```

## Troubleshooting
- `Missing GOOGLE_API_KEY`: set key in `.env`.
- `AI response was not in expected JSON format`: retry (usually transient model output formatting).
- PDF extraction issues: use a text-based PDF, not an image scan.

## Notes
This is an educational project submission.
