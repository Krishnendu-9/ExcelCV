            // SIMPLE THEME APPLICATION - WHITE FOR LIGHT, BLACK FOR DARK
            (function() {{
                // Clean up any existing intervals
                if (window.themeInterval) {{
                    clearInterval(window.themeInterval);
                }}
                
                const bgColor = '{bg_color}';
                const themeClass = bgColor === '#ffffff' ? 'theme-light' : 'theme-dark';
                
                function forceTheme() {{
                    try {{
                        const isThemeToggleButton = (btn) => {{
                            if (!btn || !btn.closest) return false;
                            const key = (btn.getAttribute('key') || '').toLowerCase();
                            if (key === 'theme_toggle' || key === 'theme_toggle_header') return true;
                            return !!btn.closest('.st-key-theme_toggle_header, .st-key-theme_toggle, [class*="theme_toggle"]');
                        }};

                        const resetThemeToggleVisuals = () => {{
                            const targets = document.querySelectorAll(
                                '.st-key-theme_toggle_header button, ' +
                                '.st-key-theme_toggle_header [data-baseweb="button"], ' +
                                '[class*="theme_toggle_header"] button, ' +
                                '[class*="theme_toggle"] button'
                            );
                            targets.forEach(el => {{
                                if (!el || !el.style) return;
                                [
                                    'background',
                                    'background-color',
                                    'background-image',
                                    'border',
                                    'border-color',
                                    'border-top-color',
                                    'border-right-color',
                                    'border-bottom-color',
                                    'border-left-color',
                                    'box-shadow',
                                    'outline',
                                    'transition',
                                    'filter',
                                    '-webkit-filter',
                                    'color',
                                ]
                                    .forEach(prop => el.style.removeProperty(prop));
                                el.querySelectorAll('*').forEach(child => {{
                                    if (!child || !child.style) return;
                                    [
                                        'background',
                                        'background-color',
                                        'background-image',
                                        'border',
                                        'border-color',
                                        'border-top-color',
                                        'border-right-color',
                                        'border-bottom-color',
                                        'border-left-color',
                                        'box-shadow',
                                        'outline',
                                        'transition',
                                        'filter',
                                        '-webkit-filter',
                                        'color',
                                    ]
                                        .forEach(prop => child.style.removeProperty(prop));
                                }});
                            }});
                        }};

                        // Apply theme class to body and html
                        if (document.body) {{
                            document.body.className = document.body.className.replace(/theme-\\w+/g, '').trim() + ' ' + themeClass;
                            document.body.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                        }}
                        if (document.documentElement) {{
                            document.documentElement.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                        }}
                        
                        // Force .stApp and ALL its children - WHITE or BLACK
                        const stApp = document.querySelector('.stApp');
                        if (stApp) {{
                            stApp.className = stApp.className.replace(/theme-\\w+/g, '').trim() + ' ' + themeClass;
                            stApp.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                            
                            // Force ALL children recursively
                            const allChildren = stApp.querySelectorAll('*');
                            allChildren.forEach(child => {{
                                if (child && child.style && !child.classList.contains('hero-shell') && !child.classList.contains('preview-card')) {{
                                    // Only override container backgrounds, not content cards
                                    if (child === stApp.firstElementChild || child.parentElement === stApp) {{
                                        child.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                                    }}
                                }}
                            }});
                        }}
                        
                        // Force Streamlit view container and ALL children
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
                        
                        // Force main and block-container to be transparent
                        document.querySelectorAll('.main, .block-container').forEach(el => {{
                            if (el && el.style) {{
                                el.style.cssText += 'background-color: transparent !important;';
                            }}
                        }});
                        // Remove top and bottom blank: force zero padding/margin on all main containers
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
                        
                        // Fix selectbox (Mode dropdown) - force theme colors
                        document.querySelectorAll('div[data-baseweb="select"]').forEach(select => {{
                            if (select) {{
                                const selectDiv = select.querySelector('div');
                                if (selectDiv) {{
                                    selectDiv.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#ffffff' : '#1f2937') + ' !important; color: ' + (bgColor === '#ffffff' ? '#111827' : '#e5e7eb') + ' !important; border-color: ' + (bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)') + ' !important;';
                                }}
                                const input = select.querySelector('input');
                                if (input) {{
                                    input.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#ffffff' : '#1f2937') + ' !important; color: ' + (bgColor === '#ffffff' ? '#111827' : '#e5e7eb') + ' !important;';
                                }}
                            }}
                        }});
                        
                        // Fix text area labels - Professional styling with larger size
                        document.querySelectorAll('.stTextArea label, .stTextArea > label, [data-testid="stTextArea"] label').forEach(label => {{
                            if (label) {{
                                const labelColor = bgColor === '#ffffff' ? '#1f2937' : '#f9fafb';
                                label.style.cssText += 'color: ' + labelColor + ' !important; font-weight: 700 !important; font-size: 1.28rem !important; margin-bottom: 0 !important; margin-top: 0 !important; display: block !important; letter-spacing: 0.01em !important; line-height: 1.2 !important; border-bottom: none !important; padding-bottom: 0 !important;';
                                // Also style any nested elements
                                const nestedElements = label.querySelectorAll('p, span, *');
                                nestedElements.forEach(el => {{
                                    if (el && el.tagName !== 'SVG' && el.tagName !== 'BUTTON') {{
                                        el.style.cssText += 'color: ' + labelColor + ' !important; font-size: inherit !important; font-weight: inherit !important;';
                                    }}
                                }});
                            }}
                        }});
                        
                        // Fix file uploader labels - Professional styling matching Job description
                        document.querySelectorAll('.stFileUploader label, .stFileUploader > label, [data-testid="stFileUploader"] label').forEach(label => {{
                            if (label) {{
                                const labelColor = bgColor === '#ffffff' ? '#1f2937' : '#f9fafb';
                                label.style.cssText += 'color: ' + labelColor + ' !important; font-weight: 700 !important; font-size: 1.28rem !important; margin-bottom: 0 !important; margin-top: 0 !important; display: block !important; letter-spacing: 0.01em !important; line-height: 1.2 !important; border-bottom: none !important; padding-bottom: 0 !important;';
                                // Also style any nested elements
                                const nestedElements = label.querySelectorAll('p, span, *');
                                nestedElements.forEach(el => {{
                                    if (el && el.tagName !== 'SVG' && el.tagName !== 'BUTTON') {{
                                        el.style.cssText += 'color: ' + labelColor + ' !important; font-size: inherit !important; font-weight: inherit !important;';
                                    }}
                                }});
                            }}
                        }});
                        
                        // Fix file uploader - force theme colors
                        document.querySelectorAll('.stFileUploader').forEach(uploader => {{
                            if (uploader) {{
                                uploader.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#f9fafb' : '#111827') + ' !important; border-color: ' + (bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)') + ' !important; padding: 0 !important;';
                                
                                // Fix Browse Files button inside uploader
                                const browseBtn = uploader.querySelector('button, [data-baseweb="button"]');
                                if (browseBtn) {{
                                    browseBtn.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#ffffff' : '#1f2937') + ' !important; color: ' + (bgColor === '#ffffff' ? '#111827' : '#e5e7eb') + ' !important; border-color: ' + (bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)') + ' !important;';
                                }}
                            }}
                        }});
                        
                        // Fix Upload & Analyze button - SAME PATTERN AS THEME TOGGLE - FORCE VISIBLE IN LIGHT MODE
                        document.querySelectorAll('form button[type="submit"], .stForm button[type="submit"], .stButton > button, button[type="submit"], button[data-testid="baseButton-primary"]').forEach(btn => {{
                            if (btn && !isThemeToggleButton(btn)) {{
                                const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                const btnText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                const btnBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';
                                btn.style.cssText += 'background-color: ' + btnBg + ' !important; background: ' + btnBg + ' !important; color: ' + btnText + ' !important; border: 1px solid ' + btnBorder + ' !important; box-shadow: ' + (bgColor === '#ffffff' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none') + ' !important;';
                                
                                // Fix ALL nested elements (divs, spans, p tags)
                                const allNested = btn.querySelectorAll('div, span, p');
                                allNested.forEach(el => {{
                                    el.style.cssText += 'background-color: transparent !important; color: ' + btnText + ' !important;';
                                }});
                            }}
                        }});
                        
                        // Fix Browse Files button - SAME PATTERN AS THEME TOGGLE - FORCE VISIBLE IN LIGHT MODE
                        document.querySelectorAll('.stFileUploader button, .stFileUploader [data-baseweb="button"], .stFileUploader [data-testid="baseButton-secondary"]').forEach(btn => {{
                            if (btn) {{
                                const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                const btnText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                const btnBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';
                                btn.style.cssText += 'background-color: ' + btnBg + ' !important; background: ' + btnBg + ' !important; color: ' + btnText + ' !important; border: 1px solid ' + btnBorder + ' !important; box-shadow: ' + (bgColor === '#ffffff' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none') + ' !important;';
                                
                                // Fix ALL nested elements (divs, spans, p tags)
                                const allNested = btn.querySelectorAll('div, span, p');
                                allNested.forEach(el => {{
                                    el.style.cssText += 'background-color: transparent !important; color: ' + btnText + ' !important;';
                                }});
                            }}
                        }});
                        
                        // Fix uploaded file visibility - ALWAYS VISIBLE - FORCE ALL TEXT
                        document.querySelectorAll('.stFileUploader .uploadedFile, .stFileUploader [data-testid="stFileUploaderFile"]').forEach(fileEl => {{
                            if (fileEl) {{
                                const fileBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                const fileText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                const fileBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.15)';
                                fileEl.style.cssText += 'background-color: ' + fileBg + ' !important; background: ' + fileBg + ' !important; color: ' + fileText + ' !important; border: 1px solid ' + fileBorder + ' !important;';
                                // Fix ALL nested elements - recursively
                                const allTextElements = fileEl.querySelectorAll('*');
                                allTextElements.forEach(textEl => {{
                                    if (textEl && textEl.tagName !== 'BUTTON' && textEl.tagName !== 'SVG') {{
                                        textEl.style.cssText += 'color: ' + fileText + ' !important; background-color: transparent !important;';
                                    }}
                                }});
                                // Also force direct children
                                Array.from(fileEl.children).forEach(child => {{
                                    child.style.cssText += 'color: ' + fileText + ' !important; background-color: ' + fileBg + ' !important;';
                                }});
                            }}
                        }});
                        
                        // Middle theme + Upload buttons with respect to the Resume report (PDF) section
                        const pdfRow = document.querySelector('[data-testid="stHorizontalBlock"]:has(#report-top-actions-marker)');
                        if (pdfRow && pdfRow.lastElementChild) {{
                            const actionsCol = pdfRow.lastElementChild;
                            actionsCol.style.display = 'flex';
                            actionsCol.style.flexDirection = 'column';
                            actionsCol.style.justifyContent = 'center';
                            actionsCol.style.gap = '8px';
                        }}
                        
                        // Theme toggle styling is handled in app-level header CSS.
                        const computedRootStyles = (target.getComputedStyle && doc && doc.documentElement)
                            ? target.getComputedStyle(doc.documentElement)
                            : null;
                        const uniformHoverBg = (computedRootStyles && computedRootStyles.getPropertyValue('--excelcv-uniform-hover-bg').trim())
                            || (bgColor === '#ffffff' ? 'rgba(239, 246, 255, 0.98)' : 'rgba(37, 99, 235, 0.16)');
                        const uniformHoverBorder = (computedRootStyles && computedRootStyles.getPropertyValue('--excelcv-uniform-hover-border').trim())
                            || (bgColor === '#ffffff' ? 'rgba(37, 99, 235, 0.62)' : 'rgba(56, 189, 248, 0.65)');
                        const uniformHoverShadow = (computedRootStyles && computedRootStyles.getPropertyValue('--excelcv-uniform-hover-shadow').trim())
                            || (bgColor === '#ffffff'
                                ? '0 0 0 3px rgba(37, 99, 235, 0.14)'
                                : '0 0 0 3px rgba(56, 189, 248, 0.14)');

                        // Apply Warm Sun glow hover to textarea - boundary glow only (no background/inset)
                        document.querySelectorAll('.stTextArea textarea').forEach(textarea => {{
                            if (textarea) {{
                                textarea.addEventListener('mouseenter', function() {{
                                    this.style.cssText += 'box-shadow: ' + uniformHoverShadow + ' !important; border-color: ' + uniformHoverBorder + ' !important; background: ' + uniformHoverBg + ' !important; background-color: ' + uniformHoverBg + ' !important;';
                                }});
                                textarea.addEventListener('mouseleave', function() {{
                                    if (!this.matches(':focus')) {{
                                        this.style.cssText = this.style.cssText.replace(/box-shadow:\\s*[^;]+/g, '').replace(/border-color:\\s*[^;]+/g, '');
                                    }}
                                }});
                            }}
                        }});
                        
                        /* Removed .stFileUploader hover - only dropzone should glow, matching textarea behavior */
                        
                        // Apply Warm Sun glow hover to dropzone - EXACTLY matching textarea hover style
                        function fixDropzoneGlow() {{
                            document.querySelectorAll('.stFileUploader [data-testid="stFileUploaderDropzone"]').forEach(dropzone => {{
                                if (dropzone) {{
                                    // Always remove box-shadow when not hovered (continuously enforce)
                                    if (!dropzone.matches(':hover')) {{
                                        dropzone.style.setProperty('box-shadow', 'none', 'important');
                                    }}

                                    if (!dropzone.hasAttribute('data-glow-applied')) {{
                                        dropzone.setAttribute('data-glow-applied', 'true');

                                        // Explicitly remove any default box-shadow first (matching textarea behavior)
                                        dropzone.style.setProperty('box-shadow', 'none', 'important');

                                        dropzone.addEventListener('mouseenter', function() {{
                                            this.style.setProperty('box-shadow', uniformHoverShadow, 'important');
                                            this.style.setProperty('border-color', uniformHoverBorder, 'important');
                                            this.style.setProperty('background', uniformHoverBg, 'important');
                                            this.style.setProperty('background-color', uniformHoverBg, 'important');
                                        }});

                                        dropzone.addEventListener('mouseleave', function() {{
                                            this.style.setProperty('box-shadow', 'none', 'important');
                                            this.style.removeProperty('border-color');
                                        }});
                                    }}
                                }}
                            }});
                        }}
                        
                        // Run immediately and keep polling briefly while Streamlit stabilizes.
                        fixDropzoneGlow();
                        const dropzoneInterval = setInterval(fixDropzoneGlow, 300);
                        setTimeout(() => clearInterval(dropzoneInterval), 12000);
                        
                        // Also run on DOM changes
                        if (document.body) {{
                            new MutationObserver(() => {{
                                setTimeout(fixDropzoneGlow, 5);
                            }}).observe(document.body, {{
                                childList: true,
                                subtree: true
                            }});
                        }}
                        
                        // Apply Warm Sun hover to "Upload another resume" button - boundary-only glow (matching textarea/dropzone)
                        function fixUploadButtonGlow() {{
                            document.querySelectorAll('button').forEach(btn => {{
                                if (btn && (btn.textContent && btn.textContent.includes('Upload another resume'))) {{
                                    const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                    
                                    // Continuously enforce no background glow
                                    if (!btn.matches(':hover')) {{
                                        btn.style.setProperty('background', btnBg, 'important');
                                        btn.style.setProperty('background-color', btnBg, 'important');
                                        btn.style.setProperty('background-image', 'none', 'important');
                                    }}
                                    
                                    if (!btn.hasAttribute('data-upload-glow-applied')) {{
                                        btn.setAttribute('data-upload-glow-applied', 'true');

                                        btn.addEventListener('mouseenter', function() {{
                                            this.style.setProperty('box-shadow', uniformHoverShadow, 'important');
                                            this.style.setProperty('border-color', uniformHoverBorder, 'important');
                                            // Keep background unchanged - NO background glow
                                            this.style.setProperty('background', btnBg, 'important');
                                            this.style.setProperty('background-color', btnBg, 'important');
                                            this.style.setProperty('background-image', 'none', 'important');
                                            // Ensure nested elements remain transparent
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
                        
                        // Run continuously for a short warm-up period only.
                        fixUploadButtonGlow();
                        const uploadBtnInterval = setInterval(fixUploadButtonGlow, 300);
                        setTimeout(() => clearInterval(uploadBtnInterval), 12000);
                        
                        // Fix ALL secondary buttons
                        document.querySelectorAll('button[data-testid="baseButton-secondary"]').forEach(btn => {{
                            if (btn && !isThemeToggleButton(btn)) {{
                                btn.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#ffffff' : '#1f2937') + ' !important; color: ' + (bgColor === '#ffffff' ? '#111827' : '#e5e7eb') + ' !important; border-color: ' + (bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)') + ' !important;';
                            }}
                        }});
                        
                        // Fix Download Reports and any other buttons inside report area (override Streamlit dark defaults)
                        document.querySelectorAll('.report-main button, .report-sidebar button').forEach(btn => {{
                            if (btn) {{
                                const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                const btnText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                const btnBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';
                                btn.style.cssText += 'background-color: ' + btnBg + ' !important; background: ' + btnBg + ' !important; color: ' + btnText + ' !important; border: 1px solid ' + btnBorder + ' !important;';
                                const nested = btn.querySelectorAll('*');
                                nested.forEach(el => {{
                                    if (el && el.style) el.style.cssText += 'background-color: transparent !important; color: ' + btnText + ' !important;';
                                }});
                            }}
                        }});
                        
                        // Catch-all: force theme on EVERY button in the app (download buttons may not be inside .report-main)
                        const viewContainerAllButtons = document.querySelector('[data-testid="stAppViewContainer"]');
                        if (viewContainerAllButtons) {{
                            viewContainerAllButtons.querySelectorAll('button').forEach(btn => {{
                                if (btn && !isThemeToggleButton(btn)) {{
                                    const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                    const btnText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                    const btnBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';
                                    btn.style.setProperty('background-color', btnBg, 'important');
                                    btn.style.setProperty('background', btnBg, 'important');
                                    btn.style.setProperty('color', btnText, 'important');
                                    btn.style.setProperty('border', '1px solid ' + btnBorder, 'important');
                                    btn.querySelectorAll('*').forEach(el => {{
                                        if (el && el.style) {{
                                            el.style.setProperty('background-color', 'transparent', 'important');
                                            el.style.setProperty('color', btnText, 'important');
                                        }}
                                    }});
                                }}
                            }});
                        }}

                        // Always reset theme toggle visuals last to keep it icon-only.
                        resetThemeToggleVisuals();
                    }} catch(e) {{
                        console.error('Theme error:', e);
                    }}
                }}
                
                // Run immediately multiple times
                forceTheme();
                setTimeout(forceTheme, 10);
                setTimeout(forceTheme, 50);
                setTimeout(forceTheme, 100);
                
                // Keep a moderate refresh interval and stop after warm-up.
                window.themeInterval = setInterval(forceTheme, 150);
                setTimeout(() => {{
                    if (window.themeInterval) {{
                        clearInterval(window.themeInterval);
                        window.themeInterval = null;
                    }}
                }}, 12000);
                
                // Also run on DOM changes
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
                
                // Run on all events
                ['DOMContentLoaded', 'load'].forEach(event => {{
                    window.addEventListener(event, forceTheme);
                }});
            }})();
