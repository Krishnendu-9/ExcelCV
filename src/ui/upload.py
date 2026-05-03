"""
Upload-page preview card rendering.
"""

from textwrap import dedent

import streamlit as st


def render_upload_preview_card() -> None:
    """Static preview card on the upload screen."""
    st.markdown(
        """
        <div class="upload-preview">
            <div class="preview-card">
                <div class="preview-header">
                    <div>
                        <div style="font-weight:700;" class="text-primary">ATS Resume Score</div>
                        <div class="text-muted" style="font-size:0.9rem;">Sample preview</div>
                    </div>
                    <div class="preview-badge">LIVE</div>
                </div>
                <div class="preview-score"><span class="num">92</span><span class="den">/100</span></div>
                <div class="pill-row">
                    <span class="pill">ATS Parse</span>
                    <span class="pill">Quantified Impact</span>
                    <span class="pill">Sections</span>
                    <span class="pill">Skills</span>
                </div>
                <div class="progress-shell">
                    <div class="progress-track">
                        <div class="progress-fill" style="width:90%;"></div>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.9rem;margin-top:6px;" class="text-secondary">
                        <span>Parse rate</span><span>90%</span>
                    </div>
                </div>
                <div class="list-row"><span>ATS Parse Rate</span><span>&#10003;</span></div>
                <div class="list-row"><span>Quantifying Impact</span><span>&#10003;</span></div>
                <div class="list-row"><span>Repetition</span><span>&#9888;</span></div>
                <div class="list-row"><span>Spelling & Grammar</span><span>&#10005;</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_landing_sections() -> None:
    """Render simple homepage sections under the main upload/compare area."""
    landing_html = dedent(
        """
        <div class="landing-extended">
            <section class="landing-clean-section landing-intro-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">ExcelCV workflow</span>
                    <h2 class="landing-clean-title">How our free resume checker works</h2>
                    <p class="landing-clean-subtitle">
                        Our AI-powered scanner analyzes your resume like top ATS systems and recruiters.
                    </p>
                </div>
                <div class="landing-clean-grid steps-grid">
                    <article class="landing-clean-card">
                        <div class="landing-clean-icon">1</div>
                        <h4>Upload your resume</h4>
                        <p>Upload PDF or DOCX and we extract resume text for ATS-friendly evaluation.</p>
                    </article>
                    <article class="landing-clean-card">
                        <div class="landing-clean-icon">2</div>
                        <h4>ATS compatibility analysis</h4>
                        <p>We check ATS parse diagnostics, sections, and formatting strength.</p>
                    </article>
                    <article class="landing-clean-card">
                        <div class="landing-clean-icon">3</div>
                        <h4>Get your resume score</h4>
                        <p>Receive actionable feedback and downloadable report output for improvements.</p>
                    </article>
                </div>
            </section>
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">Complete resume analysis</span>
                    <h3 class="landing-clean-title">Advanced resume scanner features</h3>
                    <p class="landing-clean-subtitle">
                        Everything you need to create an ATS-friendly resume that gets noticed.
                    </p>
                </div>
                <div class="landing-clean-grid features-grid">
                    <article class="landing-clean-card">
                        <h4>ATS parse diagnostics</h4>
                        <p>Evaluate how applicant tracking systems read and parse your resume structure.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Resume score calculator</h4>
                        <p>Get an instant score with strengths, weaknesses, and clear improvement direction.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Keyword optimization</h4>
                        <p>Find missing role keywords and improve JD relevance for better shortlisting.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>CV format analysis</h4>
                        <p>Check file formatting for readability and ATS compatibility across systems.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Industry feedback</h4>
                        <p>Receive practical recommendations aligned with your target role and domain.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Free review</h4>
                        <p>Use the full analysis workflow without sign-up requirements or hidden costs.</p>
                    </article>
                </div>
            </section>
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">Common Questions</span>
                    <h3 class="landing-clean-title">Frequently asked questions</h3>
                    <p class="landing-clean-subtitle">
                        Quick answers before you upload your next resume draft.
                    </p>
                </div>
                <div class="landing-clean-grid faq-clean-grid">
                    <article class="landing-clean-card">
                        <h4>Is the resume checker really free?</h4>
                        <p>Yes. Resume analysis and report download are available at no cost in this app.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>What file formats are supported?</h4>
                        <p>PDF and DOCX are supported. Text-based resumes typically produce best results.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Do you store my resume data?</h4>
                        <p>Resume content is processed in session and is not retained for long-term storage.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>How long does analysis take?</h4>
                        <p>Most runs complete quickly and return a structured report in under a minute.</p>
                    </article>
                </div>
            </section>
            <section class="landing-clean-cta">
                <h3>Start your free resume analysis now</h3>
                <p>Join more job seekers who improved their resumes with clear ATS feedback.</p>
                <div class="landing-clean-cta-pills">
                    <span>No registration required</span>
                    <span>Instant results</span>
                    <span>100% free</span>
                </div>
            </section>
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">Why choose ExcelCV</span>
                    <h3 class="landing-clean-title">Built for clarity, speed, and practical feedback</h3>
                </div>
                <div class="landing-clean-grid benefits-grid">
                    <article class="landing-clean-card"><p>Compare your resume against role expectations.</p></article>
                    <article class="landing-clean-card"><p>Improve interview callback chance with better keyword coverage.</p></article>
                    <article class="landing-clean-card"><p>Detect formatting issues that block ATS parsing.</p></article>
                    <article class="landing-clean-card"><p>Identify missing sections and contact information quickly.</p></article>
                    <article class="landing-clean-card"><p>Get JD alignment feedback with explainable scoring context.</p></article>
                    <article class="landing-clean-card"><p>Track actionable next steps for resume improvement.</p></article>
                </div>
            </section>
            <!-- COMMENTED OUT: Resume checker success stories (fake testimonials — restore when real data available)
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">Success stories</span>
                    <h3 class="landing-clean-title">Resume checker success stories</h3>
                </div>
                <div class="landing-clean-grid stories-grid">
                    <article class="landing-clean-card">
                        <p class="story-tag">CV score: 65 -> 92</p>
                        <p>"The ATS scanner found issues I never knew existed. I landed more interviews quickly."</p>
                        <h5>Sara J.</h5>
                        <span>Software Engineer</span>
                    </article>
                    <article class="landing-clean-card">
                        <p class="story-tag">Interview rate: +80%</p>
                        <p>"Keyword suggestions helped me pass ATS filters that I was missing before."</p>
                        <h5>James C.</h5>
                        <span>Marketing Manager</span>
                    </article>
                    <article class="landing-clean-card">
                        <p class="story-tag">ATS score: 58 -> 95</p>
                        <p>"Detailed feedback made my resume stronger and easier for recruiters to review."</p>
                        <h5>Jessica W.</h5>
                        <span>Financial Analyst</span>
                    </article>
                </div>
            </section>
            -->
            <!-- COMMENTED OUT: Latest resume and career tips (blog cards have no links — restore when blog pages are complete)
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">From the blog</span>
                    <h3 class="landing-clean-title">Latest resume and career tips</h3>
                </div>
                <div class="landing-clean-grid blog-grid">
                    <article class="landing-clean-card">
                        <p class="story-tag">Resume Help</p>
                        <h4>10 resume tips that help you get hired</h4>
                        <p>Learn practical steps to make your resume stand out to ATS and recruiters.</p>
                    </article>
                    <article class="landing-clean-card">
                        <p class="story-tag">Job Interviews</p>
                        <h4>How to prepare for your next interview</h4>
                        <p>A structured checklist to convert resume shortlists into interview success.</p>
                    </article>
                    <article class="landing-clean-card">
                        <p class="story-tag">Job Search</p>
                        <h4>Effective job search strategy in 2026</h4>
                        <p>Simple, consistent steps for better applications and stronger profile visibility.</p>
                    </article>
                </div>
            </section>
            -->
            <section class="landing-clean-footnote">
                <p>ExcelCV helps you analyze, improve, and share a stronger ATS-ready resume.</p>
            </section>
        </div>
        """
    ).strip()

    landing_html = "\n".join(line.lstrip() for line in landing_html.splitlines())

    st.markdown(
        landing_html,
        unsafe_allow_html=True,
    )

import streamlit.components.v1 as components

from src.auth_utils import get_session_user
from src.ui.analysis_runner import (
    _autosave_analysis,
    run_multi_resume_comparison,
    run_single_analysis,
)
from src.ui.app_utils import _build_page_href, _sanitize_cv_filename, _save_report_snapshot
from src.ui.common import issue_count

def render_upload_page(compare_mode: bool = False) -> None:
    """Landing page: upload CV + JD."""
    _current_user = get_session_user()
    with st.container(key="hero_wrapper"):
        left, right = st.columns([1.0, 1.0], gap="medium")
        with right:
            render_upload_preview_card()
            analysis_status_slot = st.container()

        with left:
            st.markdown(
                """
                <div class="hero-copy">
                    <h1 class="hero-title">Is your resume <span>good enough?</span></h1>
                    <p class="hero-subtitle">
                        Drop your resume, paste the JD, and get an ATS-ready report in seconds.
                    </p>
                    <div class="hero-chip-row">
                        <span class="hero-chip">100% free</span>
                        <span class="hero-chip">Free account</span>
                        <span class="hero-chip">History saved</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if _current_user:
                # ── Logged-in: show full upload form ──────────────────────────────
                with st.form("upload_form"):
                    jd = st.text_area(
                        "Job description",
                        key="jd",
                        height=120,
                        placeholder="Paste the role description, must-have skills, and seniority expectations.",
                    )
                    uploaded_cv = st.file_uploader(
                        "Upload resume (PDF or DOCX)",
                        type=["pdf", "docx"],
                        key="cvs",
                        accept_multiple_files=False,
                        help="PDF or DOCX supported. Maximum file size: 2MB.",
                    )
                    submitted = st.form_submit_button("Upload & analyze", use_container_width=True)
                    st.caption("Max 2MB per file.")
                    st.markdown(
                        '<div class="privacy-note">&#128274; Analysis is saved to your account history.</div>',
                        unsafe_allow_html=True,
                    )

                if submitted:
                    result = run_single_analysis(
                        jd,
                        uploaded_cv,
                        status_container=analysis_status_slot,
                    )
                    if result:
                        analysis, cv_text = result
                        safe_cv_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "CV.pdf"))
                        st.session_state["cv_text"] = cv_text
                        st.session_state["job_description"] = jd
                        st.session_state["analysis"] = analysis
                        st.session_state["cv_name"] = safe_cv_name
                        st.session_state["cv_file_size"] = getattr(uploaded_cv, "size", 0)
                        st.session_state["issues"] = issue_count(analysis)
                        st.session_state["page"] = "report"
                        st.query_params["page"] = "report"
                        snapshot_id = _save_report_snapshot()
                        st.session_state["report_snapshot_id"] = snapshot_id
                        st.query_params["rid"] = snapshot_id
                        _autosave_analysis(safe_cv_name, jd, analysis)
                        st.rerun()

            else:
                # ── Guest: JD preview + sign-in prompt in place of file uploader ──
                st.text_area(
                    "Job description",
                    key="jd_guest",
                    height=120,
                    placeholder="Paste the role description, must-have skills, and seniority expectations.",
                )
                _auth_href = _build_page_href("auth", next_page="upload-cv")
                with st.container(key="upload_guest_box"):
                    st.markdown(
                        f"""
                        <div class="guest-auth-shell">
                            <div class="guest-auth-icon">&#128274;</div>
                            <p class="guest-auth-title">
                                Sign in to upload your resume
                            </p>
                            <p class="guest-auth-copy">
                                Get AI-powered ATS scores, keyword gaps, and save your full
                                analysis history &mdash; free forever.
                            </p>
                            <a href="{_auth_href}" target="_self" class="guest-auth-cta">
                                Sign In / Create Account &rarr;
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Full-width comparison section (not one-sided).
    if compare_mode:
        components.html(
            """
            <script>
            (function() {
                var target = window.parent && window.parent !== window ? window.parent : window;
                var doc = target.document;
                setTimeout(function() {
                    var anchor = doc.getElementById("compare-section-anchor");
                    if (anchor) {
                        anchor.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                }, 120);
            })();
            </script>
            """,
            height=0,
        )

    st.markdown('<div id="compare-section-anchor"></div>', unsafe_allow_html=True)
    st.markdown('<div class="compare-section-shell">', unsafe_allow_html=True)
    if compare_mode:
        st.markdown(
            '<div class="compare-mode-badge">Comparison mode active</div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <h3 class="compare-section-title">Compare Multiple Resumes (2-5 files)</h3>
        <p class="compare-section-subtitle">
            Use one job description and rank candidates side-by-side using final score, ATS parse,
            section quality, issue count, and top missing skills.
        </p>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="compare_form_box"):
        if get_session_user():
            with st.form("comparison_form"):
                compare_jd = st.text_area(
                    "Job description for comparison",
                    key="compare_jd",
                    value=st.session_state.get("jd", ""),
                    height=130,
                    placeholder="Paste the role description once and compare multiple resumes.",
                )
                compare_files = st.file_uploader(
                    "Upload 2-5 resumes (PDF or DOCX)",
                    type=["pdf", "docx"],
                    key="compare_cvs",
                    accept_multiple_files=True,
                    help="Maximum 2MB per file. We will rank resumes by final score.",
                )
                run_compare = st.form_submit_button("Run comparison", use_container_width=True)
        else:
            run_compare = False
            compare_jd = ""
            compare_files = []
            _auth_href2 = _build_page_href("auth", next_page="compare-cv")
            st.markdown(
                f"""
                <div class="guest-auth-shell">
                    <div class="guest-auth-icon">&#128274;</div>
                    <p class="guest-auth-title">
                        Sign in to compare resumes
                    </p>
                    <p class="guest-auth-copy">
                        Upload 2–5 resumes and rank them side-by-side — free forever.
                    </p>
                    <a href="{_auth_href2}" target="_self" class="guest-auth-cta">
                        Sign In / Create Account &rarr;
                    </a>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if run_compare:
        try:
            with st.spinner("Comparing resumes..."):
                comparison = run_multi_resume_comparison(compare_jd, compare_files or [])
            st.session_state["comparison_results"] = comparison.get("rows", [])
            st.session_state["comparison_errors"] = comparison.get("errors", [])
        except ValueError as exc:
            st.error(str(exc))

    comparison_rows = st.session_state.get("comparison_results", [])
    comparison_errors = st.session_state.get("comparison_errors", [])
    if comparison_rows:
        st.markdown('<div class="compare-results-title">Comparison Results</div>', unsafe_allow_html=True)
        st.dataframe(comparison_rows, use_container_width=True, hide_index=True)
        best = comparison_rows[0]
        st.success(
            f"Top match: {best.get('Resume')} with final score {best.get('Final Score')}."
        )
    if comparison_errors:
        st.warning("Some files could not be analyzed:\n- " + "\n- ".join(comparison_errors))

    st.markdown(
        """
        <div class="compare-next-shell">
            <h4 class="compare-next-title">What happens next?</h4>
            <ul class="compare-next-list">
                <li>ExcelCV analyzes each resume for ATS quality, content strength, and role alignment.</li>
                <li>You get ranked comparison results with score breakdown and detected issue count.</li>
                <li>Top missing skills are highlighted so you can quickly compare candidate gaps.</li>
                <li>Use the same JD across files to keep ranking consistent and decision-ready.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    render_upload_landing_sections()

