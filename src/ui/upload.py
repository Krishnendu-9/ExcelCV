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
    """Render richer landing sections with distinct visual bands and messaging."""
    landing_html = dedent(
        """
        <div class="landing-extended">
            <section class="landing-panel panel-story landing-reveal">
                <div class="story-copy">
                    <p class="section-kicker">ExcelCV workflow</p>
                    <h2 class="section-title">A more focused resume checker, designed to feel premium and actionable.</h2>
                    <p class="section-subtitle">Run one clean flow: paste the role description, upload your resume, and get structured ATS plus content feedback in seconds.</p>
                    <div class="story-chip-row">
                        <span class="story-chip">ATS diagnostics</span>
                        <span class="story-chip">Impact checks</span>
                        <span class="story-chip">Section health</span>
                        <span class="story-chip">Action plan</span>
                    </div>
                    <div class="story-metric-row">
                        <div class="story-metric">
                            <span class="metric-value">4</span>
                            <span class="metric-label">Core categories</span>
                        </div>
                        <div class="story-metric">
                            <span class="metric-value">2</span>
                            <span class="metric-label">Download formats</span>
                        </div>
                        <div class="story-metric">
                            <span class="metric-value">1</span>
                            <span class="metric-label">Standard mode</span>
                        </div>
                    </div>
                </div>
                <div class="story-visual" aria-hidden="true">
                    <div class="story-orb orb-a"></div>
                    <div class="story-orb orb-b"></div>
                    <div class="story-visual-card">
                        <p class="visual-title">Live score insight</p>
                        <p class="visual-score">92 / 100</p>
                        <div class="visual-track">
                            <span style="width:92%;"></span>
                        </div>
                        <div class="visual-lines">
                            <span></span><span></span><span></span><span></span>
                        </div>
                    </div>
                </div>
            </section>
            <section class="landing-panel panel-spectrum landing-reveal">
                <div class="section-head">
                    <p class="section-kicker">Beyond basic checks</p>
                    <h3 class="section-headline">Distinct analysis blocks so users can scan quickly and act faster.</h3>
                </div>
                <div class="spectrum-grid">
                    <article class="spectrum-card">
                        <h4>ATS parse diagnostics</h4>
                        <p>Checks whether your resume structure can be parsed by applicant tracking systems.</p>
                    </article>
                    <article class="spectrum-card">
                        <h4>Quantifying Impact</h4>
                        <p>Highlights bullets that need metrics, outcomes, or measurable evidence.</p>
                    </article>
                    <article class="spectrum-card">
                        <h4>Repetition Signals</h4>
                        <p>Finds repeated wording and encourages stronger, varied phrasing.</p>
                    </article>
                    <article class="spectrum-card">
                        <h4>Spelling and Grammar</h4>
                        <p>Keeps language quality recruiter-ready with clearer presentation.</p>
                    </article>
                    <article class="spectrum-card">
                        <h4>Section Completeness</h4>
                        <p>Verifies required resume sections and highlights what is missing.</p>
                    </article>
                    <article class="spectrum-card">
                        <h4>ATS Essentials</h4>
                        <p>Checks file type, size, links, and contact formatting for submission quality.</p>
                    </article>
                </div>
            </section>
            <section class="landing-panel panel-walkthrough landing-reveal">
                <div class="section-head">
                    <p class="section-kicker">How it works</p>
                    <h3 class="section-headline">Three-step flow with clear progression for first-time users.</h3>
                </div>
                <div class="walkthrough-grid">
                    <article class="walk-card">
                        <span class="walk-index">01</span>
                        <h4>Paste job description</h4>
                        <p>Add requirements, skills, and seniority expectations from the role you target.</p>
                    </article>
                    <article class="walk-card">
                        <span class="walk-index">02</span>
                        <h4>Upload resume PDF</h4>
                        <p>We extract text and run deterministic checks before scoring the result.</p>
                    </article>
                    <article class="walk-card">
                        <span class="walk-index">03</span>
                        <h4>Review and improve</h4>
                        <p>Use section-level guidance and export results to iterate quickly.</p>
                    </article>
                </div>
            </section>
            <section class="landing-panel panel-proof landing-reveal">
                <div class="proof-grid">
                    <div class="proof-tile">
                        <p class="proof-label">Cost to use</p>
                        <p class="proof-value">100% Free</p>
                    </div>
                    <div class="proof-tile">
                        <p class="proof-label">Scoring model</p>
                        <p class="proof-value">Standard scoring</p>
                    </div>
                    <div class="proof-tile">
                        <p class="proof-label">Export formats</p>
                        <p class="proof-value">Markdown + JSON</p>
                    </div>
                    <div class="proof-tile">
                        <p class="proof-label">Data lifecycle</p>
                        <p class="proof-value">Session only</p>
                    </div>
                </div>
            </section>
            <section class="landing-panel panel-faq landing-reveal">
                <div class="section-head">
                    <p class="section-kicker">FAQs</p>
                    <h3 class="section-headline">Frequently asked questions for users before they upload their resume.</h3>
                </div>
                <div class="faq-grid">
                    <div class="faq-card">
                        <h4>Do I need to pay to use this checker?</h4>
                        <p>No. The complete workflow is free inside this app.</p>
                    </div>
                    <div class="faq-card">
                        <h4>How is the final score calculated?</h4>
                        <p>One standard scoring model combines ATS readiness and content-quality checks.</p>
                    </div>
                    <div class="faq-card">
                        <h4>What file type is supported?</h4>
                        <p>PDF is supported. Text-based PDFs provide the best extraction accuracy.</p>
                    </div>
                    <div class="faq-card">
                        <h4>Can I save my result?</h4>
                        <p>Yes. Download the report as Markdown or JSON directly from the results page.</p>
                    </div>
                </div>
            </section>
        </div>
        """
    ).strip()

    landing_html = "\n".join(line.lstrip() for line in landing_html.splitlines())

    st.markdown(
        landing_html,
        unsafe_allow_html=True,
    )




