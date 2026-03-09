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
                <div class="list-row"><span>ATS Parse Rate</span><span>✓</span></div>
                <div class="list-row"><span>Quantifying Impact</span><span>✓</span></div>
                <div class="list-row"><span>Repetition</span><span>⚠</span></div>
                <div class="list-row"><span>Spelling & Grammar</span><span>✕</span></div>
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
                <p class="landing-kicker">ExcelCV - Free GenAI Resume Reviewer</p>
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
                    <p class="mode-eyebrow">Mode 1</p>
                    <h4>General Review</h4>
                    <p>Balanced assessment of clarity, relevance, and overall resume quality.</p>
                </div>
                <div class="landing-mode-card">
                    <p class="mode-eyebrow">Mode 2</p>
                    <h4>ATS Scan</h4>
                    <p>Strict keyword and format-focused pass for ATS optimization scenarios.</p>
                </div>
                <div class="landing-mode-card">
                    <p class="mode-eyebrow">Debug</p>
                    <h4>Transparent AI output</h4>
                    <p>Enable debug mode to inspect raw model responses while troubleshooting.</p>
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
                    <p>Switch analysis modes, inspect gaps, and apply suggestions before your next application.</p>
                </div>
            </div>
            <div class="landing-proof-grid">
                <div class="proof-tile">
                    <p class="proof-label">Cost to use</p>
                    <p class="proof-value">100% Free</p>
                </div>
                <div class="proof-tile">
                    <p class="proof-label">Analysis modes</p>
                    <p class="proof-value">2 Modes</p>
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
                    <h4>Can I compare ATS Scan and General Review results?</h4>
                    <p>Yes. Change mode from the top controls to re-run analysis using stored CV text and JD.</p>
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

