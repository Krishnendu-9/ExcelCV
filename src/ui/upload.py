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
    """Extended landing-page sections inspired by modern ATS checker layouts."""
    landing_html = dedent(
        """
        <div class="landing-extended">
            <div class="landing-band">
                <p class="landing-kicker">ExcelCV</p>
                <h2 class="landing-title">A complete resume check workflow, without the paywall</h2>
                <p class="landing-subtitle">You get ATS diagnostics, content quality checks, job-description alignment, and downloadable reports in one flow. Built for students and early-career job seekers.</p>
            </div>
            <div class="landing-feature-grid">
                <div class="landing-feature-card">
                    <h3>ATS parse diagnostics</h3>
                    <p>Get parse-rate feedback so your resume can be read correctly by automated screeners.</p>
                </div>
                <div class="landing-feature-card">
                    <h3>Keyword and skill gaps</h3>
                    <p>See missing JD keywords and missing skills before you apply to a role.</p>
                </div>
                <div class="landing-feature-card">
                    <h3>Content quality checks</h3>
                    <p>Review quantification, repetition, and spelling/grammar signals in one report.</p>
                </div>
                <div class="landing-feature-card">
                    <h3>Section completeness</h3>
                    <p>Validate core sections: contact, experience, education, skills, and summary/objective.</p>
                </div>
                <div class="landing-feature-card">
                    <h3>ATS essentials validation</h3>
                    <p>Evaluate file format, size, email professionalism, and header links from your resume data.</p>
                </div>
                <div class="landing-feature-card">
                    <h3>Actionable downloads</h3>
                    <p>Export your review as Markdown or JSON and iterate on your resume quickly.</p>
                </div>
            </div>
            <div class="landing-mode-shell">
                <div class="landing-mode-card">
                    <p class="mode-eyebrow">Scoring</p>
                    <h4>Standard scoring system</h4>
                    <p>One consistent score model for ATS readiness, content quality, and resume strength.</p>
                </div>
                <div class="landing-mode-card">
                    <p class="mode-eyebrow">Coverage</p>
                    <h4>ATS + content checks</h4>
                    <p>Keyword fit, section health, impact quantification, repetition, and grammar in one pass.</p>
                </div>
                <div class="landing-mode-card">
                    <p class="mode-eyebrow">Output</p>
                    <h4>Clear action plan</h4>
                    <p>Get practical, section-level suggestions you can apply directly to your next resume revision.</p>
                </div>
            </div>
            <div class="landing-flow">
                <div class="landing-step">
                    <span class="step-num">01</span>
                    <h4>Paste job description</h4>
                    <p>Add requirements, skills, and seniority expectations from the target role.</p>
                </div>
                <div class="landing-step">
                    <span class="step-num">02</span>
                    <h4>Upload your resume PDF</h4>
                    <p>We extract text, run deterministic checks, and combine them with AI insights.</p>
                </div>
                <div class="landing-step">
                    <span class="step-num">03</span>
                    <h4>Review and improve</h4>
                    <p>Inspect gaps, apply suggestions, and iterate before your next application.</p>
                </div>
            </div>
            <div class="landing-proof-grid">
                <div class="proof-tile">
                    <p class="proof-label">Cost to use</p>
                    <p class="proof-value">100% Free</p>
                </div>
                <div class="proof-tile">
                    <p class="proof-label">Scoring system</p>
                    <p class="proof-value">Standard</p>
                </div>
                <div class="proof-tile">
                    <p class="proof-label">Report exports</p>
                    <p class="proof-value">Markdown + JSON</p>
                </div>
                <div class="proof-tile">
                    <p class="proof-label">Data handling</p>
                    <p class="proof-value">Session-only workflow</p>
                </div>
            </div>
            <div class="landing-faq">
                <h3>Frequently asked questions</h3>
                <div class="landing-faq-item">
                    <h4>Do I need to pay to use this checker?</h4>
                    <p>No. This project is intentionally free to use with the core feature set available in-app.</p>
                </div>
                <div class="landing-faq-item">
                    <h4>How is the final score calculated?</h4>
                    <p>We use one standard scoring system that combines ATS readiness, content quality, and resume fundamentals.</p>
                </div>
                <div class="landing-faq-item">
                    <h4>What file type is supported?</h4>
                    <p>PDF files are supported. Text-based PDFs produce the best extraction quality.</p>
                </div>
                <div class="landing-faq-item">
                    <h4>Can I save the result?</h4>
                    <p>Yes. Download your analysis as Markdown for reading or JSON for structured processing.</p>
                </div>
            </div>
        </div>
        """
    ).strip()

    st.markdown(
        landing_html,
        unsafe_allow_html=True,
    )



