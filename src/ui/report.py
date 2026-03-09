"""
Report-page rendering and interactive sidebar utilities.
"""

import json
from typing import Any, Dict, List

import streamlit as st
import streamlit.components.v1 as components

from src.reporting import build_report_md
from src.ui.common import (
    _markdown_inline_to_html,
    get_category_icon,
    get_score_color_class,
    issue_count,
)

def _build_sidebar_html(score: int, issues: int, categories: list) -> str:
    """Build the entire sidebar as one complete HTML string."""
    issues_cls = 'clickable' if issues > 0 else ''
    issues_attr = 'data-section-id="suggestions"' if issues > 0 else ''

    html = f"""
    <div class="report-sidebar">
        <div class="score-card">
            <div class="score-title text-muted" style="font-size:0.95rem;">Your Score</div>
            <div class="score-number">{score}<span>/100</span></div>
            <div class="issues-text {issues_cls}" {issues_attr}>{issues} issues</div>
        </div>"""

    for title, cat_score, items in categories:
        safe_score = int(cat_score) if cat_score is not None else 0
        badge_cls = get_score_color_class(safe_score)
        category_id = title.lower().replace(" ", "-")
        has_items = len(items) > 0
        cursor = 'cursor:pointer;' if has_items else ''
        chevron = '<span class="category-chevron">&#9660;</span>' if has_items else ''

        html += f"""
        <div class="category">
            <div class="category-head" id="cat-head-{category_id}" style="{cursor}">
                <span class="category-title">
                    <span>{title}</span>
                    {chevron}
                </span>
                <span class="category-score {badge_cls}">{safe_score}%</span>
            </div>"""

        if has_items:
            html += f'<div class="category-items collapsed" id="cat-items-{category_id}">'
            for item in items:
                item_label, status = item[0], item[1]
                score_val = item[2] if len(item) > 2 else None
                badge_class = {"ok": "badge badge-ok", "warn": "badge badge-warn",
                               "error": "badge badge-warn", "lock": "badge badge-lock"
                               }.get(status, "badge badge-warn")

                # For Content category metrics (ATS Parse Rate, Quantifying Impact, Repetition, Spelling & Grammar),
                # always show percentage score, not issue count
                is_content_metric = item_label in ("ATS Parse Rate", "Quantifying Impact", "Repetition", "Spelling & Grammar")
                
                if is_content_metric:
                    # Always show percentage for content metrics
                    if score_val is not None and isinstance(score_val, (int, float)):
                        badge_text = f"{int(score_val)}%"
                    else:
                        badge_text = "N/A"
                elif status in ("warn", "error"):
                    # For other metrics, show issue count if available
                    if score_val is not None and isinstance(score_val, (int, float)):
                        badge_text = f"{int(score_val)} {'issue' if int(score_val) == 1 else 'issues'}"
                    else:
                        badge_text = "Review"
                else:
                    badge_text = {"ok": "No issues", "lock": "Locked"}.get(status, "Review")

                section_id = item_label.lower().replace(" & ", "-").replace(" ", "-").replace("--", "-").strip("-")
                icon_cls = "icon-ok" if status == "ok" else "icon-warn"
                icon = "&#10003;" if status == "ok" else "&#10005;"
                clickable = "clickable" if status != "lock" else ""
                data = f'data-section-id="{section_id}"' if status != "lock" else ""

                html += f"""
                <div class="subitem {clickable}" {data}>
                    <span class="subitem-label-wrap">
                        <span class="subitem-icon {icon_cls}">{icon}</span>
                        <span>{item_label}</span>
                    </span>
                    <span class="{badge_class}">{badge_text}</span>
                </div>"""
            html += '</div>'  # close category-items

        html += '</div>'  # close category

    html += '</div>'  # close report-sidebar
    return html



def _build_sidebar_js() -> str:
    """Build JavaScript for sidebar interactions. Runs in components.html iframe."""
    return """
    <script>
    (function() {
        var doc = window.parent.document;
        var win = window.parent;
        var WRAPPER_ID = 'sidebar-fixed-clone-wrapper';

        /* ─── 1. Toggle expand/collapse for a category ─── */
        function toggleCategory(categoryId) {
            var head = doc.getElementById('cat-head-' + categoryId);
            var items = doc.getElementById('cat-items-' + categoryId);
            if (!head || !items) return;
            if (head.classList.contains('expanded')) {
                head.classList.remove('expanded');
                items.classList.remove('expanded');
                items.classList.add('collapsed');
            } else {
                head.classList.add('expanded');
                items.classList.remove('collapsed');
                items.classList.add('expanded');
            }
        }

        /* ─── 2. Fixed sidebar via clone on document.body ─── */
        function setupFixedSidebar() {
            // Find the ORIGINAL sidebar (the one inside the Streamlit column)
            var original = null;
            doc.querySelectorAll('.report-sidebar').forEach(function(el) {
                if (!el.closest('#' + WRAPPER_ID)) {
                    original = el;
                }
            });
            if (!original) return;

            var leftCol = original.closest('[data-testid="column"]');
            if (!leftCol) return;

            var colRect = leftCol.getBoundingClientRect();
            if (colRect.width < 50) return; // not rendered yet

            // Hide the original visually but keep it in layout to preserve column width
            original.style.setProperty('visibility', 'hidden', 'important');
            original.style.setProperty('height', original.offsetHeight + 'px', 'important');

            // Remove IDs from original so getElementById finds the clone's elements
            original.querySelectorAll('[id]').forEach(function(el) {
                el.setAttribute('data-orig-id', el.id);
                el.removeAttribute('id');
            });

            // Create or reuse the fixed wrapper on document.body
            var wrapper = doc.getElementById(WRAPPER_ID);
            if (!wrapper) {
                wrapper = doc.createElement('div');
                wrapper.id = WRAPPER_ID;
                doc.body.appendChild(wrapper);
            }

            // Position the wrapper exactly over the left column, fixed to viewport
            var padding = 8;
            wrapper.style.cssText =
                'position:fixed;' +
                'top:10px;' +
                'left:' + (colRect.left + padding) + 'px;' +
                'width:' + (colRect.width - padding * 2) + 'px;' +
                'max-height:calc(100vh - 20px);' +
                'overflow-y:auto;' +
                'z-index:9999;' +
                'pointer-events:auto;';

            // Deep-clone the sidebar into the wrapper
            var clone = original.cloneNode(true);
            clone.style.setProperty('visibility', 'visible', 'important');
            clone.style.removeProperty('height');

            // Restore IDs on the clone (so toggleCategory / scrollToSection find them)
            clone.querySelectorAll('[data-orig-id]').forEach(function(el) {
                el.id = el.getAttribute('data-orig-id');
                el.removeAttribute('data-orig-id');
            });

            wrapper.innerHTML = '';
            wrapper.appendChild(clone);

            // Store a flag so we don't repeat unnecessarily
            win.__sidebarFixedDone = true;

            // Handle window resize: reposition wrapper
            if (!win.__sidebarResizeBound) {
                win.__sidebarResizeBound = true;
                win.addEventListener('resize', function() {
                    var col = null;
                    doc.querySelectorAll('.report-sidebar').forEach(function(el) {
                        if (!el.closest('#' + WRAPPER_ID)) col = el.closest('[data-testid="column"]');
                    });
                    if (col) {
                        var r = col.getBoundingClientRect();
                        var w = doc.getElementById(WRAPPER_ID);
                        if (w) {
                            w.style.left = (r.left + padding) + 'px';
                            w.style.width = (r.width - padding * 2) + 'px';
                        }
                    }
                    // Also update right column scroll container on resize
                    setupScrollableContent();
                });
            }
        }

        /* ─── 2.5. Setup scrollable right content area ─── */
        function setupScrollableContent() {
            // Find the right column (the one containing .report-main or detail-card)
            var rightCol = null;
            var leftCol = null;
            
            // First find left column to identify right column
            doc.querySelectorAll('.report-sidebar').forEach(function(el) {
                if (!el.closest('#' + WRAPPER_ID)) {
                    leftCol = el.closest('[data-testid="column"]');
                }
            });
            
            if (!leftCol) return;
            
            // Find the right column (sibling of left column)
            var horizontalBlock = leftCol.closest('[data-testid="stHorizontalBlock"]');
            if (!horizontalBlock) return;
            
            var columns = horizontalBlock.querySelectorAll('[data-testid="column"]');
            if (columns.length < 2) return;
            
            // The right column should be the one that's not the left column
            for (var i = 0; i < columns.length; i++) {
                if (columns[i] !== leftCol) {
                    rightCol = columns[i];
                    break;
                }
            }
            
            if (!rightCol) return;
            
            // Make the right column scrollable with fixed height
            var colRect = rightCol.getBoundingClientRect();
            if (colRect.width < 50) return; // not rendered yet
            
            // Calculate available height (viewport height minus some padding)
            var viewportHeight = win.innerHeight;
            var topOffset = 10; // Match sidebar top offset
            var maxHeight = viewportHeight - (topOffset * 2);
            
            // Hide the original visually but keep it in layout to preserve column width
            rightCol.style.setProperty('visibility', 'hidden', 'important');
            rightCol.style.setProperty('height', rightCol.offsetHeight + 'px', 'important');
            
            // Remove IDs from original so getElementById finds the clone's elements
            rightCol.querySelectorAll('[id]').forEach(function(el) {
                el.setAttribute('data-orig-id', el.id);
                el.removeAttribute('id');
            });
            
            // Create or reuse the fixed wrapper for right content
            var RIGHT_WRAPPER_ID = 'right-content-fixed-wrapper';
            var rightWrapper = doc.getElementById(RIGHT_WRAPPER_ID);
            if (!rightWrapper) {
                rightWrapper = doc.createElement('div');
                rightWrapper.id = RIGHT_WRAPPER_ID;
                doc.body.appendChild(rightWrapper);
            }
            
            // Position the wrapper exactly over the right column, fixed to viewport
            var padding = 8;
            rightWrapper.style.cssText =
                'position:fixed;' +
                'top:' + topOffset + 'px;' +
                'left:' + (colRect.left + padding) + 'px;' +
                'width:' + (colRect.width - padding * 2) + 'px;' +
                'max-height:' + maxHeight + 'px;' +
                'overflow-y:auto;' +
                'overflow-x:hidden;' +
                'z-index:1;' +
                'pointer-events:auto;';
            
            // Deep-clone the right column content into the wrapper
            var clone = rightCol.cloneNode(true);
            clone.style.setProperty('visibility', 'visible', 'important');
            clone.style.removeProperty('height');
            clone.style.removeProperty('position');
            
            // Restore IDs on the clone (so scrollToSection finds them)
            clone.querySelectorAll('[data-orig-id]').forEach(function(el) {
                el.id = el.getAttribute('data-orig-id');
                el.removeAttribute('data-orig-id');
            });
            
            rightWrapper.innerHTML = '';
            rightWrapper.appendChild(clone);
            
            // Store reference to right column wrapper for scrolling
            win.__rightContentColumn = rightWrapper;
            
            // Handle window resize: reposition wrapper
            if (!win.__rightContentResizeBound) {
                win.__rightContentResizeBound = true;
                win.addEventListener('resize', function() {
                    var col = null;
                    doc.querySelectorAll('.report-sidebar').forEach(function(el) {
                        if (!el.closest('#' + WRAPPER_ID)) {
                            var lc = el.closest('[data-testid="column"]');
                            if (lc) {
                                var hb = lc.closest('[data-testid="stHorizontalBlock"]');
                                if (hb) {
                                    var cols = hb.querySelectorAll('[data-testid="column"]');
                                    for (var j = 0; j < cols.length; j++) {
                                        if (cols[j] !== lc) {
                                            col = cols[j];
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    });
                    if (col) {
                        var r = col.getBoundingClientRect();
                        var w = doc.getElementById(RIGHT_WRAPPER_ID);
                        if (w) {
                            w.style.left = (r.left + padding) + 'px';
                            w.style.width = (r.width - padding * 2) + 'px';
                        }
                    }
                });
            }
        }

        /* ─── 3. Scroll to a section in the main content ─── */
        function scrollToSection(sectionId) {
            // Get the scrollable container (right column wrapper)
            var scrollContainer = win.__rightContentColumn;
            if (!scrollContainer) {
                // Fallback: try to find it again
                setupScrollableContent();
                scrollContainer = win.__rightContentColumn;
            }
            
            if (scrollContainer) {
                // Find the element within the scrollable container (clone)
                var el = scrollContainer.querySelector('#' + sectionId);
                if (!el) {
                    // If not found in clone, try original (fallback)
                    el = doc.getElementById(sectionId);
                    if (!el) return;
                    // Fallback to original behavior
                    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    return;
                }
                
                // Calculate scroll position within the container
                var containerRect = scrollContainer.getBoundingClientRect();
                var elementRect = el.getBoundingClientRect();
                
                // Calculate the scroll position needed
                var scrollTop = scrollContainer.scrollTop;
                var elementTop = elementRect.top - containerRect.top + scrollTop;
                
                // Scroll with smooth behavior
                scrollContainer.scrollTo({
                    top: elementTop - 10, // 10px offset from top
                    behavior: 'smooth'
                });
                
                // Brief highlight animation
                el.style.transition = 'background-color 0.3s ease';
                var origBg = el.style.backgroundColor || '';
                el.style.backgroundColor = 'rgba(16,185,129,0.15)';
                setTimeout(function() { 
                    el.style.backgroundColor = origBg; 
                }, 1200);
            } else {
                // Fallback to original behavior if container not found
                var el = doc.getElementById(sectionId);
                if (!el) return;
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                // Brief highlight animation
                el.style.transition = 'background-color 0.3s ease';
                var origBg = el.style.backgroundColor || '';
                el.style.backgroundColor = 'rgba(16,185,129,0.15)';
                setTimeout(function() { el.style.backgroundColor = origBg; }, 1200);
            }
        }

        /* ─── 4. Event delegation for clicks (works on both original and clone) ─── */
        function handleClick(e) {
            var t = e.target;
            if (!t || !t.closest) return;

            var head = t.closest('.category-head');
            if (head && head.id && head.id.indexOf('cat-head-') === 0) {
                toggleCategory(head.id.replace('cat-head-', ''));
                e.stopPropagation();
                e.preventDefault();
                return;
            }
            var subitem = t.closest('.subitem');
            if (subitem) {
                var sid = subitem.getAttribute('data-section-id');
                if (sid) { scrollToSection(sid); e.stopPropagation(); e.preventDefault(); return; }
            }
            var issueEl = t.closest('.issues-text');
            if (issueEl) {
                var isid = issueEl.getAttribute('data-section-id');
                if (isid) { scrollToSection(isid); e.stopPropagation(); e.preventDefault(); return; }
            }
        }

        if (win.__sidebarClickHandler) {
            doc.removeEventListener('click', win.__sidebarClickHandler, true);
        }
        win.__sidebarClickHandler = handleClick;
        doc.addEventListener('click', handleClick, true);

        /* ─── 5. Auto-expand Content category ─── */
        function initContent() {
            var head = doc.getElementById('cat-head-content');
            var items = doc.getElementById('cat-items-content');
            if (head && items && !head.classList.contains('expanded')) {
                head.classList.add('expanded');
                items.classList.remove('collapsed');
                items.classList.add('expanded');
            }
        }

        /* ─── 6. Master setup: run everything ─── */
        function runAll() {
            setupFixedSidebar();
            setupScrollableContent();
            initContent();
        }

        // Run with increasing delays to catch Streamlit's async rendering
        setTimeout(runAll, 300);
        setTimeout(runAll, 600);
        setTimeout(runAll, 1000);
        setTimeout(runAll, 2000);

        var attempts = 0;
        var initTimer = setInterval(function() {
            runAll();
            attempts++;
            if (attempts > 30) clearInterval(initTimer);
        }, 500);

        // Re-run on DOM changes (Streamlit re-renders)
        if (doc.body) {
            var debounce = null;
            new MutationObserver(function(mutations) {
                // Only re-run if the sidebar was recreated by Streamlit
                var needsRedo = false;
                doc.querySelectorAll('.report-sidebar').forEach(function(el) {
                    if (!el.closest('#' + WRAPPER_ID) &&
                        el.style.visibility !== 'hidden') {
                        needsRedo = true;
                    }
                });
                if (needsRedo) {
                    win.__sidebarFixedDone = false;
                    clearTimeout(debounce);
                    debounce = setTimeout(runAll, 200);
                }
            }).observe(doc.body, { childList: true, subtree: true });
        }
    })();
    </script>
    """



def _escape_html(value: Any) -> str:
    """Escape text for safe insertion into HTML snippets."""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_ats_parse_rate_html(ats_val: int) -> str:
    ats_badge_cls = "badge-ok" if ats_val >= 80 else "badge-warn"
    ats_badge_txt = "Excellent" if ats_val >= 80 else ("Good" if ats_val >= 60 else "Needs Improvement")
    ats_msg = (
        f"Great! We parsed {ats_val}% of your resume successfully."
        if ats_val >= 80
        else f"We could parse {ats_val}% of your resume. Consider improving formatting for better ATS compatibility."
    )
    ats_card_cls = "good-card" if ats_val >= 80 else ""
    return f"""
            <div class="report-main">
            <div class="detail-card section-anchor" id="ats-parse-rate">
                <div class="detail-head">
                    <h3>ATS Parse Rate</h3>
                    <span class="badge {ats_badge_cls}">{ats_badge_txt}</span>
                </div>
                <div class="section-body">
                    <p class="section-body-item text-description">A high parse rate ensures the ATS can read your resume, experience, and skills.</p>
                    <div class="progress-track dark"><div class="progress-fill dark" style="width:{ats_val}%"></div></div>
                    <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                        <span>Score</span><span>{ats_val}%</span>
                    </div>
                    <div class="issue-card {ats_card_cls}" style="margin-top:14px;">
                        <div class="issue-heading">{ats_msg}</div>
                    </div>
                </div>
            </div>
            </div>
            """


def _build_quantifying_impact_html(quant_impact: Dict[str, Any]) -> str:
    q_score = quant_impact.get("score", 0)
    q_status = quant_impact.get("status", "ok")
    q_non_quant = quant_impact.get("non_quantified_lines", [])
    q_total = quant_impact.get("total_lines", 0)
    q_count = quant_impact.get("quantified_count", 0)
    q_badge = "ok" if q_status == "ok" else "warn"
    q_label = "No issues" if q_status == "ok" else f"{q_score}%"

    quant_html = f"""
        <div class="detail-card section-anchor" id="quantifying-impact">
            <div class="detail-head">
                <h3>Quantifying Impact</h3>
                <span class="badge badge-{q_badge}">{q_label}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">Your resume should include quantifiable achievements with numbers, metrics, and measurable results.</p>
                <div class="progress-track dark"><div class="progress-fill dark" style="width:{q_score}%"></div></div>
                <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                    <span>Score</span><span>{q_score}%</span>
                </div>"""

    if q_non_quant:
        quant_html += f"""
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">Your experience section lacks quantifiable achievements</div>
                    <div class="issue-desc">{q_count} of {q_total} bullet points contain numbers. The following need quantification:</div>"""
        for line in q_non_quant:
            quant_html += f'<div class="issue-item"><span class="issue-x">&#10005;</span><span>{_escape_html(line)}</span></div>'
        quant_html += '</div>'
    elif q_status == "ok":
        quant_html += """
                <div class="issue-card good-card" style="margin-top:14px;">
                    <div class="issue-heading">Great job! Your achievements are well quantified.</div>
                </div>"""

    quant_html += '</div></div>'
    return quant_html


def _build_repetition_html(repetition: Dict[str, Any]) -> str:
    r_score = repetition.get("score", 0)
    r_status = repetition.get("status", "ok")
    r_repeated = repetition.get("repeated_words", [])
    r_badge = "ok" if r_status == "ok" else "warn"
    r_label = "No issues" if r_status == "ok" else f"{r_score}%"

    rep_html = f"""
        <div class="detail-card section-anchor" id="repetition">
            <div class="detail-head">
                <h3>Repetition</h3>
                <span class="badge badge-{r_badge}">{r_label}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">Avoid excessive repetition of words and phrases to improve readability and professionalism.</p>
                <div class="progress-track dark"><div class="progress-fill dark" style="width:{r_score}%"></div></div>
                <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                    <span>Score (higher = less repetition)</span><span>{r_score}%</span>
                </div>"""

    if r_repeated:
        rep_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">The following words are repeated frequently in your resume:</div>"""
        for rw in r_repeated:
            word = rw.get("word", "")
            count = rw.get("count", 0)
            suggestions = rw.get("suggestions", [])
            rep_html += '<div class="repeat-group">'
            rep_html += f'<span class="repeat-word-tag">{count} times: {word}</span>'
            if suggestions:
                rep_html += '<span class="repeat-label">try replacing with</span>'
                for suggestion in suggestions:
                    rep_html += f'<span class="repeat-suggestion">{suggestion}</span>'
            rep_html += '</div>'
        rep_html += '</div>'
    elif r_status == "ok":
        rep_html += """
                <div class="issue-card good-card" style="margin-top:14px;">
                    <div class="issue-heading">Good variety in language and phrasing throughout the resume.</div>
                </div>"""

    rep_html += '</div></div>'
    return rep_html


def _build_spelling_grammar_html(spelling_grammar: Dict[str, Any]) -> str:
    s_score = spelling_grammar.get("score", 0)
    s_status = spelling_grammar.get("status", "ok")
    s_issues = spelling_grammar.get("issues_list", [])
    s_badge = "ok" if s_status == "ok" else "warn"
    s_label = "No issues" if s_status == "ok" else f"{len(s_issues)} issues"

    spell_html = f"""
        <div class="detail-card section-anchor" id="spelling-grammar">
            <div class="detail-head">
                <h3>Spelling &amp; Grammar</h3>
                <span class="badge badge-{s_badge}">{s_label}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">Ensure your resume is free of spelling and grammatical errors for a professional appearance.</p>
                <div class="progress-track dark"><div class="progress-fill dark" style="width:{s_score}%"></div></div>
                <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                    <span>Score</span><span>{s_score}%</span>
                </div>"""

    if s_issues:
        spell_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">We found the following issues in your resume:</div>"""
        for issue in s_issues:
            label = issue.get("label", "Issue")
            examples = issue.get("examples", [])
            count = issue.get("count", 0)
            spell_html += f'<div class="spell-issue-row"><span class="spell-tag"><span class="spell-tag-label">{count}x</span> {label}</span></div>'
            if examples:
                for ex in examples[:2]:
                    spell_html += f'<div class="issue-item"><span class="issue-x">&#10005;</span><span style="font-family:monospace;font-size:0.85rem;">{_escape_html(ex)}</span></div>'
        spell_html += '</div>'
    elif s_status == "ok":
        spell_html += """
                <div class="issue-card good-card" style="margin-top:14px;">
                    <div class="issue-heading">No significant spelling or grammar errors detected.</div>
                </div>"""

    spell_html += '</div></div>'
    return spell_html


def _build_essential_sections_html(sections_details: Dict[str, Any]) -> str:
    essential_sections_map = [
        ("contact", "Contact", sections_details.get("has_contact", False)),
        ("experience", "Experience", sections_details.get("has_experience", False)),
        ("education", "Education", sections_details.get("has_education", False)),
        ("skills", "Skills", sections_details.get("has_skills", False)),
        ("summary", "Summary/Objective", sections_details.get("has_summary", False)),
    ]
    es_missing = [s for s in essential_sections_map if not s[2]]
    es_badge = "ok" if not es_missing else "warn"
    es_label = "All found" if not es_missing else f"{len(es_missing)} missing"

    es_html = f"""
        <div class="detail-card section-anchor" id="essential-sections">
            <div class="detail-head">
                <h3>Essential Sections</h3>
                <span class="badge badge-{es_badge}">{es_label}</span>
            </div>
            <div class="section-body">"""

    if es_missing:
        es_html += """
                <div class="issue-card" style="margin-top:10px;">
                    <div class="issue-heading">We've found the following <strong>essential sections</strong> in your resume. However, some are missing:</div>"""
    else:
        es_html += """
                <div class="issue-card good-card" style="margin-top:10px;">
                    <div class="issue-heading">All essential sections are present in your resume:</div>"""

    for _key, label, present in essential_sections_map:
        icon_cls = "found" if present else "missing"
        icon_char = "&#10003;" if present else "&#10005;"
        es_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon {icon_cls}">{icon_char}</span>
                        <span class="contact-label">{label}</span>
                    </div>"""

    es_html += "</div></div></div>"
    return es_html


def _build_contact_information_html(contact_found: List[Dict[str, Any]], contact_missing: List[Dict[str, Any]]) -> str:
    ci_badge = "ok" if not contact_missing else "warn"
    ci_label = "All found" if not contact_missing else f"{len(contact_missing)} missing"

    contact_html = f"""
        <div class="detail-card section-anchor" id="contact-information">
            <div class="detail-head">
                <h3>Contact Information</h3>
                <span class="badge badge-{ci_badge}">{ci_label}</span>
            </div>
            <div class="section-body">"""

    if contact_found:
        contact_html += """
                <div class="issue-card good-card" style="margin-top:10px;">
                    <div class="issue-heading">We've found the following contact information in your resume:</div>"""
        for item in contact_found:
            label = item.get("label", "")
            value = item.get("value", "")
            contact_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon found">&#10003;</span>
                        <span class="contact-label">{label}:</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value">{_escape_html(value)}</span>
                    </div>"""
        contact_html += "</div>"

    if contact_missing:
        contact_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">Although, you are missing essential contact information:</div>"""
        for item in contact_missing:
            label = item.get("label", "")
            message = item.get("message", "")
            contact_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon missing">&#10005;</span>
                        <span class="contact-label">{label}</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{_escape_html(message)}</span>
                    </div>"""
        contact_html += "</div>"
    elif not contact_found:
        contact_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">No contact information could be extracted from your resume.</div>
                </div>"""

    contact_html += "</div></div>"
    return contact_html


def _build_file_format_size_html(file_format_info: Dict[str, Any]) -> str:
    ff_is_pdf = file_format_info.get("is_pdf", True)
    ff_size_ok = file_format_info.get("size_ok", True)
    ff_name = file_format_info.get("file_name", "")
    ff_size_kb = file_format_info.get("file_size_kb", 0)
    ff_size_mb = file_format_info.get("file_size_mb", 0)
    ff_all_good = ff_is_pdf and ff_size_ok
    ff_badge = "ok" if ff_all_good else "warn"
    ff_badge_txt = "No issues" if ff_all_good else "Issues found"
    ff_ext = ff_name.rsplit(".", 1)[-1].upper() if "." in ff_name else "PDF"

    ff_html = f"""
        <div class="detail-card section-anchor" id="file-format-size">
            <div class="detail-head">
                <h3>File Format &amp; Size</h3>
                <span class="badge badge-{ff_badge}">{ff_badge_txt}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">
                    When you're uploading your resume on platforms like Indeed, you're likely to meet a file size limit.
                    Ideally, your resume should be less than 2MB in size. Your file type also plays an important role
                    in ATS screening. PDF files are preferred as the text can be easily read by the applicant tracking system.
                </p>"""

    if ff_all_good:
        size_str = f"{ff_size_kb:.0f}KB" if ff_size_kb < 1024 else f"{ff_size_mb:.1f}MB"
        ff_html += f"""
                <div class="issue-card good-card" style="margin-top:14px;text-align:center;">
                    <div class="issue-heading" style="font-size:1.1rem;">Good job!</div>
                    <div class="text-description" style="margin-top:6px;">
                        Your resume file is <strong>{size_str}</strong> and your file type is <strong>{ff_ext}</strong>.
                    </div>
                </div>"""
    else:
        ff_issues_html = ""
        if not ff_is_pdf:
            ff_issues_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon missing">&#10005;</span>
                        <span class="contact-value contact-msg">Your file type is <strong>{ff_ext}</strong>. PDF is the preferred format for ATS systems.</span>
                    </div>"""
        if not ff_size_ok:
            ff_issues_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon missing">&#10005;</span>
                        <span class="contact-value contact-msg">Your file is <strong>{ff_size_mb:.1f}MB</strong>. It should be under 2MB for most platforms.</span>
                    </div>"""
        ff_html += f"""
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">File format or size issues detected:</div>
                    {ff_issues_html}
                </div>"""

    ff_html += "</div></div>"
    return ff_html


def _build_email_address_html(email_check_info: Dict[str, Any]) -> str:
    em_found = email_check_info.get("found", False)
    em_email = email_check_info.get("email", "")
    em_prof = email_check_info.get("is_professional", True)
    em_badge = "ok" if (em_found and em_prof) else "warn"
    em_badge_txt = "No issues" if (em_found and em_prof) else ("Unprofessional" if em_found else "Not found")

    em_html = f"""
        <div class="detail-card section-anchor" id="email-address">
            <div class="detail-head">
                <h3>Email Address</h3>
                <span class="badge badge-{em_badge}">{em_badge_txt}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">
                    Emails are important in today's world. It's one of the go-to ways for recruiters to get in touch with you,
                    especially if you're applying for a job that's remote and in another country.
                </p>"""

    safe_email = _escape_html(em_email)
    if em_found and em_prof:
        em_html += f"""
                <div class="issue-card good-card" style="margin-top:14px;text-align:center;">
                    <div class="issue-heading" style="font-size:1.1rem;">Good job!</div>
                    <div class="text-description" style="margin-top:6px;">Your email address seems professional.</div>
                    <div style="margin-top:12px;padding:8px 20px;border-radius:8px;background:rgba(255,255,255,0.08);display:inline-block;font-size:0.95rem;color:var(--text-primary);">
                        {safe_email}
                    </div>
                </div>"""
    elif em_found:
        em_html += f"""
                <div class="issue-card" style="margin-top:14px;text-align:center;">
                    <div class="issue-heading">Your email address may not appear professional:</div>
                    <div style="margin-top:12px;padding:8px 20px;border-radius:8px;background:rgba(255,255,255,0.08);display:inline-block;font-size:0.95rem;color:var(--text-primary);">
                        {safe_email}
                    </div>
                    <div class="text-description" style="margin-top:8px;">Consider using a professional email format (e.g. firstname.lastname@domain.com).</div>
                </div>"""
    else:
        em_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">No email address was found in your resume.</div>
                    <div class="text-description" style="margin-top:6px;">Include a professional email address so recruiters can contact you.</div>
                </div>"""

    em_html += "</div></div>"
    return em_html


def _build_header_links_html(header_links_info: Dict[str, Any]) -> str:
    hl_has = header_links_info.get("has_links", False)
    hl_links = header_links_info.get("links", [])
    hl_full = header_links_info.get("has_full_url", False)
    hl_badge = "ok" if hl_has else "warn"
    hl_badge_txt = "No issues" if hl_has else "Not found"

    hl_html = f"""
        <div class="detail-card section-anchor" id="header-links">
            <div class="detail-head">
                <h3>Header Links</h3>
                <span class="badge badge-{hl_badge}">{hl_badge_txt}</span>
            </div>
            <div class="section-body">"""

    if hl_has and hl_full:
        hl_html += """
                <div class="issue-card good-card" style="margin-top:10px;text-align:center;">
                    <div class="issue-heading" style="font-size:1.1rem;">Full link detected</div>
                    <div class="text-description" style="margin-top:6px;">
                        Your header includes a complete URL, ensuring proper recognition by ATS systems.
                    </div>
                </div>"""
        if hl_links:
            hl_html += '<div style="margin-top:10px;">'
            for link in hl_links:
                hl_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon found">&#10003;</span>
                        <span class="contact-value">{_escape_html(link)}</span>
                    </div>"""
            hl_html += '</div>'
    elif hl_has:
        hl_html += """
                <div class="issue-card" style="margin-top:10px;text-align:center;">
                    <div class="issue-heading">Partial link detected</div>
                    <div class="text-description" style="margin-top:6px;">
                        We found link references in your header, but consider using complete URLs (e.g. https://linkedin.com/in/yourname)
                        for better ATS recognition.
                    </div>
                </div>"""
    else:
        hl_html += """
                <div class="issue-card" style="margin-top:10px;">
                    <div class="issue-heading">No links found in your resume header</div>
                    <div class="text-description" style="margin-top:6px;">
                        Include links to your LinkedIn profile, GitHub, or portfolio in your resume header.
                        ATS systems often look for these to verify your online presence.
                    </div>
                </div>"""

    hl_html += "</div></div>"
    return hl_html


def _build_list_card(
    title: str,
    items: List[str],
    section_id: str,
    badge_type: str,
    badge_label: str,
    icon: str,
    empty_msg: str,
) -> str:
    """Build a uniform detail-card HTML string for list-based sections."""
    html = f"""
            <div class="detail-card section-anchor" id="{section_id}">
                <div class="detail-head">
                    <h3>{title}</h3>
                    <span class="badge badge-{badge_type}">{badge_label}</span>
                </div>
                <div class="section-body">"""
    if items:
        html += (
            '<div class="issue-card good-card" style="margin-top:10px;">'
            if badge_type == "ok"
            else '<div class="issue-card" style="margin-top:10px;">'
        )
        for item in items:
            safe_item = _markdown_inline_to_html(item)
            html += f"""
                    <div class="contact-row" style="align-items:flex-start;">
                        <span class="contact-icon {'found' if badge_type == 'ok' else 'missing'}">{icon}</span>
                        <span class="contact-value" style="line-height:1.5;">{safe_item}</span>
                    </div>"""
        html += "</div>"
    else:
        html += f"""
                <div class="issue-card good-card" style="margin-top:10px;text-align:center;">
                    <div class="issue-heading">{empty_msg}</div>
                </div>"""
    html += "</div></div>"
    return html


def _render_download_buttons(name: str, analysis: Dict[str, Any]) -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Download Reports", unsafe_allow_html=False)
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.download_button(
            "ðŸ“„ Download Markdown Report",
            data=build_report_md(name, analysis),
            file_name=f"{name}-analysis.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_md_main",
        )
    with col2:
        st.download_button(
            "ðŸ’¾ Download JSON Export",
            data=json.dumps(analysis, indent=2),
            file_name=f"{name}-analysis.json",
            mime="application/json",
            use_container_width=True,
            key="download_json_main",
        )


def render_report_page(analysis: Dict[str, Any], name: str = "CV") -> None:
    """Render the two-column report view inspired by the HTML mock."""
    score = analysis.get("match_score", 0)
    subs = analysis.get("subscores", {}) or {}
    issues = issue_count(analysis)

    # Extract content metrics
    content_metrics = analysis.get("content_metrics", {}) or {}
    ats_parse_rate = content_metrics.get("ats_parse_rate", 0)
    quant_impact = content_metrics.get("quantifying_impact", {}) or {}
    repetition = content_metrics.get("repetition", {}) or {}
    spelling_grammar = content_metrics.get("spelling_grammar", {}) or {}

    # Calculate Content category score as average of content metrics
    content_items = [
        ats_parse_rate,
        quant_impact.get("score", 0),
        repetition.get("score", 0),
        spelling_grammar.get("score", 0),
    ]
    content_score = int(sum(content_items) / len(content_items)) if content_items else subs.get("ats_readiness", score)

    # Build Content category items: (label, status, score)
    content_items_list = [
        ("ATS Parse Rate", "ok" if ats_parse_rate >= 80 else "warn" if ats_parse_rate >= 60 else "error", ats_parse_rate),
        ("Quantifying Impact", quant_impact.get("status", "ok"), quant_impact.get("score", 0)),
        ("Repetition", repetition.get("status", "ok"), repetition.get("score", 0)),
        ("Spelling & Grammar", spelling_grammar.get("status", "ok"), spelling_grammar.get("score", 0)),
    ]

    # Extract other category metrics
    sections_metrics = analysis.get("sections_metrics", {}) or {}
    sections_score = sections_metrics.get("score", subs.get("experience_alignment", score)) or 0
    sections_details = sections_metrics.get("details", {}) or {}

    # Extract contact info
    contact_info = analysis.get("contact_info", {}) or {}
    contact_found = contact_info.get("found", [])
    contact_missing = contact_info.get("missing", [])

    # Build Sections category items
    sections_items_list = []
    missing_sections = sections_details.get("missing_sections", [])
    if missing_sections:
        sections_items_list.append(("Essential Sections", "error", len(missing_sections)))
    else:
        sections_items_list.append(("Essential Sections", "ok", None))

    if contact_missing:
        sections_items_list.append(("Contact Information", "error", len(contact_missing)))
    else:
        sections_items_list.append(("Contact Information", "ok", None))

    ats_essentials_metrics = analysis.get("ats_essentials_metrics", {}) or {}
    ats_essentials_score = ats_essentials_metrics.get("score", subs.get("ats_readiness", score)) or 0
    ats_essentials_details = ats_essentials_metrics.get("details", {}) or {}

    # Extract ATS sub-section details
    file_format_info = ats_essentials_details.get("file_format", {}) or {}
    email_check_info = ats_essentials_details.get("email_check", {}) or {}
    header_links_info = ats_essentials_details.get("header_links", {}) or {}

    # Build ATS Essentials category items
    ats_items_list = []
    ats_issues = ats_essentials_details.get("issues", [])

    ff_ok = file_format_info.get("is_pdf", True) and file_format_info.get("size_ok", True)
    ats_items_list.append(("File Format & Size", "ok" if ff_ok else "warn", None if ff_ok else 1))

    if ats_issues:
        ats_items_list.append(("Design", "warn", len(ats_issues)))

    email_found = email_check_info.get("found", False)
    email_prof = email_check_info.get("is_professional", True)
    if email_found and email_prof:
        ats_items_list.append(("Email Address", "ok", None))
    elif email_found:
        ats_items_list.append(("Email Address", "warn", 1))
    else:
        ats_items_list.append(("Email Address", "error", 1))

    has_links = header_links_info.get("has_links", False)
    ats_items_list.append(("Hyperlink in Header", "ok" if has_links else "warn", None if has_links else 1))

    # Build Insights category items
    strengths_list = analysis.get("strengths", [])
    missing_skills_list = analysis.get("missing_skills", [])
    missing_keywords_list = analysis.get("missing_keywords", [])
    suggestions_list = analysis.get("suggestions", [])

    insights_items_list = [
        ("Strengths", "ok" if strengths_list else "warn", len(strengths_list) if strengths_list else None),
        ("Missing Skills", "warn" if missing_skills_list else "ok", len(missing_skills_list) if missing_skills_list else None),
        ("Missing Keywords", "warn" if missing_keywords_list else "ok", len(missing_keywords_list) if missing_keywords_list else None),
        ("Suggestions", "ok" if suggestions_list else "warn", len(suggestions_list) if suggestions_list else None),
    ]

    total_insights = len(strengths_list) + len(missing_skills_list) + len(missing_keywords_list)
    insights_score = int((len(strengths_list) / total_insights) * 100) if total_insights else 80

    categories = [
        ("Content", content_score, content_items_list),
        ("Sections", sections_score, sections_items_list),
        ("ATS Essentials", ats_essentials_score, ats_items_list),
        ("Insights", insights_score, insights_items_list),
    ]

    # Two-column layout: scoring sidebar + main content
    sidebar, main = st.columns([1, 1.6], gap="large")

    with sidebar:
        sidebar_html = _build_sidebar_html(score, issues, categories)
        st.markdown(sidebar_html, unsafe_allow_html=True)
        components.html(_build_sidebar_js(), height=0)

    with main:
        st.markdown(_build_ats_parse_rate_html(content_metrics.get("ats_parse_rate", 0)), unsafe_allow_html=True)
        st.markdown(_build_quantifying_impact_html(quant_impact), unsafe_allow_html=True)
        st.markdown(_build_repetition_html(repetition), unsafe_allow_html=True)
        st.markdown(_build_spelling_grammar_html(spelling_grammar), unsafe_allow_html=True)
        st.markdown(_build_essential_sections_html(sections_details), unsafe_allow_html=True)
        st.markdown(_build_contact_information_html(contact_found, contact_missing), unsafe_allow_html=True)
        st.markdown(_build_file_format_size_html(file_format_info), unsafe_allow_html=True)
        st.markdown(_build_email_address_html(email_check_info), unsafe_allow_html=True)
        st.markdown(_build_header_links_html(header_links_info), unsafe_allow_html=True)

        strengths_html = _build_list_card(
            "Strengths",
            strengths_list,
            "strengths",
            "ok",
            f"{len(strengths_list)} found" if strengths_list else "None",
            "&#10003;",
            "No specific strengths identified yet.",
        )
        st.markdown(strengths_html, unsafe_allow_html=True)

        missing_skills_html = _build_list_card(
            "Missing Skills",
            missing_skills_list,
            "missing-skills",
            "warn" if missing_skills_list else "ok",
            f"{len(missing_skills_list)} missing" if missing_skills_list else "All covered",
            "&#10005;",
            "No missing skills detected — great job!",
        )
        st.markdown(missing_skills_html, unsafe_allow_html=True)

        missing_kw_html = _build_list_card(
            "Missing Keywords (ATS)",
            missing_keywords_list,
            "missing-keywords",
            "warn" if missing_keywords_list else "ok",
            f"{len(missing_keywords_list)} missing" if missing_keywords_list else "All covered",
            "&#10005;",
            "No missing ATS keywords detected — your resume is well-optimized!",
        )
        st.markdown(missing_kw_html, unsafe_allow_html=True)

        suggestions_html = _build_list_card(
            "Suggestions",
            suggestions_list,
            "suggestions",
            "ok",
            f"{len(suggestions_list)} tips" if suggestions_list else "None",
            "💡",
            "No additional suggestions at this time.",
        )
        st.markdown(suggestions_html, unsafe_allow_html=True)

        _render_download_buttons(name, analysis)
        st.markdown("</div>", unsafe_allow_html=True)
