"""Static / informational page renderers (blog, policy, contact, how-it-works …)."""

from datetime import datetime

import streamlit as st

from src.email_utils import is_email_configured, send_contact_email
from src.cover_letter import render_cover_letter_page
from src.ui.app_utils import _build_page_href
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

    if page_key == "motivation-letter":
        render_cover_letter_page()
        return

    if page_key == "resume-builder":
        st.session_state["page"] = "cv-builder"
        st.rerun()
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
            f"""
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
            "From upload to report in a transparent, reproducible flow.",
        )
        st.markdown("### 1. Input")
        st.write("Paste the job description and upload a PDF/DOCX resume.")
        st.markdown("### 2. Parsing")
        st.write("ExcelCV extracts text and checks parse confidence.")
        st.markdown("### 3. Analysis")
        st.write("Deterministic content checks run alongside model-based qualitative analysis.")
        st.markdown("### 4. Scoring")
        st.write("A weighted, explainable scoring breakdown computes final match score.")
        st.markdown("### 5. Actionable Output")
        st.write("You get missing skills, keyword gaps, rewrite suggestions, and downloadable reports.")
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
            "Analysis data is handled in-session for app functionality. We do not provide user account storage in this project build."
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

