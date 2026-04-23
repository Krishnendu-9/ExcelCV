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


