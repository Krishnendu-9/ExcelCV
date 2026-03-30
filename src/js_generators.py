"""
JavaScript Generation Helpers

This module contains functions to generate JavaScript code for dynamic UI behavior.
All JavaScript is generated programmatically to maintain consistency.
"""

from src.ui_constants import (
    JS_TIMEOUT_DELAYS,
    JS_INTERVAL_MS,
    THEME_BUTTON_SELECTORS,
    WARM_HOVER_BORDER,
    WARM_HOVER_GLOW,
    get_js_colors,
)


def generate_theme_force_js(bg_color: str, text_color: str) -> str:
    """Generate JavaScript to force theme application."""
    theme_class = 'theme-light' if bg_color == '#ffffff' else 'theme-dark'
    return f"""
            (function() {{
                if (window.themeInterval) {{
                    clearInterval(window.themeInterval);
                }}
                
                const bgColor = '{bg_color}';
                const themeClass = '{theme_class}';
                
                function forceTheme() {{
                    try {{
                        if (document.body) {{
                            document.body.className = document.body.className.replace(/theme-\\w+/g, '').trim() + ' ' + themeClass;
                            document.body.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                        }}
                        if (document.documentElement) {{
                            document.documentElement.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                        }}
                        
                        const stApp = document.querySelector('.stApp');
                        if (stApp) {{
                            stApp.className = stApp.className.replace(/theme-\\w+/g, '').trim() + ' ' + themeClass;
                            stApp.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                            
                            const allChildren = stApp.querySelectorAll('*');
                            allChildren.forEach(child => {{
                                if (child && child.style && !child.classList.contains('hero-shell') && !child.classList.contains('preview-card')) {{
                                    if (child === stApp.firstElementChild || child.parentElement === stApp) {{
                                        child.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                                    }}
                                }}
                            }});
                        }}
                        
                        const viewContainer = document.querySelector('[data-testid="stAppViewContainer"]');
                        if (viewContainer) {{
                            viewContainer.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                            const allViewChildren = viewContainer.querySelectorAll('*');
                            allViewChildren.forEach(child => {{
                                if (child && child.style && child.parentElement === viewContainer) {{
                                    child.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                                }}
                            }});
                        }}
                        
                        document.querySelectorAll('.main, .block-container').forEach(el => {{
                            if (el && el.style) {{
                                el.style.cssText += 'background-color: transparent !important;';
                            }}
                        }});
                        
                        const view = document.querySelector('[data-testid="stAppViewContainer"]');
                        if (view) {{
                            view.style.paddingTop = '0'; view.style.paddingBottom = '0';
                            view.style.marginTop = '0'; view.style.marginBottom = '0';
                            const section = view.querySelector('section');
                            if (section) {{
                                section.style.paddingTop = '0'; section.style.paddingBottom = '0';
                                section.style.marginTop = '0'; section.style.marginBottom = '0';
                                [].forEach.call(section.children, div => {{
                                    div.style.paddingTop = '0'; div.style.paddingBottom = '0';
                                }});
                            }}
                        }}
                        document.querySelectorAll('.main, .block-container').forEach(el => {{
                            if (el && el.style) {{
                                el.style.paddingTop = '0'; el.style.paddingBottom = '0';
                                el.style.marginTop = '0'; el.style.marginBottom = '0';
                            }}
                        }});
                    }} catch(e) {{
                        console.error('Theme error:', e);
                    }}
                }}
                
                forceTheme();
                {chr(10).join([f'setTimeout(forceTheme, {delay});' for delay in JS_TIMEOUT_DELAYS])}
                window.themeInterval = setInterval(forceTheme, 10);
                
                if (document.body) {{
                    new MutationObserver(() => {{
                        setTimeout(forceTheme, 5);
                    }}).observe(document.body, {{
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeFilter: ['style', 'class']
                    }});
                }}
                
                ['DOMContentLoaded', 'load'].forEach(event => {{
                    window.addEventListener(event, forceTheme);
                }});
            }})();
    """


def generate_hover_effects_js(is_light: bool, bg_color: str) -> str:
    """Generate JavaScript for hover effects (textarea, dropzone, buttons)."""
    btn_bg, btn_text, btn_border = get_js_colors(is_light)
    dropzone_bg = '#ffffff' if is_light else '#1f2937'
    
    theme_selectors_str = ', '.join([f"'{s}'" for s in THEME_BUTTON_SELECTORS])
    
    return f"""
            (function() {{
                const bgColor = '{bg_color}';
                const btnBg = '{btn_bg}';
                const btnText = '{btn_text}';
                const btnBorder = '{btn_border}';
                const dropzoneBg = '{dropzone_bg}';
                const warmHoverBorder = '{WARM_HOVER_BORDER}';
                const warmGlow = '{WARM_HOVER_GLOW}';
                
                // Theme button hover effect
                function fixThemeButtonGlow() {{
                    const themeBtnSelectors = [{theme_selectors_str}];
                    
                    themeBtnSelectors.forEach(selector => {{
                        document.querySelectorAll(selector).forEach(themeBtn => {{
                            if (themeBtn) {{
                                if (!themeBtn.matches(':hover')) {{
                                    themeBtn.style.setProperty('background-color', btnBg, 'important');
                                    themeBtn.style.setProperty('background', btnBg, 'important');
                                    themeBtn.style.setProperty('background-image', 'none', 'important');
                                }}
                                
                                if (!themeBtn.hasAttribute('data-theme-glow-applied')) {{
                                    themeBtn.setAttribute('data-theme-glow-applied', 'true');
                                    
                                    themeBtn.style.setProperty('background-color', btnBg, 'important');
                                    themeBtn.style.setProperty('background', btnBg, 'important');
                                    themeBtn.style.setProperty('color', btnText, 'important');
                                    themeBtn.style.setProperty('border-color', btnBorder, 'important');
                                    
                                    const btnDivs = themeBtn.querySelectorAll('div, span, p');
                                    btnDivs.forEach(div => {{
                                        div.style.setProperty('background-color', 'transparent', 'important');
                                        div.style.setProperty('background', 'transparent', 'important');
                                        div.style.setProperty('background-image', 'none', 'important');
                                        div.style.setProperty('color', btnText, 'important');
                                    }});
                                    
                                    themeBtn.addEventListener('mouseenter', function(e) {{
                                        e.stopPropagation();
                                        this.style.setProperty('box-shadow', warmGlow, 'important');
                                        this.style.setProperty('border-color', warmHoverBorder, 'important');
                                        this.style.setProperty('background-color', btnBg, 'important');
                                        this.style.setProperty('background', btnBg, 'important');
                                        this.style.setProperty('background-image', 'none', 'important');
                                        const allNested = this.querySelectorAll('*');
                                        allNested.forEach(el => {{
                                            if (el && el.tagName !== 'SVG') {{
                                                el.style.setProperty('background-color', 'transparent', 'important');
                                                el.style.setProperty('background', 'transparent', 'important');
                                                el.style.setProperty('background-image', 'none', 'important');
                                            }}
                                        }});
                                    }}, true);
                                    
                                    themeBtn.addEventListener('mouseover', function(e) {{
                                        e.stopPropagation();
                                        this.style.setProperty('box-shadow', warmGlow, 'important');
                                        this.style.setProperty('border-color', warmHoverBorder, 'important');
                                        this.style.setProperty('background-color', btnBg, 'important');
                                        this.style.setProperty('background', btnBg, 'important');
                                        this.style.setProperty('background-image', 'none', 'important');
                                    }}, true);
                                    
                                    themeBtn.addEventListener('mouseleave', function(e) {{
                                        e.stopPropagation();
                                        this.style.removeProperty('box-shadow');
                                        this.style.setProperty('border-color', btnBorder, 'important');
                                    }}, true);
                                    
                                    themeBtn.addEventListener('mouseout', function(e) {{
                                        e.stopPropagation();
                                        this.style.removeProperty('box-shadow');
                                        this.style.setProperty('border-color', btnBorder, 'important');
                                    }}, true);
                                }}
                            }}
                        }});
                    }});
                }}
                
                fixThemeButtonGlow();
                {chr(10).join([f'setTimeout(fixThemeButtonGlow, {delay});' for delay in JS_TIMEOUT_DELAYS])}
                setInterval(fixThemeButtonGlow, {JS_INTERVAL_MS});
                
                if (document.body) {{
                    new MutationObserver(() => {{
                        setTimeout(fixThemeButtonGlow, 5);
                    }}).observe(document.body, {{
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeFilter: ['key', 'class', 'data-testid']
                    }});
                }}
                
                ['DOMContentLoaded', 'load', 'pageshow'].forEach(event => {{
                    window.addEventListener(event, fixThemeButtonGlow);
                }});
                
                // Textarea hover effect
                document.querySelectorAll('.stTextArea textarea').forEach(textarea => {{
                    if (textarea) {{
                        textarea.addEventListener('mouseenter', function() {{
                            this.style.cssText += 'box-shadow: ' + warmGlow + ' !important; border-color: ' + warmHoverBorder + ' !important; background: var(--bg-card) !important; background-color: var(--bg-card) !important;';
                        }});
                        textarea.addEventListener('mouseleave', function() {{
                            if (!this.matches(':focus')) {{
                                this.style.cssText = this.style.cssText.replace(/box-shadow:\\s*[^;]+/g, '').replace(/border-color:\\s*[^;]+/g, '');
                            }}
                        }});
                    }}
                }});
                
                // Dropzone hover effect
                function fixDropzoneGlow() {{
                    document.querySelectorAll('.stFileUploader [data-testid="stFileUploaderDropzone"]').forEach(dropzone => {{
                        if (dropzone) {{
                            if (!dropzone.matches(':hover')) {{
                                dropzone.style.setProperty('box-shadow', 'none', 'important');
                            }}
                            dropzone.style.setProperty('background', dropzoneBg, 'important');
                            dropzone.style.setProperty('background-color', dropzoneBg, 'important');
                            
                            if (!dropzone.hasAttribute('data-glow-applied')) {{
                                dropzone.setAttribute('data-glow-applied', 'true');
                                dropzone.style.setProperty('box-shadow', 'none', 'important');
                                
                                dropzone.addEventListener('mouseenter', function() {{
                                    this.style.setProperty('box-shadow', warmGlow, 'important');
                                    this.style.setProperty('border-color', warmHoverBorder, 'important');
                                    this.style.setProperty('background', dropzoneBg, 'important');
                                    this.style.setProperty('background-color', dropzoneBg, 'important');
                                }});
                                
                                dropzone.addEventListener('mouseleave', function() {{
                                    this.style.setProperty('box-shadow', 'none', 'important');
                                    this.style.removeProperty('border-color');
                                }});
                            }}
                        }}
                    }});
                }}
                
                fixDropzoneGlow();
                setInterval(fixDropzoneGlow, {JS_INTERVAL_MS});
                
                if (document.body) {{
                    new MutationObserver(() => {{
                        setTimeout(fixDropzoneGlow, 5);
                    }}).observe(document.body, {{
                        childList: true,
                        subtree: true
                    }});
                }}
                
                // Upload button hover effect
                function fixUploadButtonGlow() {{
                    document.querySelectorAll('button').forEach(btn => {{
                        if (btn && (btn.textContent && btn.textContent.includes('Upload another resume'))) {{
                            if (!btn.matches(':hover')) {{
                                btn.style.setProperty('background', btnBg, 'important');
                                btn.style.setProperty('background-color', btnBg, 'important');
                                btn.style.setProperty('background-image', 'none', 'important');
                            }}
                            
                            if (!btn.hasAttribute('data-upload-glow-applied')) {{
                                btn.setAttribute('data-upload-glow-applied', 'true');
                                
                                btn.addEventListener('mouseenter', function() {{
                                    this.style.setProperty('box-shadow', warmGlow, 'important');
                                    this.style.setProperty('border-color', warmHoverBorder, 'important');
                                    this.style.setProperty('background', btnBg, 'important');
                                    this.style.setProperty('background-color', btnBg, 'important');
                                    this.style.setProperty('background-image', 'none', 'important');
                                    const allNested = this.querySelectorAll('*');
                                    allNested.forEach(el => {{
                                        if (el && el.tagName !== 'SVG') {{
                                            el.style.setProperty('background-color', 'transparent', 'important');
                                            el.style.setProperty('background', 'transparent', 'important');
                                            el.style.setProperty('background-image', 'none', 'important');
                                        }}
                                    }});
                                }});
                                
                                btn.addEventListener('mouseleave', function() {{
                                    this.style.setProperty('box-shadow', 'none', 'important');
                                    this.style.removeProperty('border-color');
                                }});
                            }}
                        }}
                    }});
                }}
                
                fixUploadButtonGlow();
                setInterval(fixUploadButtonGlow, {JS_INTERVAL_MS});
            }})();
    """


def generate_scroll_to_section_js() -> str:
    """Generate JavaScript for smooth scrolling to sections."""
    return """
            function scrollToSection(sectionId) {
                const element = document.getElementById(sectionId);
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    element.style.transition = 'background-color 0.3s ease';
                    const originalBg = element.style.backgroundColor;
                    element.style.backgroundColor = 'rgba(16,185,129,0.15)';
                    setTimeout(() => {
                        element.style.backgroundColor = originalBg;
                    }, 1000);
                }
            }
    """
