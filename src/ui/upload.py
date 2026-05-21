"""
Upload-page preview card rendering.
"""

import csv
import hashlib
import html
from io import BytesIO, StringIO
from textwrap import dedent

import streamlit as st
import streamlit.components.v1 as components

from src.auth_utils import get_session_user
from src.config import MAX_FILE_MB
from src.ui.analysis_runner import (
    _autosave_analysis,
    run_multi_resume_comparison,
    run_single_analysis,
)
from src.ui.app_utils import (
    _build_page_href,
    _clear_comparison_run_artifacts,
    _sanitize_cv_filename,
    _save_report_snapshot,
)
from src.ui.common import issue_count


def render_upload_preview_card() -> None:
    """Animated 'live report' illustration shown beside the hero copy."""
    st.markdown(
        """
        <div class="hv-stats">
            <div class="hv-stat-item">
                <span class="hv-stat-val">5.4s</span>
                <span class="hv-stat-label">avg analysis</span>
            </div>
            <div class="hv-stat-divider"></div>
            <div class="hv-stat-item">
                <span class="hv-stat-val">11</span>
                <span class="hv-stat-label">scoring metrics</span>
            </div>
            <div class="hv-stat-divider"></div>
            <div class="hv-stat-item">
                <span class="hv-stat-val">100%</span>
                <span class="hv-stat-label">free</span>
            </div>
            <div class="hv-stat-divider"></div>
            <div class="hv-stat-item">
                <span class="hv-stat-val">50+</span>
                <span class="hv-stat-label">CVs scored</span>
            </div>
        </div>
        <div class="hv-steps">
            <div class="hv-step">
                <div class="hv-step-num">1</div>
                <div class="hv-step-body">
                    <div class="hv-step-title">Upload</div>
                    <div class="hv-step-desc">PDF or DOCX</div>
                </div>
            </div>
            <div class="hv-step-arrow">&rarr;</div>
            <div class="hv-step">
                <div class="hv-step-num">2</div>
                <div class="hv-step-body">
                    <div class="hv-step-title">Paste JD</div>
                    <div class="hv-step-desc">role description</div>
                </div>
            </div>
            <div class="hv-step-arrow">&rarr;</div>
            <div class="hv-step">
                <div class="hv-step-num">3</div>
                <div class="hv-step-body">
                    <div class="hv-step-title">Get scored</div>
                    <div class="hv-step-desc">in seconds</div>
                </div>
            </div>
        </div>
        <div class="hero-visual">
            <div class="hv-glow"></div>
            <div class="hv-top">
                <div class="hv-header">
                    <span class="hv-dot"></span>
                    <span class="hv-title">ATS Resume Report</span>
                    <span class="hv-live">SAMPLE</span>
                </div>
                <div class="hv-ring-wrap">
                    <div class="hv-ring"></div>
                    <div class="hv-ring-label">
                        <span class="hv-score">86</span>
                        <span class="hv-out">OUT OF 100</span>
                    </div>
                </div>
                <div class="hv-grade">Strong match &mdash; recruiter-ready</div>
            </div>
            <div class="hv-bottom">
                <div class="hv-bars">
                    <div class="hv-bar-row">
                        <span class="hv-bar-name">Content</span>
                        <span class="hv-bar"><span class="hv-bar-fill" style="--w:92%"></span></span>
                        <span class="hv-bar-val">92%</span>
                    </div>
                    <div class="hv-bar-row">
                        <span class="hv-bar-name">Sections</span>
                        <span class="hv-bar"><span class="hv-bar-fill" style="--w:88%"></span></span>
                        <span class="hv-bar-val">88%</span>
                    </div>
                    <div class="hv-bar-row">
                        <span class="hv-bar-name">ATS Essentials</span>
                        <span class="hv-bar"><span class="hv-bar-fill" style="--w:100%"></span></span>
                        <span class="hv-bar-val">100%</span>
                    </div>
                    <div class="hv-bar-row">
                        <span class="hv-bar-name">Insights</span>
                        <span class="hv-bar"><span class="hv-bar-fill" style="--w:80%"></span></span>
                        <span class="hv-bar-val">80%</span>
                    </div>
                </div>
                <div class="hv-tips">
                    <span class="hv-tip">Quantify achievements with concrete metrics</span>
                    <span class="hv-tip">Add missing keyword: &ldquo;Kubernetes&rdquo;</span>
                    <span class="hv-tip">Trim the summary to three sharp lines</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # JS to align the demo card's TOP with the Job description card's TOP on
    # the left side of the hero_wrapper. Runs in the parent document, watches
    # for layout changes.
    components.html(
        """
<script>
(function () {
    var w = window.parent && window.parent !== window ? window.parent : window;
    var doc = w.document;

    function alignHero() {
        var wrapper = doc.querySelector('.st-key-hero_wrapper');
        if (!wrapper) return;
        var hero = wrapper.querySelector('.hero-visual');
        var jdBox = wrapper.querySelector('[data-testid="stTextArea"]');
        if (!hero || !jdBox) return;
        // Reset any prior offset so we measure clean.
        hero.style.marginTop = '0px';
        var jdTop = jdBox.getBoundingClientRect().top;
        var heroTop = hero.getBoundingClientRect().top;
        var offset = jdTop - heroTop;
        // Only nudge DOWN (positive marginTop). Pulling up via negative
        // margin caused the card to collide with the steps strip above it.
        // If natural flow places hero below JD, we accept that small offset.
        if (offset > 4) {
            hero.style.marginTop = Math.round(offset) + 'px';
        }
    }

    // Run shortly after render, then again to catch late layout changes.
    setTimeout(alignHero, 60);
    setTimeout(alignHero, 240);
    setTimeout(alignHero, 720);

    // Re-align on window resize.
    if (!w.__excelcvHeroAlignResize) {
        w.__excelcvHeroAlignResize = true;
        w.addEventListener('resize', function () {
            setTimeout(alignHero, 60);
        });
    }

    // Observe the wrapper for size/content changes (Streamlit reruns) and re-align.
    try {
        var wrapper0 = doc.querySelector('.st-key-hero_wrapper');
        if (wrapper0 && !wrapper0.__excelcvHeroAlignObserver) {
            var obs = new w.ResizeObserver(function () { alignHero(); });
            obs.observe(wrapper0);
            wrapper0.__excelcvHeroAlignObserver = obs;
        }
    } catch (e) {}

    // ── Count-up animation for the hero score number ───────────────────
    function animateScore() {
        var el = doc.querySelector('.hv-score');
        if (!el || el.__excelcvCounted) return;
        var target = parseInt(el.getAttribute('data-target') || el.textContent, 10);
        if (!isFinite(target) || target <= 0) return;
        el.__excelcvCounted = true;
        // Match the score bar's hv-sweep animation: 1.7s duration with .25s delay.
        var duration = 1700;
        var startDelay = 250;
        var startTs = null;
        function easeOut(t) { return 1 - Math.pow(1 - t, 3); }
        function step(ts) {
            if (startTs === null) startTs = ts;
            var t = Math.min(1, (ts - startTs) / duration);
            el.textContent = Math.round(easeOut(t) * target).toString();
            if (t < 1) w.requestAnimationFrame(step);
            else el.textContent = target.toString();
        }
        setTimeout(function () { w.requestAnimationFrame(step); }, startDelay);
    }

    // Honor prefers-reduced-motion: skip the count-up entirely.
    try {
        if (w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            var elN = doc.querySelector('.hv-score');
            if (elN) elN.__excelcvCounted = true;
        }
    } catch (e) {}

    setTimeout(animateScore, 80);
    setTimeout(animateScore, 320);
})();
</script>
""",
        height=0,
    )


def render_upload_landing_sections() -> None:
    """Render simple homepage sections under the main upload/compare area."""
    landing_html = dedent(
        """
        <div class="landing-extended">
            <section class="landing-clean-section">
                <div class="landing-clean-head">
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
                        <p>Guest runs stay in-session; signed-in users can save analyses and comparisons to their account history.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>How long does analysis take?</h4>
                        <p>Most runs complete quickly and return a structured report in under a minute.</p>
                    </article>
                </div>
            </section>
            <section class="landing-clean-section landing-showcase-section">
                <div class="landing-clean-head">
                    <h3 class="landing-clean-title">More than just a checker</h3>
                    <p class="landing-clean-subtitle">
                        ExcelCV is a full career platform &mdash; analyze, compare, write, build, and track in one place.
                    </p>
                </div>
                <div class="landing-showcase-grid">
                    <article class="landing-showcase-card">
                        <div class="lsc-emoji">📋</div>
                        <h4 class="lsc-title">Resume Builder</h4>
                        <div class="lsc-mock lsc-mock-builder">
                            <div class="lsc-mb-rail">
                                <span class="lsc-mb-section active"></span>
                                <span class="lsc-mb-section"></span>
                                <span class="lsc-mb-section"></span>
                                <span class="lsc-mb-section"></span>
                            </div>
                            <div class="lsc-mb-editor">
                                <span class="lsc-mb-line lsc-mb-h"></span>
                                <span class="lsc-mb-line lsc-mb-l1"></span>
                                <span class="lsc-mb-line lsc-mb-l2"></span>
                                <span class="lsc-mb-line lsc-mb-l3"></span>
                            </div>
                            <div class="lsc-mb-preview">
                                <span class="lsc-mb-pname"></span>
                                <span class="lsc-mb-pmeta"></span>
                                <span class="lsc-mb-prule"></span>
                                <span class="lsc-mb-pline"></span>
                                <span class="lsc-mb-pline lsc-mb-pline-short"></span>
                            </div>
                        </div>
                        <p class="lsc-desc">3 templates &middot; live preview &middot; AI bullet suggestions &middot; one-click PDF.</p>
                    </article>
                    <article class="landing-showcase-card">
                        <div class="lsc-emoji">📊</div>
                        <h4 class="lsc-title">Compare Resumes</h4>
                        <div class="lsc-mock lsc-mock-compare">
                            <div class="lsc-cmp-row lsc-cmp-winner">
                                <span class="lsc-cmp-rank">★ 1</span>
                                <span class="lsc-cmp-name"></span>
                                <span class="lsc-cmp-score lsc-good">91</span>
                            </div>
                            <div class="lsc-cmp-row">
                                <span class="lsc-cmp-rank">2</span>
                                <span class="lsc-cmp-name"></span>
                                <span class="lsc-cmp-score lsc-mid">74</span>
                            </div>
                            <div class="lsc-cmp-row">
                                <span class="lsc-cmp-rank">3</span>
                                <span class="lsc-cmp-name"></span>
                                <span class="lsc-cmp-score lsc-mid">68</span>
                            </div>
                            <div class="lsc-cmp-row">
                                <span class="lsc-cmp-rank">4</span>
                                <span class="lsc-cmp-name"></span>
                                <span class="lsc-cmp-score lsc-low">52</span>
                            </div>
                        </div>
                        <p class="lsc-desc">Rank 2&ndash;5 CVs against one JD with sort, drill-down, and PDF export.</p>
                    </article>
                    <article class="landing-showcase-card">
                        <div class="lsc-emoji">✉️</div>
                        <h4 class="lsc-title">Cover Letter</h4>
                        <div class="lsc-mock lsc-mock-letter">
                            <div class="lsc-cl-head">
                                <span class="lsc-cl-name"></span>
                                <span class="lsc-cl-date"></span>
                            </div>
                            <span class="lsc-cl-line"></span>
                            <span class="lsc-cl-line"></span>
                            <span class="lsc-cl-line lsc-cl-line-short"></span>
                            <span class="lsc-cl-line"></span>
                            <span class="lsc-cl-line lsc-cl-line-short"></span>
                            <div class="lsc-cl-foot">
                                <span class="lsc-cl-pill">DOCX</span>
                            </div>
                        </div>
                        <p class="lsc-desc">AI-tailored to your resume + JD. Optional tone, company, role. DOCX export.</p>
                    </article>
                    <article class="landing-showcase-card">
                        <div class="lsc-emoji">📁</div>
                        <h4 class="lsc-title">Your History</h4>
                        <div class="lsc-mock lsc-mock-history">
                            <div class="lsc-hi-row">
                                <span class="lsc-hi-dot"></span>
                                <span class="lsc-hi-name"></span>
                                <span class="lsc-hi-score lsc-good">88</span>
                            </div>
                            <div class="lsc-hi-row">
                                <span class="lsc-hi-dot"></span>
                                <span class="lsc-hi-name"></span>
                                <span class="lsc-hi-score lsc-mid">72</span>
                            </div>
                            <div class="lsc-hi-row">
                                <span class="lsc-hi-dot"></span>
                                <span class="lsc-hi-name"></span>
                                <span class="lsc-hi-score lsc-good">94</span>
                            </div>
                            <div class="lsc-hi-row">
                                <span class="lsc-hi-dot"></span>
                                <span class="lsc-hi-name"></span>
                                <span class="lsc-hi-score lsc-mid">65</span>
                            </div>
                        </div>
                        <p class="lsc-desc">Saved CVs, analyses, and comparisons &mdash; survive logout, all per-user.</p>
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
            <section class="landing-clean-section landing-compare-section">
                <div class="landing-clean-head">
                    <p class="landing-compare-lead">Built differently. Built openly.</p>
                    <h3 class="landing-clean-title">Why ExcelCV instead of a generic ATS scanner?</h3>
                    <p class="landing-clean-subtitle">
                        Most ATS tools give you a number and a keyword list. ExcelCV gives you a full report card &mdash; and the tools to act on it.
                    </p>
                </div>
                <div class="landing-compare-wrap">
                    <table class="landing-compare-table">
                        <thead>
                            <tr>
                                <th class="lc-th-feature">Feature</th>
                                <th class="lc-th-other">Generic ATS scanners</th>
                                <th class="lc-th-us">ExcelCV</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="lc-feature">Score explainability</td>
                                <td class="lc-other">Single black-box number</td>
                                <td class="lc-us">11 metrics &middot; weighted breakdown &middot; per-check feedback</td>
                            </tr>
                            <tr>
                                <td class="lc-feature">Multi-resume comparison</td>
                                <td class="lc-other">One at a time</td>
                                <td class="lc-us">Up to 5 side-by-side with sortable ranking</td>
                            </tr>
                            <tr>
                                <td class="lc-feature">Cover letter generation</td>
                                <td class="lc-other">Not included</td>
                                <td class="lc-us">AI-tailored, DOCX download</td>
                            </tr>
                            <tr>
                                <td class="lc-feature">Resume builder</td>
                                <td class="lc-other">External tool needed</td>
                                <td class="lc-us">Built-in &middot; 3 templates &middot; live preview &middot; PDF export</td>
                            </tr>
                            <tr>
                                <td class="lc-feature">Saved history</td>
                                <td class="lc-other">Often locked behind paywall</td>
                                <td class="lc-us">My CVs &middot; My Analyses &middot; My Comparisons &mdash; free</td>
                            </tr>
                            <tr>
                                <td class="lc-feature">Pricing</td>
                                <td class="lc-other">Subscription / per-scan fees</td>
                                <td class="lc-us">100% free, no card required</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>
            <!-- COMMENTED OUT: Resume checker success stories (fake testimonials — restore when real data available)
            <section class="landing-clean-section">
                <div class="landing-clean-head">
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
        </div>
        """
    ).strip()

    landing_html = "\n".join(line.lstrip() for line in landing_html.splitlines())

    st.markdown(
        landing_html,
        unsafe_allow_html=True,
    )


def _comparison_input_signature(
    job_description: str, uploaded_cvs: list[object]
) -> tuple[str, tuple[tuple[str, int], ...]]:
    """Build a stable signature for comparison inputs to detect stale results."""
    normalized_jd = (job_description or "").strip().lower()
    file_tokens: list[tuple[str, int]] = []
    for uploaded_cv in uploaded_cvs or []:
        safe_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "resume")).lower()
        file_size = int(getattr(uploaded_cv, "size", 0) or 0)
        file_tokens.append((safe_name, file_size))
    return normalized_jd, tuple(sorted(file_tokens))


class _InMemoryUploadedFile:
    """Minimal uploaded-file compatible wrapper backed by bytes."""

    def __init__(self, name: str, raw_bytes: bytes) -> None:
        self.name = name
        self.size = len(raw_bytes)
        self._raw_bytes = raw_bytes
        self._buffer = BytesIO(raw_bytes)

    def read(self, *args, **kwargs):
        return self._buffer.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._buffer.seek(*args, **kwargs)

    def getvalue(self) -> bytes:
        return self._raw_bytes


def _read_uploaded_cv_bytes(uploaded_cv) -> bytes:
    """Read an UploadedFile's contents defensively.

    Streamlit's first-interaction-in-a-session edge cases can make ``getvalue()``
    return a non-``bytes`` buffer (e.g., ``bytearray`` or an empty value before
    the upload finishes hydrating). Returning ``b""`` here lets the caller treat
    the file as "unreadable on this attempt" and surface a clear message instead
    of silently dropping the file.
    """
    try:
        if hasattr(uploaded_cv, "getvalue"):
            data = uploaded_cv.getvalue()
            if isinstance(data, (bytes, bytearray)) and len(data) > 0:
                return bytes(data)
    except Exception:
        pass
    try:
        if hasattr(uploaded_cv, "seek"):
            uploaded_cv.seek(0)
        if hasattr(uploaded_cv, "read"):
            data = uploaded_cv.read()
            if isinstance(data, (bytes, bytearray)) and len(data) > 0:
                if hasattr(uploaded_cv, "seek"):
                    try:
                        uploaded_cv.seek(0)
                    except Exception:
                        pass
                return bytes(data)
    except Exception:
        pass
    return b""


def _format_file_size(file_size_bytes: int) -> str:
    """Return display-friendly file size text."""
    if file_size_bytes >= 1024 * 1024:
        return f"{file_size_bytes / (1024 * 1024):.1f}MB"
    return f"{file_size_bytes / 1024:.1f}KB"


def _build_staged_compare_uploads(staged_files: list[dict[str, object]]) -> list[object]:
    """Convert staged file records into uploaded-file compatible wrappers."""
    uploads: list[object] = []
    for item in staged_files:
        file_name = str(item.get("name", "resume.pdf"))
        raw_bytes = item.get("bytes")
        if isinstance(raw_bytes, bytes):
            uploads.append(_InMemoryUploadedFile(file_name, raw_bytes))
    return uploads


def _render_selected_compare_files(staged_files: list[dict[str, object]]) -> int | None:
    """Render compact selected-file rows with inline delete actions."""
    if not staged_files:
        return None

    st.markdown(
        """
        <style>
        .st-key-compare_selected_list_box [data-testid="stVerticalBlock"] > div {
            margin-bottom: 8px !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] {
            border: 1px solid rgba(148, 163, 184, 0.32);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.66);
            padding: 0 10px;
            min-height: 54px;
            display: flex !important;
            align-items: center !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] > [data-testid="stVerticalBlock"] {
            width: 100%;
            min-height: 54px !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] > [data-testid="stVerticalBlock"] > div {
            margin: 0 !important;
            width: 100%;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stHorizontalBlock"] {
            display: flex !important;
            align-items: center !important;
            min-height: 54px !important;
            height: 54px !important;
            margin: 0 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            align-self: stretch !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stElementContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="column"] {
            display: flex !important;
            align-items: center !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="column"] > div {
            width: 100%;
            height: 100%;
            display: flex !important;
            align-items: center !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="column"] [data-testid="stVerticalBlock"] {
            width: 100%;
            height: 100%;
            display: flex !important;
            justify-content: center !important;
            gap: 0 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="column"] [data-testid="stVerticalBlock"] > div {
            margin: 0 !important;
        }
        body.theme-dark .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] {
            border-color: rgba(100, 116, 139, 0.5);
            background: rgba(15, 23, 42, 0.5);
        }
        .st-key-compare_selected_list_box .compare-file-icon {
            font-size: 1.25rem;
            line-height: 1;
            opacity: 0.9;
        }
        .st-key-compare_selected_list_box .compare-file-meta {
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 0;
            width: 100%;
            line-height: 1;
            min-height: 30px;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stMarkdownContainer"] {
            margin: 0 !important;
            line-height: 1 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            line-height: 1 !important;
        }
        .st-key-compare_selected_list_box .compare-file-meta > span {
            display: inline-flex;
            align-items: center;
        }
        .st-key-compare_selected_list_box .compare-file-name {
            font-weight: 600;
            color: #1f2937;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.15;
        }
        body.theme-dark .st-key-compare_selected_list_box .compare-file-name {
            color: #e2e8f0;
        }
        .st-key-compare_selected_list_box .compare-file-size {
            color: #64748b;
            font-size: 0.92rem;
            white-space: nowrap;
            line-height: 1.15;
        }
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button[data-testid="baseButton-secondary"],
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] {
            min-height: 30px !important;
            min-width: 30px !important;
            width: 30px !important;
            padding: 0 !important;
            border-radius: 7px !important;
            border: 1px solid rgba(148, 163, 184, 0.5) !important;
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            filter: none !important;
            color: #334155 !important;
            transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease !important;
        }
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] > div,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] > div > div,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button > div,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button > div > div,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button *,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] * {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            color: inherit !important;
        }
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button:hover,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button:focus-visible,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"]:hover,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"]:focus-visible {
            background: rgba(239, 68, 68, 0.12) !important;
            border-color: rgba(239, 68, 68, 0.75) !important;
            color: #dc2626 !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button,
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] {
            color: #cbd5e1 !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button:hover,
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button:focus-visible,
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"]:hover,
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"]:focus-visible {
            background: rgba(239, 68, 68, 0.18) !important;
            border-color: rgba(248, 113, 113, 0.8) !important;
            color: #fca5a5 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"],
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] > [data-testid="stVerticalBlock"],
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] > [data-testid="stVerticalBlock"] > div {
            height: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-testid="stButton"] {
            width: 100%;
            height: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            margin: 0 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-testid="stButton"] > button {
            margin: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    deleted_index: int | None = None
    with st.container(key="compare_selected_list_box"):
        for row_start in range(0, len(staged_files), 2):
            row_cols = st.columns(2, gap="small")
            for col_offset, col in enumerate(row_cols):
                idx = row_start + col_offset
                if idx >= len(staged_files):
                    continue
                item = staged_files[idx]
                file_name = str(item.get("name", "resume.pdf"))
                file_size = int(item.get("size", 0) or 0)
                with col:
                    with st.container(key=f"compare_file_row_{idx}"):
                        row_col, action_col = st.columns([14, 1], gap="small")
                        with row_col:
                            st.markdown(
                                f"""
                                <div class="compare-file-meta">
                                    <span class="compare-file-icon">CV</span>
                                    <span class="compare-file-name">{html.escape(file_name)}</span>
                                    <span class="compare-file-size">{_format_file_size(file_size)}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with action_col:
                            with st.container(key=f"compare_file_delete_btn_{idx}"):
                                if st.button(
                                    ":material/delete:",
                                    key=f"compare_delete_{idx}",
                                    type="tertiary",
                                ):
                                    deleted_index = idx
    return deleted_index


def _clear_comparison_session_state() -> None:
    """Clear all comparison state — run artifacts plus form inputs.

    Used by callers that want a full reset (e.g. "start over" flows). Run-only
    artifact cleanup goes through ``_clear_comparison_run_artifacts`` in
    ``app_utils`` so the run-vs-form lifecycle is owned in one place.
    """
    _clear_comparison_run_artifacts()
    st.session_state.pop("compare_upload_warnings", None)
    st.session_state.pop("compare_upload_hydration_retries", None)
    st.session_state.pop("compare_jd", None)
    st.session_state.pop("compare_selected_files", None)
    st.session_state.pop("compare_cvs_rev", None)
    for key in list(st.session_state.keys()):
        if str(key).startswith("compare_cvs_input_"):
            st.session_state.pop(key, None)


def _comparison_rows_to_csv(rows: list[dict[str, object]], ordered_columns: list[str]) -> str:
    """Serialize comparison rows into a CSV string with stable column order."""
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=ordered_columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in ordered_columns})
    return buffer.getvalue()


def _render_compare_form_card(current_user) -> None:
    """Render the compare form (or guest CTA) and, on submit, navigate to compare-report."""
    if not current_user:
        # ── Guest: TWO separate cards — JD textarea (input) + sign-in CTA (action) ──
        st.text_area(
            "Job description for comparison",
            key="compare_jd_guest",
            height=92,
            placeholder="Paste the role description once and compare multiple resumes.",
        )
        _auth_href2 = _build_page_href("auth", next_page="compare-cv")
        with st.container(key="compare_guest_box"):
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
        return

    with st.container(key="compare_form_box"):
        if "compare_jd" not in st.session_state and st.session_state.get("jd"):
            st.session_state["compare_jd"] = st.session_state.get("jd", "")
        if "compare_selected_files" not in st.session_state:
            st.session_state["compare_selected_files"] = []
        if "compare_cvs_rev" not in st.session_state:
            st.session_state["compare_cvs_rev"] = 0

        compare_jd = st.text_area(
            "Job description for comparison",
            key="compare_jd",
            height=50,
            placeholder="Paste the role description once and compare multiple resumes.",
        )
        compare_uploader_key = (
            f"compare_cvs_input_{int(st.session_state.get('compare_cvs_rev', 0))}"
        )
        newly_uploaded = st.file_uploader(
            "Upload 2-5 resumes (PDF or DOCX)",
            type=["pdf", "docx"],
            key=compare_uploader_key,
            accept_multiple_files=True,
            help=f"Maximum {MAX_FILE_MB}MB per file. We will rank resumes by final score.",
        )

        staged_files: list[dict[str, object]] = list(
            st.session_state.get("compare_selected_files", [])
        )
        if newly_uploaded:
            seen_signatures = {str(item.get("signature", "")) for item in staged_files}
            duplicate_names: list[str] = []
            skipped_over_limit = 0
            unreadable_names: list[str] = []
            added_count = 0
            for uploaded_cv in newly_uploaded:
                safe_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "resume.pdf"))
                raw_bytes = _read_uploaded_cv_bytes(uploaded_cv)
                if not raw_bytes:
                    unreadable_names.append(safe_name)
                    continue
                file_size = len(raw_bytes)
                file_hash = hashlib.sha256(raw_bytes).hexdigest()
                signature = f"{safe_name.lower()}|{file_size}|{file_hash}"
                if signature in seen_signatures:
                    duplicate_names.append(safe_name)
                    continue
                if len(staged_files) >= 5:
                    skipped_over_limit += 1
                    continue
                staged_files.append(
                    {
                        "name": safe_name,
                        "size": file_size,
                        "bytes": raw_bytes,
                        "signature": signature,
                    }
                )
                seen_signatures.add(signature)
                added_count += 1

            # First-interaction hydration race: Streamlit's UploadedFile can
            # return empty bytes on the very first run of a session, before
            # the upload finishes hydrating. If every file in this batch came
            # back unreadable AND nothing else made progress, treat it as a
            # transient race: silently rerun (up to MAX_HYDRATION_RETRIES) and
            # try the read again. Only surface the "could not read" warning
            # after the retries are exhausted — otherwise the user sees a
            # phantom error on every first upload of a session.
            MAX_HYDRATION_RETRIES = 2
            had_progress = bool(added_count or duplicate_names or skipped_over_limit)
            unreadable_only_batch = bool(unreadable_names) and not had_progress
            retry_count = int(st.session_state.get("compare_upload_hydration_retries", 0))

            if unreadable_only_batch and retry_count < MAX_HYDRATION_RETRIES:
                st.session_state["compare_upload_hydration_retries"] = retry_count + 1
                # Don't bump the uploader rev — the same widget state must
                # re-deliver the files on the next pass so we can re-read them.
                st.rerun()

            # Past this point we either made progress or genuinely exhausted
            # retries, so the hydration counter has done its job.
            st.session_state["compare_upload_hydration_retries"] = 0

            # Replace warnings each batch instead of appending so stale messages
            # from a previous batch (e.g. a retried hydration race) don't linger
            # after a successful upload.
            upload_warnings_for_ui: list[str] = []
            if duplicate_names:
                upload_warnings_for_ui.append(
                    "Already selected and skipped: " + ", ".join(duplicate_names)
                )
            if skipped_over_limit > 0:
                upload_warnings_for_ui.append(
                    f"Only 5 resumes are allowed. Skipped {skipped_over_limit} extra file(s)."
                )
            if unreadable_names:
                upload_warnings_for_ui.append(
                    "Could not read these files (try re-selecting): " + ", ".join(unreadable_names)
                )
            st.session_state["compare_upload_warnings"] = upload_warnings_for_ui
            st.session_state["compare_selected_files"] = staged_files
            # Only reset the uploader widget (via key change) when at least one
            # file made it through. If everything failed to read, leave the
            # widget key untouched so the user's selection isn't silently wiped.
            if had_progress:
                st.session_state["compare_cvs_rev"] = (
                    int(st.session_state.get("compare_cvs_rev", 0)) + 1
                )
            st.rerun()

        staged_files = list(st.session_state.get("compare_selected_files", []))
        if staged_files:
            st.markdown("**Selected resumes**")
            deleted_index = _render_selected_compare_files(staged_files)
            if deleted_index is not None:
                del staged_files[deleted_index]
                st.session_state["compare_selected_files"] = staged_files
                st.rerun()

        # Surface any upload-stage warnings (dedup, size cap, unreadable file)
        # inside the form so users see them next to the controls that produced
        # them, not buried on the report page.
        upload_warnings = list(st.session_state.get("compare_upload_warnings", []))
        if upload_warnings:
            st.info("\n".join(f"- {w}" for w in upload_warnings))

        compare_files = _build_staged_compare_uploads(staged_files)
        run_compare = st.button("Run comparison", key="run_compare_btn", width="stretch")
        progress_slot = st.empty()

    comparison_signature = _comparison_input_signature(compare_jd, compare_files or [])
    last_signature = st.session_state.get("comparison_signature")
    if last_signature and last_signature != comparison_signature and not run_compare:
        # Inputs changed since the last run; drop stale results AND the
        # "attempted" flag so the report page's empty state reads as
        # "no comparison yet" instead of "your last run produced 0 rows".
        _clear_comparison_run_artifacts()
        st.info("Comparison inputs changed. Run comparison again to refresh results.")

    if run_compare:
        try:
            _run_comparison_with_progress(
                compare_jd,
                compare_files or [],
                comparison_signature,
                progress_slot,
            )
        except ValueError as exc:
            # Validation errors (missing JD, too few/many files) belong on the
            # form page itself — no navigation needed.
            _clear_comparison_run_artifacts()
            st.error(str(exc))


def _run_comparison_with_progress(
    compare_jd: str,
    compare_files: list[object],
    comparison_signature: tuple,
    progress_slot,
) -> None:
    """Run the comparison while streaming per-file status into ``progress_slot``.

    Sequential by design — see [analysis_runner.run_multi_resume_comparison]: a
    Gemini 429 on file N short-circuits files N+1..end, which only works if the
    files are processed in order.
    """
    total = max(1, len(compare_files))
    status_lines: list[str] = []
    icon_by_status = {
        "running": "&#9203;",  # ⏳
        "done": "&#9989;",  # ✅
        "error": "&#10060;",  # ❌
        "skipped": "&#9888;&#65039;",  # ⚠️
    }

    def _render_progress(current_idx: int, current_total: int) -> None:
        header = (
            f'<div class="compare-progress-header">Analyzing resume '
            f"<strong>{current_idx}</strong> of <strong>{current_total}</strong>…</div>"
        )
        body = "".join(
            f'<li class="compare-progress-item compare-progress-item--{cls}">'
            f'<span class="compare-progress-icon">{icon_by_status.get(cls, "")}</span>'
            f'<span class="compare-progress-name">{html.escape(name)}</span>'
            f'<span class="compare-progress-status">{label}</span>'
            f"</li>"
            for name, cls, label in status_lines
        )
        progress_slot.markdown(
            f'<div class="compare-progress-shell">{header}'
            f'<ul class="compare-progress-list">{body}</ul></div>',
            unsafe_allow_html=True,
        )

    def _on_progress(file_name: str, idx: int, total_files: int, status: str) -> None:
        label_for_status = {
            "running": "analyzing…",
            "done": "done",
            "error": "failed",
            "skipped": "skipped (rate limit)",
        }.get(status, status)
        # Update existing line if we already started this file, else append.
        for pos, (existing_name, _existing_cls, _existing_label) in enumerate(status_lines):
            if existing_name == file_name:
                status_lines[pos] = (file_name, status, label_for_status)
                break
        else:
            status_lines.append((file_name, status, label_for_status))
        _render_progress(idx, total_files)

    _render_progress(0, total)
    comparison = run_multi_resume_comparison(
        compare_jd,
        compare_files,
        progress_callback=_on_progress,
    )
    progress_slot.empty()

    rows = comparison.get("rows", [])
    run_errors = comparison.get("errors", [])
    run_warnings = comparison.get("warnings", [])
    st.session_state["comparison_results"] = rows
    st.session_state["comparison_errors"] = run_errors
    st.session_state["comparison_warnings"] = run_warnings
    st.session_state["comparison_signature"] = comparison_signature
    st.session_state["comparison_attempted"] = True
    # Once the run committed, drop transient upload-stage warnings — they
    # described the now-stale selection state.
    st.session_state.pop("compare_upload_warnings", None)
    # Persist successful runs (>= 1 ranked row) to the DB so signed-in users
    # can revisit them from the My Comparisons page without re-uploading.
    # Failure is silent — autosave is a convenience, not a critical path.
    if rows:
        from src.ui.compare_report import _autosave_comparison

        _autosave_comparison(rows, compare_jd, run_errors, run_warnings)
    # Always navigate to the dedicated report page once a comparison was
    # attempted — even when every file failed. The report page's empty
    # state then surfaces the per-file errors/warnings so the user can
    # see WHY it failed (rate limit, unreadable PDF, etc.) instead of a
    # generic "no rows" message that hides the real cause.
    # One-shot flag consumed by compare_report.py so the new page lands
    # at scroll position 0 — without it the browser preserves the scroll
    # offset from mid-page on the upload form.
    st.session_state["scroll_compare_report_to_top"] = True
    st.session_state["page"] = "compare-report"
    try:
        st.query_params["page"] = "compare-report"
    except Exception:
        pass
    st.rerun()


def render_upload_page(compare_mode: bool = False) -> None:
    """Landing page: upload CV + JD."""
    _current_user = get_session_user()
    # Set when the upload form is submitted; the analysis itself runs *after* the
    # whole page is rendered and all layout contexts have closed (see end of fn).
    pending_analysis = None  # tuple[str, UploadedFile] | None
    with st.container(key="hero_wrapper"):
        left, right = st.columns([1.0, 1.0], gap="medium")
        with right:
            render_upload_preview_card()
            analysis_status_slot = st.container(key="analysis_status_box")

        with left:
            st.markdown(
                """
                <div class="hero-copy">
                    <h1 class="hero-title">Is your resume <span>good enough?</span></h1>
                    <p class="hero-subtitle">Drop your resume, paste the job description, and get an ATS-ready score with &mdash; in seconds.</p>
                    <div class="hero-chip-row">
                        <span class="hero-chip">&#10003; 100% free</span>
                        <span class="hero-chip">&#10003; ATS-scored</span>
                        <span class="hero-chip">&#10003; Instant fixes</span>
                        <span class="hero-chip">&#10003; History saved</span>
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
                        height=92,
                        placeholder="Paste the role description, must-have skills, and seniority expectations.",
                    )
                    uploaded_cv = st.file_uploader(
                        "Upload resume (PDF or DOCX)",
                        type=["pdf", "docx"],
                        key="cvs",
                        accept_multiple_files=False,
                        help="PDF or DOCX supported. Maximum file size: 2MB.",
                    )
                    submitted = st.form_submit_button("Upload & analyze", width="stretch")

                if submitted:
                    pending_analysis = (jd, uploaded_cv)

            else:
                # ── Guest: JD preview + sign-in prompt in place of file uploader ──
                st.text_area(
                    "Job description",
                    key="jd_guest",
                    height=92,
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

    # Instant landing on the compare section when arriving via top-nav action.
    should_anchor_compare = st.session_state.pop("scroll_to_compare_anchor", False)
    if should_anchor_compare:
        components.html(
            """
            <script>
            (function() {
                var target = window.parent && window.parent !== window ? window.parent : window;
                var doc = target.document;
                var tryScroll = function() {
                    var anchor = doc.getElementById("compare-section-anchor");
                    if (anchor) {
                        try { anchor.scrollIntoView({ behavior: "instant", block: "start" }); }
                        catch (_e) { anchor.scrollIntoView(true); }
                    }
                };
                [0, 50, 150, 400].forEach(function(ms) { setTimeout(tryScroll, ms); });
            })();
            </script>
            """,
            height=0,
        )

    st.markdown(
        '<div id="compare-section-anchor" style="scroll-margin-top: 130px;"></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="compare_section_shell"):
        if compare_mode:
            st.markdown(
                '<div class="compare-mode-badge">Comparison mode active</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            """
            <div class="landing-clean-head">
                <h2 class="landing-clean-title">Compare Multiple Resumes (2-5 files)</h2>
                <p class="landing-clean-subtitle">
                    Use one job description and rank candidates side-by-side using final score,
                    ATS parse, section quality, issue count, and top missing skills.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _cmp_left, _cmp_right = st.columns([1.0, 1.0], gap="medium")
        with _cmp_left:
            _render_compare_form_card(_current_user)
        with _cmp_right:
            st.markdown(
                """
                <div class="compare-preview-card">
                    <div class="cpc-top-match">
                        <div class="cpc-tm-tag">&starf; TOP MATCH &middot; RANK #1</div>
                        <div class="cpc-tm-row">
                            <span class="cpc-tm-name">Alex Rivera</span>
                            <span class="cpc-tm-score">91<span class="cpc-tm-out">/100</span></span>
                        </div>
                        <div class="cpc-tm-bar"><span class="cpc-tm-bar-fill"></span></div>
                        <div class="cpc-tm-metrics">
                            <div class="cpc-tm-metric">
                                <span class="cpc-tm-mlabel">JD Align</span>
                                <span class="cpc-tm-mval cpc-good">92</span>
                            </div>
                            <div class="cpc-tm-metric">
                                <span class="cpc-tm-mlabel">ATS Parse</span>
                                <span class="cpc-tm-mval cpc-good">95</span>
                            </div>
                            <div class="cpc-tm-metric">
                                <span class="cpc-tm-mlabel">Sections</span>
                                <span class="cpc-tm-mval cpc-good">88</span>
                            </div>
                            <div class="cpc-tm-metric">
                                <span class="cpc-tm-mlabel">Issues</span>
                                <span class="cpc-tm-mval cpc-mid">9</span>
                            </div>
                        </div>
                    </div>
                    <div class="cpc-table">
                        <div class="cpc-row cpc-row-winner">
                            <span class="cpc-rank">&starf; 1</span>
                            <span class="cpc-name">Alex Rivera</span>
                            <span class="cpc-bar"><span class="cpc-bar-fill cpc-good-bg" style="--cw:91%"></span></span>
                            <span class="cpc-score cpc-good">91</span>
                        </div>
                        <div class="cpc-row">
                            <span class="cpc-rank">2</span>
                            <span class="cpc-name">Maria Solis</span>
                            <span class="cpc-bar"><span class="cpc-bar-fill cpc-mid-bg" style="--cw:78%"></span></span>
                            <span class="cpc-score cpc-mid">78</span>
                        </div>
                        <div class="cpc-row">
                            <span class="cpc-rank">3</span>
                            <span class="cpc-name">Jordan Kim</span>
                            <span class="cpc-bar"><span class="cpc-bar-fill cpc-mid-bg" style="--cw:65%"></span></span>
                            <span class="cpc-score cpc-mid">65</span>
                        </div>
                        <div class="cpc-row">
                            <span class="cpc-rank">4</span>
                            <span class="cpc-name">Sam Patel</span>
                            <span class="cpc-bar"><span class="cpc-bar-fill cpc-low-bg" style="--cw:52%"></span></span>
                            <span class="cpc-score cpc-low">52</span>
                        </div>
                    </div>
                    <div class="cpc-foot">SAMPLE &middot; what a real ranking looks like</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if st.session_state.get("comparison_results"):
            _view_compare_results_href = _build_page_href("compare-report")
            st.markdown(
                f"""
                <div class="compare-view-results-row">
                    <a href="{_view_compare_results_href}" target="_self" class="compare-view-results-link">
                        View latest comparison results &rarr;
                    </a>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(
            """
            <div class="compare-feature-chips">
                <div class="cfc-chip">
                    <span class="cfc-icon">&#9889;</span>
                    <span class="cfc-text"><strong>2&ndash;5 resumes</strong> ranked side-by-side</span>
                </div>
                <div class="cfc-chip">
                    <span class="cfc-icon">&#128202;</span>
                    <span class="cfc-text"><strong>8 sort options</strong> &middot; rank re-numbers live</span>
                </div>
                <div class="cfc-chip">
                    <span class="cfc-icon">&starf;</span>
                    <span class="cfc-text"><strong>Identity-locked</strong> top-match pill</span>
                </div>
                <div class="cfc-chip">
                    <span class="cfc-icon">&#128229;</span>
                    <span class="cfc-text"><strong>CSV + PDF</strong> export &middot; auto-saved</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Marker for the end of the Compare Resumes section. The scroll-spy uses
    # this to know when the user has scrolled past both top-of-page sections
    # so it can clear both Analyze CV and Compare Resumes nav highlights.
    st.markdown('<div id="compare-section-end"></div>', unsafe_allow_html=True)

    render_upload_landing_sections()

    # Scroll-spy: three states keyed off where the viewport's reference line
    # (top + 130px, matching the compare anchor's scroll-margin-top) sits
    # relative to the start/end markers of the Compare section.
    #   - reference line above compare-section-anchor  → Analyze CV active
    #   - between compare-section-anchor and compare-section-end → Compare Resumes active
    #   - below compare-section-end → neither active (user has scrolled past both)
    components.html(
        """
        <script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            var doc = target.document;
            var attempts = 0;
            var attach = function() {
                var startAnchor = doc.getElementById("compare-section-anchor");
                var endAnchor = doc.getElementById("compare-section-end");
                var analyzeItem = doc.querySelector('a.site-nav-item[data-nav-action="upload-cv"]');
                var compareItem = doc.querySelector('a.site-nav-item[data-nav-action="compare-anchor"]');
                if (!startAnchor || !endAnchor || !analyzeItem || !compareItem) {
                    if (attempts++ < 30) setTimeout(attach, 200);
                    return;
                }
                if (target.__excelcv_compare_spy_observer__) {
                    try { target.__excelcv_compare_spy_observer__.disconnect(); } catch (_e) {}
                    target.__excelcv_compare_spy_observer__ = null;
                }
                if (target.__excelcv_compare_spy_scroll__) {
                    try { target.removeEventListener('scroll', target.__excelcv_compare_spy_scroll__, true); } catch (_e) {}
                    try { target.removeEventListener('resize', target.__excelcv_compare_spy_scroll__, true); } catch (_e) {}
                    target.__excelcv_compare_spy_scroll__ = null;
                }
                // Reference line: 130px below viewport top — matches the
                // scroll-margin-top of compare-section-anchor so the active
                // state flips exactly when the heading lands at its anchored
                // resting position.
                var REF_OFFSET = 130;
                var apply = function() {
                    var refY = REF_OFFSET;
                    var startTop = startAnchor.getBoundingClientRect().top;
                    var endTop = endAnchor.getBoundingClientRect().top;
                    var inAnalyze = startTop > refY;
                    var inCompare = !inAnalyze && endTop > refY;
                    analyzeItem.classList.toggle('site-nav-item-active', inAnalyze);
                    compareItem.classList.toggle('site-nav-item-active', inCompare);
                };
                var onScroll = function() {
                    if (target.__excelcv_compare_spy_raf__) return;
                    target.__excelcv_compare_spy_raf__ = target.requestAnimationFrame(function() {
                        target.__excelcv_compare_spy_raf__ = 0;
                        apply();
                    });
                };
                target.addEventListener('scroll', onScroll, true);
                target.addEventListener('resize', onScroll, true);
                target.__excelcv_compare_spy_scroll__ = onScroll;
                apply();
            };
            attach();
        })();
        </script>
        """,
        height=0,
    )

    # Scroll-to-top trigger: when the user clicks "Analyze CV" while already
    # on the home page, app.py sets this flag so we smooth-scroll back to the
    # top of the page (which IS the Analyze CV section). Without this, the
    # nav click would be a visible no-op when the user is scrolled down.
    if st.session_state.pop("scroll_to_analyze_top", False):
        components.html(
            """
            <script>
            (function() {
                var target = window.parent && window.parent !== window ? window.parent : window;
                var tryScroll = function() {
                    try { target.scrollTo({ top: 0, behavior: "auto" }); }
                    catch (_e) { target.scrollTo(0, 0); }
                };
                [0, 50, 150, 400].forEach(function(ms) { setTimeout(tryScroll, ms); });
            })();
            </script>
            """,
            height=0,
        )

    # ── Run the submitted analysis last ───────────────────────────────────────
    # Doing it here — after the whole page is rendered and every `with` layout
    # context (hero_wrapper, columns, the form) has closed cleanly — means the
    # st.rerun() that navigates to the report fires from the function's top
    # level, not from deep inside the hero. That avoids the stale duplicate-hero
    # render that occurred when rerun unwound those contexts mid-render.
    if pending_analysis is not None:
        jd, uploaded_cv = pending_analysis
        result = run_single_analysis(jd, uploaded_cv, status_container=analysis_status_slot)
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
