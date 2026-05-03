# ExcelCV Setup Guide

This repository currently runs as a Streamlit application.

## 1) Install Dependencies

```bash
py -3 -m pip install -r requirements.txt
```

## 2) Configure Environment

Create `.env` from `.env.example` and fill required keys.

Required:
- `GOOGLE_API_KEY`

Optional:
- `SESSION_SECRET`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `SMTP_*` values for password reset emails

## 3) Run the App

```bash
py -3 -m streamlit run app.py
```

Default local URL:
- `http://localhost:8501`

## 4) Run Tests

```bash
py -3 -m unittest discover -s tests -p "test_*.py" -q
```

Optional Streamlit runtime smoke test:

```bash
$env:RUN_STREAMLIT_SMOKE="1"
py -3 -m unittest tests/test_streamlit_runtime_smoke.py -q
```

## Notes

- The app stores local data in `data/excelcv.db`.
- Core logic is under `src/`:
  - `gemini_client.py`: AI orchestration + deterministic merge
  - `scoring.py`: deterministic scoring engine
  - `ui/`: UI renderers and theme injection
