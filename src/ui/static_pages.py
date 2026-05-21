"""Static / informational page renderers (blog, policy, contact, how-it-works …)."""

import streamlit as st

from src.cover_letter import render_cover_letter_page
from src.email_utils import is_email_configured, send_acknowledgement_email, send_contact_email
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
    analysis = (
        st.session_state.get("analysis", {})
        if isinstance(st.session_state.get("analysis"), dict)
        else {}
    )

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
            st.info(
                "No report found in the current session. Upload a resume on the home page to generate one."
            )
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
            "templates (Classic, Creative, Modern), customize accent color and typography, and use "
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
        # Pillar page for the Resume Tips hub. The redesigned hub + sub-guide
        # articles live in src/ui/guides.py; this branch just dispatches to it.
        from src.ui.guides import render_resume_tips_pillar

        render_resume_tips_pillar()
        return

    if page_key == "cover-letter-guide":
        from src.ui.guides import render_cover_letter_guide

        render_cover_letter_guide()
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
        from src.ui.guides import render_privacy_policy

        render_privacy_policy()
        return

    if page_key == "terms-of-service":
        from src.ui.guides import render_terms_of_service

        render_terms_of_service()
        return

    if page_key == "contact":
        privacy_href = _build_page_href("privacy-policy")
        how_it_works_href = _build_page_href("how-it-works")
        resume_tips_href = _build_page_href("resume-tips")

        # SVG icons inlined so we don't depend on an icon font. Kept compact —
        # `currentColor` so they inherit the accent tint from the surrounding
        # icon chip.
        _MAIL_ICON = (
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true">'
            '<rect x="2" y="4" width="20" height="16" rx="2"/>'
            '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>'
        )
        _CLOCK_ICON = (
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true">'
            '<circle cx="12" cy="12" r="10"/>'
            '<polyline points="12 6 12 12 16 14"/></svg>'
        )
        _BOOK_ICON = (
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true">'
            '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>'
            '<path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>'
            "</svg>"
        )

        st.markdown(
            """
            <style>
            [data-testid="stAppViewContainer"] .support-page-shell {
                margin-top: -72px !important;
                display: flex !important;
                flex-direction: column !important;
                gap: 18px !important;
                margin-bottom: 18px !important;
            }
            [data-testid="stAppViewContainer"] .support-page-shell .landing-clean-head {
                text-align: center !important;
            }
            [data-testid="stAppViewContainer"] .support-page-shell .landing-clean-title {
                color: var(--text-primary) !important;
                font-size: 2.25rem !important;
                font-weight: 800 !important;
                margin: 0 0 10px 0 !important;
                letter-spacing: -0.01em !important;
            }
            [data-testid="stAppViewContainer"] .support-page-shell .landing-clean-subtitle {
                color: var(--text-secondary) !important;
                font-size: 1rem !important;
                line-height: 1.55 !important;
                max-width: 640px !important;
                margin: 0 auto !important;
            }
            /* Outer card containers (left info column + right form column) */
            [data-testid="stAppViewContainer"] .st-key-support_info_card,
            [data-testid="stAppViewContainer"] .st-key-support_form_card {
                background: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 18px !important;
                padding: 26px 28px !important;
                box-shadow: 0 12px 24px var(--shadow) !important;
            }
            [data-testid="stAppViewContainer"] .support-section-title {
                color: var(--text-primary) !important;
                font-size: 1.1rem !important;
                font-weight: 800 !important;
                margin: 0 0 4px 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-section-sub {
                color: var(--text-secondary) !important;
                font-size: 0.92rem !important;
                line-height: 1.55 !important;
                margin: 0 0 18px 0 !important;
            }
            /* Three stacked contact "channel" rows in the left card */
            [data-testid="stAppViewContainer"] .support-channel {
                display: flex !important;
                gap: 14px !important;
                padding: 16px 0 !important;
                border-top: 1px solid var(--border-color) !important;
            }
            [data-testid="stAppViewContainer"] .support-channel:first-of-type {
                border-top: none !important;
                padding-top: 4px !important;
            }
            [data-testid="stAppViewContainer"] .support-channel:last-of-type {
                padding-bottom: 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-channel-icon {
                flex: 0 0 38px !important;
                width: 38px !important;
                height: 38px !important;
                border-radius: 10px !important;
                background: rgba(59, 130, 246, 0.12) !important;
                color: #3b82f6 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }
            [data-testid="stAppViewContainer"] .support-channel-icon svg {
                width: 18px !important;
                height: 18px !important;
            }
            [data-testid="stAppViewContainer"] .support-channel-body {
                flex: 1 1 auto !important;
                min-width: 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-channel-body h4 {
                color: var(--text-primary) !important;
                font-size: 0.98rem !important;
                font-weight: 700 !important;
                margin: 0 0 4px 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-channel-body p {
                color: var(--text-secondary) !important;
                font-size: 0.88rem !important;
                line-height: 1.5 !important;
                margin: 0 0 4px 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-channel-body p:last-child {
                margin-bottom: 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-channel-body a {
                color: #3b82f6 !important;
                text-decoration: none !important;
            }
            [data-testid="stAppViewContainer"] .support-channel-body a:hover {
                text-decoration: underline !important;
            }
            [data-testid="stAppViewContainer"] .support-doc-list {
                list-style: none !important;
                padding: 0 !important;
                margin: 6px 0 0 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-doc-list li {
                margin: 0 !important;
                padding: 3px 0 !important;
                color: var(--text-secondary) !important;
                font-size: 0.88rem !important;
            }
            /* Form column — small caps section dividers between "your details"
               and "your message" so the form scans as two phases, not one
               long stack. */
            [data-testid="stAppViewContainer"] .support-form-section-label {
                color: var(--text-secondary) !important;
                font-size: 0.74rem !important;
                font-weight: 800 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.08em !important;
                margin: 18px 0 4px 0 !important;
                padding-bottom: 6px !important;
                border-bottom: 1px solid var(--border-color) !important;
            }
            [data-testid="stAppViewContainer"] .support-form-section-label.first {
                margin-top: 4px !important;
            }
            /* Submit row — left-align so the button doesn't span the card */
            [data-testid="stAppViewContainer"] .st-key-support_form_card div[data-testid="stFormSubmitButton"] button {
                width: auto !important;
                min-width: 160px !important;
            }
            [data-testid="stAppViewContainer"] .support-privacy-note {
                color: var(--text-secondary) !important;
                font-size: 0.82rem !important;
                line-height: 1.5 !important;
                margin: 14px 0 0 0 !important;
            }
            [data-testid="stAppViewContainer"] .support-privacy-note a {
                color: #3b82f6 !important;
                text-decoration: none !important;
            }
            [data-testid="stAppViewContainer"] .support-privacy-note a:hover {
                text-decoration: underline !important;
            }
            @media (max-width: 900px) {
                [data-testid="stAppViewContainer"] .support-page-shell {
                    margin-top: -38px !important;
                }
                [data-testid="stAppViewContainer"] .support-page-shell .landing-clean-title {
                    font-size: 1.75rem !important;
                }
                [data-testid="stAppViewContainer"] .st-key-support_info_card,
                [data-testid="stAppViewContainer"] .st-key-support_form_card {
                    padding: 18px 16px !important;
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
                    <h2 class="landing-clean-title">Get in touch</h2>
                    <p class="landing-clean-subtitle">
                        Have a question, found a bug, or want to share feedback? Send us
                        a message — we read every one. Most replies go out within
                        2–3 business days.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        left, right = st.columns([1.1, 1.9], gap="large")
        with left:
            with st.container(key="support_info_card"):
                st.markdown('<p class="support-section-title">Reach us</p>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="support-section-sub">Pick the channel that fits your question best.</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"""
                    <div class="support-channel">
                        <div class="support-channel-icon">{_MAIL_ICON}</div>
                        <div class="support-channel-body">
                            <h4>Email</h4>
                            <p><a href="mailto:support@excelcv.app">support@excelcv.app</a></p>
                            <p>Best for account issues and urgent bugs.</p>
                        </div>
                    </div>
                    <div class="support-channel">
                        <div class="support-channel-icon">{_CLOCK_ICON}</div>
                        <div class="support-channel-body">
                            <h4>Response time</h4>
                            <p>Within <strong>2–3 business days</strong>.</p>
                            <p>Best effort — no SLA, since ExcelCV is a portfolio project.</p>
                        </div>
                    </div>
                    <div class="support-channel">
                        <div class="support-channel-icon">{_BOOK_ICON}</div>
                        <div class="support-channel-body">
                            <h4>Try the docs first</h4>
                            <p>Most questions are answered in our guides:</p>
                            <ul class="support-doc-list">
                                <li>→ <a href="{how_it_works_href}" target="_self">How It Works</a></li>
                                <li>→ <a href="{resume_tips_href}" target="_self">Resume Tips</a></li>
                                <li>→ <a href="{privacy_href}" target="_self">Privacy Policy</a></li>
                            </ul>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        with right:
            with st.container(key="support_form_card"):
                st.markdown(
                    '<p class="support-section-title">Send a message</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<p class="support-section-sub">Fields marked * are required.</p>',
                    unsafe_allow_html=True,
                )
                with st.form("contact_page_form", clear_on_submit=True):
                    st.markdown(
                        '<div class="support-form-section-label first">Your details</div>',
                        unsafe_allow_html=True,
                    )
                    col_name, col_email = st.columns(2)
                    with col_name:
                        name = st.text_input("Your name *", placeholder="Enter your name")
                    with col_email:
                        email = st.text_input("Email address *", placeholder="you@example.com")

                    st.markdown(
                        '<div class="support-form-section-label">Your message</div>',
                        unsafe_allow_html=True,
                    )
                    inquiry = st.selectbox(
                        "Inquiry type *",
                        options=["General Inquiry", "Technical Support", "Feedback / Suggestion"],
                        index=None,
                        placeholder="Choose an inquiry type…",
                    )
                    subject = st.text_input("Subject *", placeholder="How can we help?")
                    message = st.text_area(
                        "Message *",
                        height=160,
                        placeholder=(
                            "Share as much detail as you can — what you were trying to "
                            "do, what happened, and any error messages you saw."
                        ),
                    )
                    sent = st.form_submit_button("Send message", type="primary")

                if sent:
                    if not name.strip() or not email.strip() or not message.strip():
                        st.error("Please fill in your name, email, and message.")
                    elif "@" not in email or "." not in email.split("@", 1)[-1]:
                        st.error("Enter a valid email address so we can reply to you.")
                    elif not inquiry:
                        st.error("Please choose an inquiry type.")
                    elif is_email_configured():
                        ok = send_contact_email(
                            name.strip(),
                            email.strip(),
                            inquiry,
                            subject.strip() or "(no subject)",
                            message.strip(),
                        )
                        if ok:
                            # Best-effort acknowledgement back to the submitter —
                            # background thread so the success banner shows
                            # immediately without waiting for a second SMTP send.
                            import threading as _threading

                            _threading.Thread(
                                target=send_acknowledgement_email,
                                args=(email.strip(), name.strip(), inquiry, message.strip()),
                                daemon=True,
                            ).start()
                            st.success(
                                f"Thanks, {name.strip()}! Your message has been sent — "
                                "we'll reply within 2–3 business days."
                            )
                        else:
                            st.warning(
                                "Message could not be delivered right now. "
                                "Please email us directly at `support@excelcv.app`."
                            )
                    else:
                        st.warning(
                            "Email delivery is not configured in this deployment, so your "
                            "message could not be sent. Please email `support@excelcv.app` "
                            "directly and we'll get back to you."
                        )

                st.markdown(
                    f'<p class="support-privacy-note">Your message is sent to '
                    f"<strong>support@excelcv.app</strong> and isn't shared with third "
                    f'parties. See our <a href="{privacy_href}" target="_self">Privacy Policy</a>.</p>',
                    unsafe_allow_html=True,
                )
        return

    # Fallback for unknown routes.
    _render_info_page_header("Page Not Found")
    st.warning("The requested page is unavailable. Use the navigation links to continue.")
