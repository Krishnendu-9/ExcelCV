# ExcelCV Viva QA Summary

- Total number of questions generated: **231**
- Output document: **ExcelCV_Final_Year_Project_Viva_QA.docx**

## Main Sections Included
- 1. Project Overview Questions
- 2. Technology Stack Questions
- 3. Architecture and Folder Structure Questions
- 4. Feature-Based Questions
- 5. Database Questions
- 6. AI / LLM / API Integration Questions
- 7. Streamlit-Specific Questions
- 8. Code-Level Questions
- 9. Security Questions
- 10. Testing Questions
- 11. Deployment Questions
- 12. GitHub / Version Control Questions
- 13. Practical Examiner Questions
- 14. Very Simple Questions
- 15. Medium-Level Questions
- 16. Hard-Level Questions
- 17. Strong Why Questions
- 18. Future Scope Questions
- 19. Weakness and Limitation Questions
- 20. How to Explain This Project in 2 Minutes
- 21. Most Important 30 Questions to Revise Before Viva
- 22. File-by-File Explanation
- 23. Possible Code Walkthrough Script
- 24. Project Demonstration Script

## Important Project Files Analyzed
- `app.py`
- `src/config.py`
- `src/database.py`
- `src/auth_utils.py`
- `src/oauth_utils.py`
- `src/email_utils.py`
- `src/pdf_utils.py`
- `src/gemini_client.py`
- `src/services/scoring.py`
- `src/services/reporting.py`
- `src/services/comparison_pdf.py`
- `src/ui/upload.py`
- `src/ui/analysis_runner.py`
- `src/ui/report.py`
- `src/ui/compare_report.py`
- `src/ui/cv_builder_page.py`
- `src/cover_letter/page.py`
- `src/cover_letter/service.py`
- `src/cover_letter/generator.py`
- `tests/test_oauth_utils.py`
- `tests/test_scoring_sections_order.py`
- `requirements.txt`
- `requirements-dev.txt`
- `pyproject.toml`
- `.streamlit/config.toml`
- `.env.example`
- `.gitignore`
- `README.md`

## Missing or Weak Areas Found
- Automated test coverage is currently minimal compared to feature surface area.
- Some static/docs content appears partially out-of-sync with latest code behavior.
- SQLite is excellent for local/demo use but limited for high-concurrency production.
- Large module (`src/ui/cv_builder_page.py`) can be further refactored for maintainability.

## Suggestions Before Final Submission
- Add unit/integration tests for analysis runner, scoring, auth, and cover letter pipeline.
- Add at least one end-to-end UI regression path (upload -> analyze -> export).
- Synchronize all docs/static text with current implemented flows and table names.
- Prepare a clean demo dataset and rehearse the 2-minute pitch + walkthrough script.
- Add a final architecture diagram and DB ER summary screenshot in presentation slides.
