"""Static / informational page renderers (blog, policy, contact, how-it-works …)."""

from datetime import datetime

import streamlit as st

from src.cover_letter import render_cover_letter_page
from src.email_utils import is_email_configured, send_contact_email
from src.ui.report import render_evaluation_toolkit


def _render_info_page_header(title: str, subtitle: str = "") -> None:
    """Render a consistent heading block for non-analysis pages."""
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


def render_static_page(page: str) -> None:
    """Render informational pages for navigation/footer sections."""
    page_key = str(page or "home")
    analysis = st.session_state.get("analysis", {}) if isinstance(st.session_state.get("analysis"), dict) else {}

    if page_key == "career-blog":
        _render_info_page_header(
            "Career Blog",
            "Practical career guidance for resume improvement, ATS strategy, and interview success.",
        )
        st.markdown("### Latest Topics")
        st.markdown(
            "1. **How to Quantify Resume Bullets**\n"
            "Turn generic tasks into measurable impact statements with clear metrics.\n\n"
            "2. **ATS Keyword Strategy Without Stuffing**\n"
            "Match role language naturally while keeping your resume recruiter-friendly.\n\n"
            "3. **Common Resume Rejections and Fixes**\n"
            "Spot structural issues that cause early screening drop-offs."
        )
        st.markdown("### Weekly Practice")
        st.markdown(
            "- Rewrite 3 bullets with numbers\n"
            "- Align top 10 role keywords from your target JD\n"
            "- Review one resume section per day"
        )
        return

    if page_key == "cover-letter":
        render_cover_letter_page()
        return


    if page_key == "ats-insights":
        _render_info_page_header(
            "ATS Insights",
            "Understand how ExcelCV measures recruiter and ATS readiness before final submission.",
        )
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown("### What We Analyze")
            st.markdown(
                "- ATS Parse Rate\n"
                "- Quantifying Impact in bullet points\n"
                "- Repetition of action verbs\n"
                "- Spelling and grammar quality\n"
                "- Section completeness and ATS essentials"
            )
        with c2:
            st.markdown("### Score Interpretation")
            st.markdown(
                "- `80-100`: Strong ATS readiness\n"
                "- `60-79`: Moderate, needs targeted improvements\n"
                "- `0-59`: High risk for ATS/recruiter screening"
            )
        st.markdown("### Why It Matters")
        st.write(
            "Many resumes are rejected before a recruiter reads them. "
            "This page explains how ATS-visible structure and measurable outcomes improve selection chances."
        )
        return

    if page_key == "explainable-scoring":
        st.markdown(
            """
<div class="landing-extended">

  <section class="landing-clean-section landing-intro-section">
    <div class="landing-clean-head">
      <span class="landing-clean-tag">Scoring methodology</span>
      <h2 class="landing-clean-title">How ExcelCV scores your resume</h2>
      <p class="landing-clean-subtitle">
        Every number you see is produced by a transparent, weighted formula —
        no black-box AI guessing. You can verify every component yourself.
      </p>
    </div>
    <div class="landing-clean-grid steps-grid">
      <article class="landing-clean-card">
        <div class="landing-clean-icon">1</div>
        <h4>Text extraction</h4>
        <p>Your PDF or DOCX is parsed and raw text is extracted. Parse confidence
           becomes your ATS Parse Rate score.</p>
      </article>
      <article class="landing-clean-card">
        <div class="landing-clean-icon">2</div>
        <h4>Deterministic checks</h4>
        <p>Five rule-based checks run on the extracted text: parse rate, quantifying
           impact, repetition, spelling &amp; grammar, and section completeness.</p>
      </article>
      <article class="landing-clean-card">
        <div class="landing-clean-icon">3</div>
        <h4>Weighted final score</h4>
        <p>Each component contributes a fixed percentage to the final 0–100 score.
           The weights are shown below — nothing is hidden.</p>
      </article>
    </div>
  </section>

  <section class="landing-clean-section">
    <div class="landing-clean-head">
      <span class="landing-clean-tag">Score weights</span>
      <h3 class="landing-clean-title">What makes up your score</h3>
      <p class="landing-clean-subtitle">
        Five categories, fixed weights, fully reproducible.
      </p>
    </div>
    <div class="landing-clean-grid features-grid">
      <article class="landing-clean-card">
        <h4>Content Quality &nbsp;<span style="color:#2563eb;font-size:1.1rem;font-weight:800;">30%</span></h4>
        <p>Average of ATS parse rate, quantifying impact, repetition penalty, and
           spelling &amp; grammar — all computed deterministically on your text.</p>
      </article>
      <article class="landing-clean-card">
        <h4>ATS Essentials &nbsp;<span style="color:#2563eb;font-size:1.1rem;font-weight:800;">20%</span></h4>
        <p>Checks for contact info, measurable bullets, appropriate resume length,
           and absence of ATS-unfriendly formatting like tables or images.</p>
      </article>
      <article class="landing-clean-card">
        <h4>JD Alignment &nbsp;<span style="color:#2563eb;font-size:1.1rem;font-weight:800;">25%</span></h4>
        <p>Keyword overlap and skill gap count between your resume and the job
           description. Only active in JD mode — weight shifts to Content when no JD is provided.</p>
      </article>
      <article class="landing-clean-card">
        <h4>Section Quality &nbsp;<span style="color:#2563eb;font-size:1.1rem;font-weight:800;">15%</span></h4>
        <p>Checks that key sections (Summary, Experience, Education, Skills) are
           present, non-empty, and correctly labeled for ATS recognition.</p>
      </article>
      <article class="landing-clean-card">
        <h4>Skills Match &nbsp;<span style="color:#2563eb;font-size:1.1rem;font-weight:800;">10%</span></h4>
        <p>Compares listed skills against role-relevant keywords extracted from the
           job description to surface critical gaps.</p>
      </article>
      <article class="landing-clean-card">
        <h4>Score bands</h4>
        <p>
          <strong>90–100</strong> — Submit with confidence<br>
          <strong>75–89</strong> — Good, minor fixes needed<br>
          <strong>60–74</strong> — Fair, targeted improvements<br>
          <strong>0–59</strong> — High risk, revise before applying
        </p>
      </article>
    </div>
  </section>

  <section class="landing-clean-section">
    <div class="landing-clean-head">
      <span class="landing-clean-tag">Why it matters</span>
      <h3 class="landing-clean-title">Transparency you can trust</h3>
      <p class="landing-clean-subtitle">
        Most resume tools give you a score with no explanation. ExcelCV shows
        every component so you know exactly what to fix.
      </p>
    </div>
    <div class="landing-clean-grid steps-grid">
      <article class="landing-clean-card">
        <div class="landing-clean-icon">&#10003;</div>
        <h4>No guessing</h4>
        <p>All five checks are deterministic — same resume always returns the same score.</p>
      </article>
      <article class="landing-clean-card">
        <div class="landing-clean-icon">&#10003;</div>
        <h4>Actionable gaps</h4>
        <p>Each low-scoring component links directly to the section of your report
           that explains how to fix it.</p>
      </article>
      <article class="landing-clean-card">
        <div class="landing-clean-icon">&#10003;</div>
        <h4>JD-aware mode</h4>
        <p>Add a job description and the scoring shifts to prioritise role-specific
           keyword alignment and skill match.</p>
      </article>
    </div>
  </section>

  <section class="landing-clean-cta">
    <h3>See your own score breakdown</h3>
    <p>Upload your resume and get a fully explainable report in seconds.</p>
    <div class="landing-clean-cta-pills">
      <span>Deterministic scoring</span>
      <span>No black box</span>
      <span>Free to use</span>
    </div>
  </section>

</div>
            """,
            unsafe_allow_html=True,
        )
        return

    if page_key == "instant-report":
        _render_info_page_header(
            "Instant Report",
            "Generate a complete resume-vs-job-description report with structured and actionable feedback.",
        )
        st.markdown("### What You Get")
        st.markdown(
            "- Overall match score\n"
            "- Explainable weighted score breakdown\n"
            "- Missing skills and keyword gaps\n"
            "- Rewrite suggestions and priority action plan\n"
            "- Downloadable Markdown and JSON output"
        )
        if analysis:
            st.success("A recent report is available in this session.")
            if st.button("Open Latest Report", key="open_latest_report_btn", width="content"):
                st.session_state["page"] = "report"
                st.query_params["page"] = "report"
                rid = st.session_state.get("report_snapshot_id") or st.query_params.get("rid")
                if rid:
                    st.query_params["rid"] = str(rid)
                st.rerun()
        else:
            st.info("No report found in the current session. Upload a resume on the home page to generate one.")
        return

    if page_key == "evaluation-toolkit":
        _render_info_page_header(
            "Evaluation Toolkit",
            "Benchmark model output against human reviewer scores for project validation.",
        )
        st.markdown(
            "Use this toolkit to track model quality with:\n"
            "- Mean Absolute Error (MAE)\n"
            "- Root Mean Square Error (RMSE)\n"
            "- Pearson correlation"
        )
        if analysis:
            resume_name = str(st.session_state.get("cv_name", "CV"))
            render_evaluation_toolkit(analysis, resume_name)
        else:
            st.warning("Analyze at least one resume first to use the interactive toolkit.")
        return

    if page_key == "project-notes":
        _render_info_page_header(
            "Project Notes",
            "Technical overview of architecture, scoring strategy, and implementation choices.",
        )
        st.markdown("### Architecture")
        st.markdown(
            "- `app.py` (~350 lines): routing, session orchestration, OAuth/cookie handling\n"
            "- `src/ui/layout.py`: site header, footer, theme toggle\n"
            "- `src/ui/upload.py`: upload page, compare mode, file handling UI\n"
            "- `src/ui/report.py`: full report rendering, evaluation toolkit\n"
            "- `src/ui/css_injection.py`: all custom CSS/JS injection (header bar, top-bar)\n"
            "- `src/ui/analysis_runner.py`: CV analysis pipeline, multi-resume comparison, DB auto-save\n"
            "- `src/ui/app_utils.py`: URL helpers, state helpers, report snapshot store\n"
            "- `src/ui/static_pages.py`: informational pages (blog, privacy, contact, how-it-works)\n"
            "- `src/ui/auth_page.py`: sign in, create account, forgot/reset password\n"
            "- `src/gemini_client.py`: Gemini 2.0 Flash orchestration + JSON parsing\n"
            "- `src/scoring.py`: deterministic ATS/content/tailoring scoring\n"
            "- `src/auth_utils.py`: bcrypt login, HMAC session tokens, cookie restore\n"
            "- `src/database.py`: SQLAlchemy ORM (User, CV, Analysis, PasswordResetToken)\n"
            "- `src/email_utils.py`: SMTP password reset + contact form email"
        )
        st.markdown("### Engineering Decisions")
        st.markdown(
            "- Two-pronged scoring: deterministic rules (explainability) + Gemini qualitative analysis\n"
            "- Session-scoped analysis state for fast cross-page navigation\n"
            "- HMAC-SHA256 signed tokens + bcrypt 12-round hashing for auth security\n"
            "- SQLite (SQLAlchemy ORM) with `_migrate()` for zero-downtime schema evolution\n"
            "- Export support (`Markdown`, `JSON`) for demos and portfolio records"
        )
        st.markdown("### Suggested Next Iterations")
        st.markdown(
            "- Migrate to hosted PostgreSQL (e.g. Supabase) for Streamlit Cloud persistence\n"
            "- Add persistent benchmark storage for evaluation toolkit\n"
            "- Introduce role-specific scoring profiles\n"
            "- Automated regression dashboards for scoring changes"
        )
        return

    if page_key == "how-it-works":
        _render_info_page_header(
            "How It Works",
            "A walkthrough of every ExcelCV feature — what it does, how to use it, and what you get back.",
        )
        st.markdown("### Analyze CV")
        st.markdown(
            "Paste a job description and upload a PDF or DOCX resume. ExcelCV extracts the text, "
            "runs deterministic checks (ATS parse rate, quantifying impact, repetition, spelling, "
            "section completeness), and combines them with a model-based qualitative review. "
            "You get a weighted final score, explainable component breakdown, missing skills, "
            "keyword gaps, and rewrite suggestions you can act on."
        )
        st.markdown("### Compare Resumes")
        st.markdown(
            "Upload 2–5 resumes against the same job description to rank candidates side-by-side. "
            "Each resume is scored independently, then ranked by final score with ATS parse, section "
            "quality, issue count, and top missing skills shown in a single ranking table — useful "
            "for picking the strongest applicant for a role or for comparing multiple drafts of your "
            "own resume."
        )
        st.markdown("### Cover Letter")
        st.markdown(
            "Generate a tailored cover letter from your resume and the target job description. "
            "ExcelCV pulls relevant experience from your CV, aligns it to the role's key requirements, "
            "and produces a paragraph-formatted draft you can copy, edit, and refine — designed to "
            "stay grounded in what's actually on your resume rather than inventing claims."
        )
        st.markdown("### Resume Builder")
        st.markdown(
            "Build a resume from scratch in a two-pane editor with a live preview. Pick from three "
            "templates (Classic, Modern, Minimal), customize accent color and typography, and use "
            "AI-suggested bullet points for experience entries. Save drafts to your account, reload "
            "them later, and export to PDF when ready."
        )
        st.markdown("### My CVs and My Analyses")
        st.markdown(
            "Signed-in users get a personal library: every analysis you run is auto-saved to "
            "**My Analyses** with the original JD, score, and report. Every resume you build is "
            "saved to **My CVs** for editing, duplicating, or exporting later. No re-uploads — "
            "everything stays attached to your account."
        )
        return

    if page_key == "resume-tips":
        _render_info_page_header(
            "Resume Tips",
            "Practical, ATS-friendly resume writing guidance — what recruiters and parsers actually look for.",
        )
        st.markdown("### Structure That Works")
        st.markdown(
            "- Use a single-column layout — tables, text boxes, and multi-column designs break ATS parsers.\n"
            "- Stick to standard section headings: **Summary**, **Experience**, **Education**, **Skills**, **Projects**.\n"
            "- Keep file format to PDF or DOCX. Avoid scanned images or PDFs exported from design tools.\n"
            "- Aim for 1 page (early career) or 2 pages (5+ years experience). Cutting filler beats padding."
        )
        st.markdown("### Write Bullets That Land")
        st.markdown(
            "- Lead with a strong action verb: *built, shipped, reduced, automated, led, designed*.\n"
            "- Quantify impact whenever possible — numbers, percentages, time saved, dollars, scale.\n"
            "- Show the result, not just the task. *\"Migrated billing service to Kafka, cutting end-to-end latency 38%\"* beats *\"Worked on billing service migration.\"*\n"
            "- Vary your action verbs across bullets so the resume doesn't read as repetitive."
        )
        st.markdown("### Tailor to the Job Description")
        st.markdown(
            "- Read the JD twice. Highlight role-specific keywords (tools, methodologies, seniority cues).\n"
            "- Mirror those keywords naturally in your Summary and Experience — don't keyword-stuff.\n"
            "- If a must-have skill is missing from your resume but you do have it, add it explicitly.\n"
            "- Reorder bullets within a role so the JD-relevant ones appear first."
        )
        st.markdown("### Common Mistakes to Avoid")
        st.markdown(
            "- Generic objective statements (*\"Looking for a challenging role…\"*) — replace with a 2-line summary of your impact.\n"
            "- Listing responsibilities instead of accomplishments.\n"
            "- Inconsistent date formats, tense, or punctuation across entries.\n"
            "- Using graphics, icons, or photos — they break parsing and rarely help.\n"
            "- Outdated contact info or a non-professional email address."
        )
        st.markdown("### Before You Send")
        st.markdown(
            "- Run your resume through **Analyze CV** with the actual JD to catch gaps before a recruiter does.\n"
            "- Read it out loud — awkward phrasing surfaces fast.\n"
            "- Ask one peer in your target field for a 5-minute review."
        )
        return

    if page_key == "cover-letter-guide":
        _render_info_page_header(
            "Cover Letter Guide",
            "How to write a short, specific cover letter that complements your resume instead of repeating it.",
        )
        st.markdown("### What a Cover Letter Should Actually Do")
        st.markdown(
            "A good cover letter answers three questions the resume can't:\n"
            "1. **Why this role, specifically?** Not the field — this exact position at this company.\n"
            "2. **What evidence from your background maps directly to it?** One or two concrete stories.\n"
            "3. **What do you bring that isn't on the resume?** Context, motivation, soft signals."
        )
        st.markdown("### Recommended Structure")
        st.markdown(
            "- **Opening (2–3 lines):** State the role and one specific reason you're applying — a "
            "product, mission, or technical bet the company is making that you care about.\n"
            "- **Middle (1–2 short paragraphs):** Pick the strongest story from your resume that "
            "matches the role's top requirement. Explain *what*, *how*, and *result* in plain language.\n"
            "- **Close (2–3 lines):** A clear next step (*\"I'd welcome the chance to discuss…\"*) and a thank-you.\n"
            "- Keep the whole thing to **250–350 words**. Recruiters skim — long letters lose them."
        )
        st.markdown("### Tone and Voice")
        st.markdown(
            "- Write the way you'd speak in a first interview — professional, but not stiff.\n"
            "- Avoid clichés (*\"team player,\" \"results-driven,\" \"passionate about\"*). Show, don't claim.\n"
            "- Match the company's vocabulary — read their About page, latest blog post, or product copy.\n"
            "- Use the hiring manager's name if you can find it. *\"Dear Hiring Team\"* is fine when you can't."
        )
        st.markdown("### Tailoring Quickly")
        st.markdown(
            "- Start from a base letter, then rewrite the opening and middle paragraph per application.\n"
            "- The boilerplate that survives across applications is the close — everything before it should change.\n"
            "- If you can't name a specific reason for *this* company within 30 seconds of thinking, it shows in the letter."
        )
        st.markdown("### Common Mistakes")
        st.markdown(
            "- Re-stating the resume bullet-by-bullet. The letter is context, not a summary.\n"
            "- Vague enthusiasm without evidence (*\"I'm very excited about this opportunity\"*).\n"
            "- Mentioning skills you don't have — recruiters notice and it costs trust.\n"
            "- Forgetting to update the company name when reusing a draft. (It happens. Proofread.)"
        )
        st.markdown("### Generate a Draft Quickly")
        st.markdown(
            "Use the **Cover Letter** generator in ExcelCV to produce a tailored first draft from your "
            "saved CV and a job description, then refine the opening and close with your own voice."
        )
        return

    if page_key == "interview-prep":
        _render_info_page_header(
            "Interview Prep",
            "Prepare structured answers from strengths and identified skill gaps.",
        )
        prep_rows = analysis.get("interview_prep", []) if isinstance(analysis, dict) else []
        if prep_rows:
            st.markdown("### Questions Generated From Your Latest Analysis")
            for idx, row in enumerate(prep_rows, start=1):
                st.markdown(f"**{idx}. {row.get('type', 'Question')}**")
                st.write(row.get("question", ""))
                st.caption(row.get("why", ""))
        else:
            st.markdown("### Recommended Practice Areas")
            st.markdown(
                "- Explain a project with measurable impact\n"
                "- Defend technology choices with tradeoffs\n"
                "- Describe how you would close a missing-skill gap in 30 days\n"
                "- Prepare STAR-format stories for leadership and collaboration"
            )
            st.info("Run a resume analysis first to generate targeted interview questions.")
        return

    if page_key == "privacy-policy":
        _render_info_page_header("Privacy Policy", f"Last updated: {datetime.now().strftime('%B %d, %Y')}")
        st.markdown("### 1. Introduction")
        st.write(
            "ExcelCV is designed for educational and portfolio use. We respect user privacy and keep data handling minimal."
        )
        st.markdown("### 2. Data We Process")
        st.markdown(
            "- Job description text entered by the user\n"
            "- Uploaded resume content for analysis\n"
            "- Optional evaluation notes provided by the user"
        )
        st.markdown("### 3. Storage & Retention")
        st.write(
            "Signed-in accounts can persist CVs, analyses, and comparison history in the app database. "
            "Guest sessions keep analysis data only for the current browser session."
        )
        st.markdown("### 4. Security")
        st.write("Reasonable safeguards are applied for processing within the app runtime environment.")
        st.markdown("### 5. Contact")
        st.write("For privacy-related questions, use the Contact page.")
        return

    if page_key == "terms-of-service":
        _render_info_page_header("Terms of Service", f"Last updated: {datetime.now().strftime('%B %d, %Y')}")
        st.markdown("### 1. Acceptance")
        st.write("By using ExcelCV, you agree to these terms for this educational demo application.")
        st.markdown("### 2. Intended Use")
        st.write("The service provides resume feedback and does not guarantee hiring outcomes.")
        st.markdown("### 3. User Responsibility")
        st.write("Users are responsible for uploaded content and ensuring they have rights to submit it.")
        st.markdown("### 4. Prohibited Use")
        st.markdown(
            "- Uploading unlawful or malicious content\n"
            "- Attempting to disrupt or reverse-engineer the service"
        )
        st.markdown("### 5. Liability")
        st.write("The service is provided as-is for educational purposes without warranty.")
        st.markdown("### 6. Updates")
        st.write("Terms may be revised as the project evolves.")
        return

    if page_key == "contact":
        st.markdown(
            """
            <style>
            [data-testid="stAppViewContainer"] .support-page-shell {
                margin-top: -72px !important;
                display: flex !important;
                flex-direction: column !important;
                gap: 14px !important;
            }
            [data-testid="stAppViewContainer"] .support-page-shell .landing-clean-tag {
                display: none !important;
            }
            [data-testid="stAppViewContainer"] .support-info-grid {
                display: grid !important;
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
                gap: 10px !important;
            }
            [data-testid="stAppViewContainer"] .support-mini-card {
                border: 1px solid var(--border-color) !important;
                border-radius: 14px !important;
                background: var(--bg-card) !important;
                padding: 14px !important;
                box-shadow: 0 8px 18px var(--shadow) !important;
            }
            [data-testid="stAppViewContainer"] .support-mini-card h4 {
                margin: 0 0 6px 0 !important;
                color: var(--text-primary) !important;
                font-size: 1rem !important;
                font-weight: 800 !important;
            }
            [data-testid="stAppViewContainer"] .support-mini-card p {
                margin: 0 !important;
                color: var(--text-secondary) !important;
                font-size: 0.92rem !important;
                line-height: 1.48 !important;
            }
            [data-testid="stAppViewContainer"] .st-key-support_info_card,
            [data-testid="stAppViewContainer"] .st-key-support_form_card {
                background: linear-gradient(160deg, var(--bg-card), var(--bg-secondary)) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 18px !important;
                padding: 22px 24px !important;
                box-shadow: 0 12px 24px var(--shadow) !important;
            }
            [data-testid="stAppViewContainer"] .support-body-copy {
                color: var(--text-secondary) !important;
                font-size: 0.96rem !important;
                line-height: 1.58 !important;
                margin: 0 0 12px 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-section-title {
                color: var(--text-primary) !important;
                font-size: 1.12rem !important;
                font-weight: 800 !important;
                margin: 0 0 8px 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-list {
                margin: 0 !important;
                padding-left: 18px !important;
                color: var(--text-secondary) !important;
            }
            [data-testid="stAppViewContainer"] .support-list li {
                margin-bottom: 8px !important;
            }
            @media (max-width: 900px) {
                [data-testid="stAppViewContainer"] .support-page-shell {
                    margin-top: -38px !important;
                }
                [data-testid="stAppViewContainer"] .support-info-grid {
                    grid-template-columns: 1fr !important;
                }
                [data-testid="stAppViewContainer"] .st-key-support_info_card,
                [data-testid="stAppViewContainer"] .st-key-support_form_card {
                    padding: 16px 14px !important;
                }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="support-page-shell">
                <div class="landing-clean-head">
                    <h2 class="landing-clean-title">Need help with ExcelCV?</h2>
                    <p class="landing-clean-subtitle">
                        Share your question, technical issue, or product feedback and we will review it quickly.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        left, right = st.columns([1.05, 1.95], gap="large")
        with left:
            with st.container(key="support_info_card"):
                st.markdown('<p class="support-section-title">Reach us</p>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="support-body-copy">Use the form to contact the team. For direct follow-up, use our support email.</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    """
                    <div class="support-info-grid">
                        <article class="support-mini-card">
                            <h4>Email</h4>
                            <p>support@excelcv.app</p>
                        </article>
                        <article class="support-mini-card">
                            <h4>Project Type</h4>
                            <p>Academic and portfolio demo</p>
                        </article>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown('<p class="support-section-title" style="margin-top:14px;">Typical topics</p>', unsafe_allow_html=True)
                st.markdown(
                    """
                    <ul class="support-list">
                        <li>Feature requests and UX suggestions</li>
                        <li>Technical support and bug reports</li>
                        <li>Resume scoring and report clarifications</li>
                    </ul>
                    """,
                    unsafe_allow_html=True,
                )
        with right:
            with st.container(key="support_form_card"):
                st.markdown('<p class="support-section-title">Send a message</p>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="support-body-copy">Fill all required fields and we will get back to you.</p>',
                    unsafe_allow_html=True,
                )
                with st.form("contact_page_form", clear_on_submit=True):
                    name = st.text_input("Your Name", placeholder="Enter your name")
                    email = st.text_input("Email Address", placeholder="you@example.com")
                    inquiry = st.radio(
                        "Inquiry Type",
                        ["General Inquiry", "Technical Support", "Feedback / Suggestion"],
                    )
                    subject = st.text_input("Subject", placeholder="How can we help?")
                    message = st.text_area("Message", height=140, placeholder="Write your message...")
                    sent = st.form_submit_button("Send Message", width="stretch")
                if sent:
                    if not name.strip() or not email.strip() or not message.strip():
                        st.error("Please fill in your name, email, and message.")
                    elif "@" not in email or "." not in email.split("@", 1)[-1]:
                        st.error("Enter a valid email address so we can reply to you.")
                    elif is_email_configured():
                        ok = send_contact_email(
                            name.strip(),
                            email.strip(),
                            inquiry,
                            subject.strip() or "(no subject)",
                            message.strip(),
                        )
                        if ok:
                            st.success(f"Thanks, {name.strip()}! Your message has been sent.")
                        else:
                            st.warning(
                                "Message could not be delivered right now. "
                                "Please email us directly at `support@excelcv.app`."
                            )
                    else:
                        st.success(f"Thanks, {name.strip()}! Your message has been received.")
                        st.caption("Email delivery is not configured in this deployment; contact `support@excelcv.app` directly.")
        return

    # Fallback for unknown routes.
    _render_info_page_header("Page Not Found")
    st.warning("The requested page is unavailable. Use the navigation links to continue.")

