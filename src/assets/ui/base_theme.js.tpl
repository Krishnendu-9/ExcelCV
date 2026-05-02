            (function() {{
                const bgColor = '{bg_color}';
                const themeClass = bgColor === '#ffffff' ? 'theme-light' : 'theme-dark';

                function collectTargets() {{
                    const body = document.body;
                    const html = document.documentElement;
                    const stApp = document.querySelector('.stApp');
                    const viewContainer = document.querySelector('[data-testid="stAppViewContainer"]');
                    return [body, html, stApp, viewContainer].filter(Boolean);
                }}

                function applyThemeClass() {{
                    collectTargets().forEach((el) => {{
                        if (!el || !el.classList) return;
                        el.classList.remove('theme-light', 'theme-dark');
                        el.classList.add(themeClass);
                    }});
                }}

                // Apply immediately for this render pass.
                applyThemeClass();

                // One short follow-up pass for late-mounted Streamlit nodes.
                setTimeout(applyThemeClass, 60);
                setTimeout(applyThemeClass, 220);
            }})();
