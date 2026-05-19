            {theme_base_css}
            
            {css_variables}

            /* App-level scrollbar baseline. */
            :root {
                --excelcv-scrollbar-track: #edf1f4;
                --excelcv-scrollbar-thumb: #8e959d;
                --excelcv-scrollbar-thumb-hover: #757d86;
            }
            body.theme-light,
            .stApp.theme-light {
                color-scheme: light;
                --excelcv-scrollbar-track: #edf1f4;
                --excelcv-scrollbar-thumb: #8e959d;
                --excelcv-scrollbar-thumb-hover: #757d86;
            }
            html:has(body.theme-dark),
            html:has(.stApp.theme-dark),
            body.theme-dark,
            .stApp.theme-dark {
                color-scheme: dark;
                --excelcv-scrollbar-track: #1f2732;
                --excelcv-scrollbar-thumb: #7f8b99;
                --excelcv-scrollbar-thumb-hover: #9aa6b5;
            }
            
            /* Keep layout defaults intact; page-level modules can opt-in to custom overflow rules. */
            [data-testid="stHorizontalBlock"] {{
                align-items: flex-start !important;
            }}
            /* Placeholder visibility: explicit color so visible in light theme (no body class needed) */
            .stTextArea textarea::placeholder {{
                color: var(--placeholder-color) !important;
                opacity: 1 !important;
            }}
            .stTextArea textarea::-webkit-input-placeholder {{
                color: var(--placeholder-color) !important;
                opacity: 1 !important;
            }}
            .stTextArea textarea::-moz-placeholder {{
                color: var(--placeholder-color) !important;
                opacity: 1 !important;
            }}
            
            /* Textarea and Dropzone Styling */
            {textarea_css}
            {dropzone_css}
            
            /* Label Styling */
            {label_css}
            
            /* Theme Button Styling */
            {theme_button_css}
            
            /* Button Hover Effects */
            {button_hover_css}
            
            /* BUTTONS: variable-based so visible in light/dark without body class */
            .stButton > button,
            .stButton button,
            .stButton > button *,
            .stButton button *,
            form button[type="submit"],
            form button,
            form button *,
            .stForm button[type="submit"],
            .stForm button,
            .stForm button *,
            .stForm .stButton button,
            .stForm .stButton button *,
            button[data-testid="baseButton-primary"],
            button[data-testid="baseButton-primary"] * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-border) !important;
            }}
            .stButton > button,
            .stButton button,
            form button[type="submit"],
            form button,
            .stForm button[type="submit"],
            .stForm button,
            button[data-testid="baseButton-primary"] {{
                border: 1px solid var(--button-border) !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                padding: 0.75rem 1.5rem !important;
                min-height: 44px !important;
                box-shadow: var(--button-shadow) !important;
            }}
            .stButton > button:hover,
            .stButton button:hover,
            form button[type="submit"]:hover,
            form button:hover,
            .stForm button[type="submit"]:hover,
            .stForm button:hover,
            .stButton > button:hover *,
            .stButton button:hover *,
            form button:hover *,
            .stForm button:hover *,
            button[data-testid="baseButton-primary"]:hover,
            button[data-testid="baseButton-primary"]:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            .stButton > button:hover,
            .stButton button:hover,
            form button[type="submit"]:hover,
            form button:hover,
            .stForm button[type="submit"]:hover,
            .stForm button:hover,
            button[data-testid="baseButton-primary"]:hover {{
                box-shadow: var(--button-hover-shadow) !important;
            }}
            [data-testid="stAppViewContainer"] .stForm button,
            [data-testid="stAppViewContainer"] .stForm button *,
            [data-testid="stAppViewContainer"] .stForm .stButton button,
            [data-testid="stAppViewContainer"] .stForm .stButton button * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-border) !important;
            }}
            [data-testid="stAppViewContainer"] .stForm button:hover,
            [data-testid="stAppViewContainer"] .stForm button:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            /* Catch-all: every button in the app (e.g. Download Reports) - download buttons may sit outside .report-main in DOM */
            [data-testid="stAppViewContainer"] .stButton button,
            [data-testid="stAppViewContainer"] .stButton button *,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-primary"],
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-primary"] *,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-secondary"],
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-secondary"] * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-border) !important;
            }}
            [data-testid="stAppViewContainer"] .stButton button:hover,
            [data-testid="stAppViewContainer"] .stButton button:hover *,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-primary"]:hover,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-primary"]:hover *,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-secondary"]:hover,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-secondary"]:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            /* Nuclear: any button in the app (Streamlit download buttons may use different markup) */
            [data-testid="stAppViewContainer"] button {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border: 1px solid var(--button-border) !important;
            }}
            [data-testid="stAppViewContainer"] button:hover {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            [data-testid="stAppViewContainer"] button * {{
                background-color: transparent !important;
                color: var(--button-text) !important;
            }}
            [data-testid="stAppViewContainer"] button:hover * {{
                color: var(--button-text) !important;
            }}
            /* Browse files: secondary outline style, independent from primary CTA dark button */
            .stFileUploader button,
            .stFileUploader button *,
            .stFileUploader [data-baseweb="button"],
            .stFileUploader [data-baseweb="button"] * {{
                background-color: var(--bg-card) !important;
                background: var(--bg-card) !important;
                color: var(--text-primary) !important;
                border-color: var(--border-color) !important;
            }}
            .stFileUploader button,
            .stFileUploader [data-baseweb="button"] {{
                border: 1px solid var(--border-color) !important;
                border-radius: 8px !important;
                padding: 8px 16px !important;
                font-weight: 600 !important;
                min-height: 36px !important;
                box-shadow: none !important;
            }}
            .stFileUploader button:hover,
            .stFileUploader [data-baseweb="button"]:hover,
            .stFileUploader button:hover *,
            .stFileUploader [data-baseweb="button"]:hover * {{
                background-color: var(--bg-secondary) !important;
                background: var(--bg-secondary) !important;
                color: var(--text-primary) !important;
                border-color: var(--border-color) !important;
            }}
            button[data-testid="baseButton-secondary"],
            button[data-testid="baseButton-secondary"] * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border: 1px solid var(--button-border) !important;
            }}
            button[data-testid="baseButton-secondary"]:hover,
            button[data-testid="baseButton-secondary"]:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}

            /* Hide Streamlit's deploy button */
            #MainMenu {{
                visibility: hidden;
            }}
            .stDeployButton {{
                display: none !important;
            }}
            /* Remove top blank: collapse header so it takes no space */
            header[data-testid="stHeader"] {{
                display: none !important;
                height: 0 !important;
                min-height: 0 !important;
                padding: 0 !important;
                margin: 0 !important;
                overflow: hidden !important;
                border: none !important;
            }}
            [data-testid="stToolbar"],
            [data-testid="stStatusWidget"],
            [data-testid="stDecoration"] {{
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }}
            /* Nudge the first controls row flush to top */
            [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(.stSelectbox):first-child {{
                margin-top: 10px !important;
                padding-top: 0 !important;
            }}
            
            /* Hide Streamlit's default file size limit text */
            .stFileUploader > div > div > small {{
                display: none !important;
            }}
            
            /* Remove ALL top and bottom blank: zero padding/margin on every container */
            [data-testid="stAppViewContainer"] {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            [data-testid="stAppViewContainer"] section {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            [data-testid="stAppViewContainer"] > section > div {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}
            .main {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            .main .block-container {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
                margin-bottom: 0 !important;
                max-width: 1240px;
                background: transparent !important;
                overflow: visible !important;
            }}
            /* Collapse invisible markdown/script injection containers so top controls start at page top */
            [data-testid="stMainBlockContainer"] {{
                padding-top: 0 !important;
                margin-top: 0 !important;
            }}
            .block-container {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}
            /* Remove bottom blank: no margin/padding on last block */
            .main .block-container > div:last-child {{
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }}
            /* Tighten gaps between rows */
            [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {{
                margin-bottom: 0 !important;
            }}
            .topbar {{
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 0 8px;
                margin-bottom: 6px;
            }}
            .brand-mark {{
                width: 38px;
                height: 38px;
                border-radius: 14px;
                background: linear-gradient(135deg, #10b981, #7c6bff);
                display: grid;
                place-items: center;
                font-weight: 900;
                color: #ffffff;
                font-size: 1.2rem;
            }}
            .brand-copy {{
                display: flex;
                flex-direction: column;
                gap: 2px;
            }}
            .brand-title {{ 
                font-weight: 700; 
                font-size: 1.1rem; 
                color: var(--text-primary); 
            }}
            .brand-subtitle {{ 
                color: var(--text-secondary); 
                font-size: 0.85rem; 
            }}
            .site-brand {{
                display: flex;
                align-items: center;
                gap: 12px;
                min-height: 56px;
                padding-top: 4px;
            }}
            .site-logo-shell {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                border-radius: 0;
                padding: 0;
                line-height: 1;
                background: transparent;
                border: none;
                box-shadow: none;
            }}
            .site-logo-wordmark {{
                height: 36px;
                width: auto;
                max-width: 100%;
                display: block;
                object-fit: contain;
                object-position: left center;
            }}
            .site-logo-badge {{
                width: 52px;
                height: 52px;
                border-radius: 14px;
                background: linear-gradient(135deg, #10b981, #22d3ee);
                color: #ffffff;
                font-weight: 900;
                font-size: 1rem;
                display: grid;
                place-items: center;
                letter-spacing: 0.03em;
                box-shadow: 0 10px 24px rgba(16, 185, 129, 0.25);
            }}
            .site-brand-copy {{
                display: flex;
                align-items: center;
            }}
            .site-name {{
                color: var(--text-primary);
                font-size: 1.95rem;
                font-weight: 900;
                letter-spacing: 0.012em;
                margin: 0;
                line-height: 1;
            }}
            .site-nav {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                flex-wrap: nowrap;
                padding-top: 4px;
            }}
            .site-nav-item {{
                display: inline-flex;
                align-items: center;
                padding: 8px 13px;
                border-radius: 999px;
                border: 1px solid var(--border-color);
                background: var(--bg-card);
                color: var(--text-secondary);
                font-size: 0.92rem;
                font-weight: 700;
                line-height: 1;
                white-space: nowrap;
            }}
            .st-key-site_nav_action_bridge {{
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                overflow: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }}
            .st-key-site_nav_action_bridge [data-testid="stButton"] {{
                margin: 0 !important;
                padding: 0 !important;
            }}
            .st-key-site_nav_action_bridge button {{
                width: 1px !important;
                min-width: 1px !important;
                height: 1px !important;
                min-height: 1px !important;
                padding: 0 !important;
                border: 0 !important;
            }}
            [class*="st-key-nav_action_"] {{
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
                clip: rect(0 0 0 0) !important;
                clip-path: inset(50%) !important;
                white-space: nowrap !important;
                border: 0 !important;
            }}
            [class*="st-key-nav_action_"] [data-testid="stButton"],
            [class*="st-key-nav_action_"] button {{
                margin: 0 !important;
                padding: 0 !important;
                min-width: 1px !important;
                min-height: 1px !important;
                width: 1px !important;
                height: 1px !important;
                border: 0 !important;
                box-shadow: none !important;
            }}
            /* Force the st.code copy button to stay visible (Streamlit hides
               its wrapper at opacity:0 until hover). Only one st.code in the
               app — the support dialog's email row — so global scope is fine. */
            [data-testid="stCode"] > div,
            [data-testid="stCode"] button,
            [data-testid="stCodeBlockCopyButton"],
            [data-testid="stCodeCopyButton"] {{
                opacity: 1 !important;
                visibility: visible !important;
                pointer-events: auto !important;
            }}
            .theme-toggle-gap {{
                height: 4px;
            }}
            .st-key-theme_toggle_header {{
                margin-top: 0 !important;
            }}
            .site-header-rule {{
                height: 1px;
                margin: 6px 0 6px;
                background: var(--border-light);
            }}
            @media (max-width: 1200px) {{
                .site-name {{
                    font-size: 1.75rem;
                }}
                .site-logo-shell {{
                    padding: 0;
                }}
                .site-logo-wordmark {{
                    height: 32px;
                }}
                .site-logo-badge {{
                    width: 52px;
                    height: 52px;
                    font-size: 1rem;
                }}
            }}
            @media (max-width: 980px) {{
                .site-nav {{
                    justify-content: center;
                    gap: 8px;
                    flex-wrap: wrap;
                }}
                .site-nav-item {{
                    font-size: 0.82rem;
                    padding: 7px 10px;
                }}
                .site-name {{
                    font-size: 1.35rem;
                }}
                .site-logo-shell {{
                    padding: 0;
                }}
                .site-logo-wordmark {{
                    height: 28px;
                }}
                .site-logo-badge {{
                    width: 42px;
                    height: 42px;
                    font-size: 0.9rem;
                }}
                .theme-toggle-gap {{
                    height: 2px;
                }}
            }}
            /* Fix selectbox cursor issue and theme */
            div[data-baseweb="select"] input,
            div[data-baseweb="select"] > div,
            .stSelectbox > div > div > div input {{
                cursor: pointer !important;
                caret-color: transparent !important;
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color) !important;
            }}
            div[data-baseweb="select"] input:focus {{
                cursor: pointer !important;
                caret-color: transparent !important;
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            
            /* Fix selectbox container and all nested elements */
            .stSelectbox > div > div {{
                background-color: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
            }}
            .stSelectbox > div > div > div {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            .stSelectbox > div > div > div > div {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            
            /* Force all baseweb select elements */
            [data-baseweb="select"] {{
                background-color: var(--bg-card) !important;
            }}
            [data-baseweb="select"] > div {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            [data-baseweb="select"] input {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            
            /* Style selectbox (Mode dropdown) to match theme */
            .stSelectbox label {{
                color: var(--text-primary) !important;
                font-size: 0.9rem;
                font-weight: 700;
            }}

            /* Style checkbox labels to ensure visibility in both themes */
            .stCheckbox label,
            .stCheckbox label p,
            .stCheckbox label span,
            [data-testid="stCheckbox"] label,
            [data-testid="stCheckbox"] label p,
            [data-testid="stCheckbox"] label span,
            [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {{
                color: var(--text-primary) !important;
                opacity: 1 !important;
                font-size: 0.95rem !important;
                font-weight: 600 !important;
            }}
            body.theme-light .stCheckbox label,
            body.theme-light [data-testid="stCheckbox"] label,
            body.theme-light [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {{
                color: #1f2937 !important;
            }}
            body.theme-dark .stCheckbox label,
            body.theme-dark [data-testid="stCheckbox"] label,
            body.theme-dark [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {{
                color: #f9fafb !important;
            }}
            
            /* Fix selectbox dropdown background and text */
            div[data-baseweb="select"] > div {{
                background-color: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
                color: var(--text-primary) !important;
            }}
            div[data-baseweb="select"] input {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            div[data-baseweb="popover"] {{
                background-color: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
            }}
            div[data-baseweb="popover"] li {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            div[data-baseweb="popover"] li:hover {{
                background-color: var(--bg-secondary) !important;
            }}
            
            /* (Button styles above use CSS variables; no body.theme-* override) */
            
            /* Style text area */
            .stTextArea textarea {{
                background: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 12px !important;
                color: var(--text-primary) !important;
                padding: 12px 16px !important;
                font-size: 0.95rem !important;
                transition: all 0.2s ease !important;
                box-shadow: none !important;
            }}
            .stTextArea textarea:hover {{
                box-shadow: 0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4) !important;
                border-color: #f5e6a8 !important;
                background: var(--bg-card) !important;
                background-color: var(--bg-card) !important;
            }}
            .stTextArea textarea:focus {{
                border-color: #f5e6a8 !important;
                box-shadow: 0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4) !important;
            }}
            /* Target the label container that comes before textarea */
            .stTextArea > div:first-child,
            .stTextArea > div:first-child label,
            .stTextArea > div:first-child > label {{
                color: {label_text_color} !important;
                font-weight: 700 !important;
                font-size: 1.28rem !important;
                margin-bottom: 0 !important;
                margin-top: 0 !important;
                display: block !important;
                letter-spacing: 0.01em !important;
                line-height: 1.2 !important;
            }}
            /* Style text area label - Professional and prominent styling - Multiple selectors for maximum coverage */
            .stTextArea label,
            .stTextArea > label,
            .stTextArea label p,
            .stTextArea label span,
            [data-testid="stTextArea"] label,
            [data-testid="stTextArea"] > label,
            .stForm .stTextArea label,
            .stForm .stTextArea > label,
            form .stTextArea label,
            form .stTextArea > label {{
                color: {label_text_color} !important;
                font-weight: 700 !important;
                font-size: 1.28rem !important;
                margin-bottom: 0 !important;
                margin-top: 0 !important;
                display: block !important;
                letter-spacing: 0.01em !important;
                line-height: 1.2 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
                text-transform: none !important;
            }}
            /* Additional specificity for light mode - Professional styling with accent line */
            body.theme-light .stTextArea label,
            body.theme-light .stTextArea > label,
            body.theme-light [data-testid="stTextArea"] label,
            body.theme-light .stForm .stTextArea label {{
                color: #1f2937 !important;
                border-bottom: none !important;
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }}
            /* Additional specificity for dark mode - Professional styling with accent line */
            body.theme-dark .stTextArea label,
            body.theme-dark .stTextArea > label,
            body.theme-dark [data-testid="stTextArea"] label,
            body.theme-dark .stForm .stTextArea label {{
                color: #f9fafb !important;
                border-bottom: none !important;
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }}
            /* Target label text content directly */
            .stTextArea label p,
            .stTextArea label span,
            .stTextArea label * {{
                color: inherit !important;
                font-size: inherit !important;
                font-weight: inherit !important;
            }}

            /* Theme-safe text/number inputs for utility pages (contact/evaluation/etc.) */
            .stTextInput label,
            .stNumberInput label,
            [data-testid="stTextInput"] label,
            [data-testid="stNumberInput"] label {{
                color: var(--text-primary) !important;
                font-weight: 600 !important;
            }}
            body.theme-light .stTextInput input,
            body.theme-light .stNumberInput input,
            body.theme-light [data-testid="stTextInput"] input,
            body.theme-light [data-testid="stNumberInput"] input,
            body.theme-light div[data-baseweb="input"] input {{
                background: #ffffff !important;
                background-color: #ffffff !important;
                color: #111827 !important;
                border: 1px solid rgba(15, 23, 42, 0.18) !important;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06) !important;
            }}
            body.theme-light div[data-baseweb="input"] {{
                background: #ffffff !important;
                border-color: rgba(15, 23, 42, 0.18) !important;
            }}
            body.theme-dark .stTextInput input,
            body.theme-dark .stNumberInput input,
            body.theme-dark [data-testid="stTextInput"] input,
            body.theme-dark [data-testid="stNumberInput"] input,
            body.theme-dark div[data-baseweb="input"] input {{
                background: #1f2937 !important;
                background-color: #1f2937 !important;
                color: #e5e7eb !important;
                border: 1px solid rgba(148, 163, 184, 0.28) !important;
                box-shadow: none !important;
            }}
            body.theme-dark div[data-baseweb="input"] {{
                background: #1f2937 !important;
                border-color: rgba(148, 163, 184, 0.28) !important;
            }}
            .stTextInput input::placeholder,
            .stNumberInput input::placeholder {{
                color: var(--placeholder-color) !important;
                opacity: 1 !important;
            }}
            /* Hide Streamlit helper hint like "Press Enter to apply" globally. */
            [data-testid="InputInstructions"],
            [data-testid="stTextInputInstructions"] {{
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                pointer-events: none !important;
            }}

            /* Radio controls readable in both themes */
            .stRadio label,
            .stRadio p,
            [data-testid="stRadio"] label,
            [data-testid="stRadio"] p {{
                color: var(--text-primary) !important;
                opacity: 1 !important;
            }}
            body.theme-light [data-testid="stRadio"] [role="radio"],
            body.theme-light [data-testid="stRadio"] label {{
                color: #1f2937 !important;
            }}
            body.theme-dark [data-testid="stRadio"] [role="radio"],
            body.theme-dark [data-testid="stRadio"] label {{
                color: #e5e7eb !important;
            }}

            /* Alert readability (especially warning/info cards in light mode) */
            [data-testid="stAlert"],
            [data-testid="stAlert"] *,
            [data-testid="stNotification"],
            [data-testid="stNotification"] * {{
                color: var(--text-primary) !important;
            }}
            body.theme-light [data-testid="stAlert"] {{
                border-color: rgba(217, 119, 6, 0.25) !important;
            }}
            body.theme-dark [data-testid="stAlert"] {{
                border-color: rgba(250, 204, 21, 0.25) !important;
            }}
            
            /* Style file uploader (Upload PDF/browse file) - LIGHT MODE */
            body.theme-light .stFileUploader {{
                border: 1px solid rgba(0, 0, 0, 0.1) !important;
                border-radius: 14px !important;
                padding: 0;
                background: #f9fafb !important;
                transition: all 0.2s ease;
            }}
            /* Removed .stFileUploader:hover - only dropzone should glow, not the container */
            /* Style file uploader label - Professional styling matching Job description - Multiple selectors */
            .stFileUploader label,
            .stFileUploader > label,
            .stFileUploader label p,
            .stFileUploader label span,
            [data-testid="stFileUploader"] label,
            [data-testid="stFileUploader"] > label,
            .stForm .stFileUploader label,
            .stForm .stFileUploader > label,
            form .stFileUploader label,
            form .stFileUploader > label {{
                color: {label_text_color} !important;
                font-weight: 700 !important;
                font-size: 1.28rem !important;
                margin-bottom: 0 !important;
                margin-top: 0 !important;
                display: block !important;
                letter-spacing: 0.01em !important;
                line-height: 1.2 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
                text-transform: none !important;
            }}
            /* Additional specificity for light mode - Professional styling with accent line */
            body.theme-light .stFileUploader label,
            body.theme-light .stFileUploader > label,
            body.theme-light [data-testid="stFileUploader"] label,
            body.theme-light .stForm .stFileUploader label {{
                color: #1f2937 !important;
                border-bottom: none !important;
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }}
            
            /* Style file uploader - DARK MODE */
            body.theme-dark .stFileUploader {{
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 14px !important;
                background: #111827 !important;
            }}
            /* Removed .stFileUploader:hover - only dropzone should glow, not the container */
            /* Additional specificity for dark mode - Professional styling with accent line */
            body.theme-dark .stFileUploader label,
            body.theme-dark .stFileUploader > label,
            body.theme-dark [data-testid="stFileUploader"] label,
            body.theme-dark .stForm .stFileUploader label {{
                color: #f9fafb !important;
                border-bottom: none !important;
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }}
            /* Target file uploader label text content directly */
            .stFileUploader label p,
            .stFileUploader label span,
            .stFileUploader label * {{
                color: inherit !important;
                font-size: inherit !important;
                font-weight: inherit !important;
            }}
            
            /* Fix file uploader inner elements and buttons */
            .stFileUploader > div {{
                background-color: transparent !important;
            }}
            
            /* Uploaded file display - theme-aware (light: white card, dark: dark card) */
            .stFileUploader .uploadedFile,
            .stFileUploader [data-testid="stFileUploaderFile"],
            .stFileUploader [data-testid="stFileUploaderFile"] > div,
            .stFileUploader [data-testid="stFileUploaderFile"] span,
            .stFileUploader [data-testid="stFileUploaderFile"] p,
            .stFileUploader [data-testid="stFileUploaderFile"] div,
            .stFileUploader .uploadedFile span,
            .stFileUploader .uploadedFile div,
            .stFileUploader .uploadedFile p,
            .stFileUploader .uploadedFile *,
            .stFileUploader [data-testid="stFileUploaderFile"] * {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
                border-color: var(--border-color) !important;
            }}
            .stFileUploader .uploadedFile,
            .stFileUploader [data-testid="stFileUploaderFile"] {{
                border: 1px solid var(--border-color) !important;
                padding: 8px 12px !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
                font-size: 0.9rem !important;
            }}
            .stFileUploader .uploadedFile:hover,
            .stFileUploader [data-testid="stFileUploaderFile"]:hover {{
                background-color: var(--bg-secondary) !important;
                border-color: var(--accent-2) !important;
            }}
            .stFileUploader .uploadedFile:hover *,
            .stFileUploader [data-testid="stFileUploaderFile"]:hover * {{
                background-color: transparent !important;
                color: var(--text-primary) !important;
            }}
            
            /* (Browse Files uses variable-based button rules above) */
            
            /* Style form elements */
            .stForm {{
                border: none;
                background: transparent;
            }}
            [data-testid="stForm"] {{
                border: none !important;
                background: transparent !important;
                padding: 0 !important;
                box-shadow: none !important;
            }}

            /* Upload page — hero wrapper card */
            .st-key-hero_wrapper {{
                position: relative;
                overflow: hidden;
                background:
                    radial-gradient(120% 70% at 100% 0%, rgba(20, 184, 166, 0.08), transparent 55%),
                    linear-gradient(135deg, var(--bg-hero), var(--bg-secondary));
                border: 1px solid var(--border-light);
                border-radius: 22px;
                padding: 26px 40px 24px;
                box-shadow: 0 8px 40px var(--shadow-lg);
                margin-top: -24px;
            }}
            /* Even vertical rhythm inside the hero card. */
            .st-key-hero_wrapper [data-testid="stVerticalBlock"] {{
                gap: 1rem !important;
            }}
            .st-key-hero_wrapper [data-testid="stForm"] {{
                margin-bottom: 0 !important;
            }}
            /* Hero CTA: make only the upload form submit button dark and prominent */
            .st-key-hero_wrapper [data-testid="stFormSubmitButton"] button,
            .st-key-hero_wrapper [data-testid="stFormSubmitButton"] button * {{
                background: #111827 !important;
                background-color: #111827 !important;
                color: #ffffff !important;
                border-color: #111827 !important;
                font-weight: 700 !important;
            }}
            .st-key-hero_wrapper [data-testid="stFormSubmitButton"] button:hover,
            .st-key-hero_wrapper [data-testid="stFormSubmitButton"] button:hover * {{
                background: #1f2937 !important;
                background-color: #1f2937 !important;
                color: #ffffff !important;
                border-color: #1f2937 !important;
            }}
            .hero-copy {{
                padding-right: 12px;
                margin-top: 0 !important;
            }}
            .hero-title {{
                font-size: clamp(2.3rem, 3.4vw, 3rem);
                line-height: 1.06;
                margin: 0 0 8px;
                font-weight: 900;
                letter-spacing: -0.02em;
                color: var(--text-primary);
            }}
            .hero-title span {{
                background: linear-gradient(118deg, #0f6ac9 8%, #14b8a6 92%);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
            }}
            .hero-subtitle {{
                color: var(--text-secondary);
                font-size: 1.02rem;
                max-width: none;
                margin: 0 0 12px;
                line-height: 1.5;
                white-space: nowrap;
            }}
            /* Allow the one-liner to wrap on screens too narrow to hold it. */
            @media (max-width: 1280px) {{
                .hero-subtitle {{
                    white-space: normal;
                }}
            }}
            .hero-chip-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin: 12px 0 6px;
            }}
            .hero-chip {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                border-radius: 999px;
                padding: 5px 11px;
                background: linear-gradient(145deg, var(--bg-card), var(--bg-secondary));
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.01em;
                margin: 0;
                transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
            }}
            .hero-chip:hover {{
                transform: translateY(-1px);
                border-color: rgba(20, 184, 166, 0.45);
                box-shadow: 0 6px 16px var(--shadow);
            }}
            .privacy-note {{
                color: var(--text-secondary);
                font-size: 0.82rem;
                margin-top: 6px;
                margin-bottom: 4px;
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .upload-preview {{
                background: var(--bg-sidebar);
                border: 1px solid var(--border-light);
                border-radius: 20px;
                padding: 16px;
                margin-top: 0;
                box-shadow: inset 0 1px 0 var(--border-light);
            }}

            /* ── Hero illustrative panel: animated "live report" mock ───────── */
            @property --hv-p {{
                syntax: '<percentage>';
                inherits: false;
                initial-value: 86%;
            }}
            /* ── Vertically center .hero-visual within the right column of the
                hero_wrapper. We force the row to stretch columns, then make the
                right column's stVerticalBlock use justify-content: center so
                the card sits in the middle of the available vertical space. */
            .st-key-hero_wrapper [data-testid="stHorizontalBlock"] {{
                align-items: stretch !important;
            }}
            .st-key-hero_wrapper [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(.hero-visual),
            .st-key-hero_wrapper [data-testid="stHorizontalBlock"] > [data-testid="column"]:has(.hero-visual) {{
                display: flex !important;
                flex-direction: column !important;
                align-self: stretch !important;
            }}
            .st-key-hero_wrapper [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(.hero-visual) > div,
            .st-key-hero_wrapper [data-testid="stHorizontalBlock"] > [data-testid="column"]:has(.hero-visual) > div {{
                flex: 1 1 auto !important;
                display: flex !important;
                flex-direction: column !important;
            }}
            .st-key-hero_wrapper [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:has(.hero-visual) [data-testid="stVerticalBlock"]:has(.hero-visual),
            .st-key-hero_wrapper [data-testid="stHorizontalBlock"] > [data-testid="column"]:has(.hero-visual) [data-testid="stVerticalBlock"]:has(.hero-visual) {{
                flex: 1 1 auto !important;
                justify-content: center !important;
            }}
            /* ── Stats strip (above the demo card) ──────────────────────── */
            .hv-stats {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
                padding: 4px 6px 14px;
                margin-bottom: 4px;
            }}
            .hv-stat-item {{
                display: flex;
                flex-direction: column;
                align-items: center;
                flex: 1;
                min-width: 0;
            }}
            .hv-stat-val {{
                font-size: 1.15rem;
                font-weight: 800;
                color: var(--text-primary);
                background: linear-gradient(120deg, #0f6ac9, #14b8a6);
                -webkit-background-clip: text;
                background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: 0.01em;
                line-height: 1.1;
            }}
            .hv-stat-label {{
                font-size: 0.68rem;
                font-weight: 600;
                color: var(--text-muted);
                letter-spacing: 0.06em;
                text-transform: uppercase;
                margin-top: 2px;
            }}
            .hv-stat-divider {{
                width: 1px;
                height: 28px;
                background: linear-gradient(180deg, transparent, var(--border-color), transparent);
                flex: none;
            }}

            /* ── How-it-works 3-step strip ─────────────────────────────── */
            .hv-steps {{
                display: flex;
                align-items: stretch;
                gap: 8px;
                margin-bottom: 14px;
            }}
            .hv-step {{
                flex: 1;
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 12px 12px;
                border-radius: 14px;
                background: var(--bg-card);
                border: 1px solid var(--border-light);
                box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
                min-width: 0;
            }}
            body.theme-dark .hv-step {{
                box-shadow: 0 4px 12px rgba(2, 8, 23, 0.30);
            }}
            .hv-step-num {{
                flex: none;
                width: 28px;
                height: 28px;
                border-radius: 999px;
                background: linear-gradient(135deg, #0f6ac9, #14b8a6);
                color: #ffffff;
                font-weight: 800;
                font-size: 0.88rem;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 10px rgba(20, 184, 166, 0.30);
            }}
            .hv-step-body {{
                display: flex;
                flex-direction: column;
                min-width: 0;
            }}
            .hv-step-title {{
                font-size: 0.85rem;
                font-weight: 700;
                color: var(--text-primary);
                line-height: 1.15;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .hv-step-desc {{
                font-size: 0.7rem;
                color: var(--text-muted);
                line-height: 1.2;
                margin-top: 2px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .hv-step-arrow {{
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--text-muted);
                font-size: 1.1rem;
                font-weight: 600;
                flex: none;
                padding: 0 2px;
                opacity: 0.7;
            }}

            .hero-visual {{
                --hv-c1: #0f6ac9;
                --hv-c2: #14b8a6;
                position: relative;
                overflow: hidden;
                border-radius: 20px;
                padding: 18px 20px 16px;
                background:
                    radial-gradient(120% 80% at 12% 0%, rgba(15, 106, 201, 0.10), transparent 60%),
                    radial-gradient(130% 90% at 100% 100%, rgba(20, 184, 166, 0.13), transparent 55%),
                    var(--bg-card);
                border: 1px solid var(--border-light);
                box-shadow: 0 22px 56px var(--shadow-lg);
                display: flex;
                flex-direction: column;
            }}
            .hv-top,
            .hv-bottom {{
                position: relative;
                z-index: 1;
                display: flex;
                flex-direction: column;
            }}
            .hv-glow {{
                position: absolute;
                inset: -45% -20% auto -20%;
                height: 240px;
                background: radial-gradient(50% 60% at 50% 0%, rgba(20, 184, 166, 0.22), transparent 70%);
                pointer-events: none;
                animation: hv-glow-drift 9s ease-in-out infinite alternate;
            }}
            .hv-header {{
                position: relative;
                z-index: 1;
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
            }}
            .hv-dot {{
                width: 9px;
                height: 9px;
                border-radius: 999px;
                background: #22c55e;
                animation: hv-pulse 2.2s ease-out infinite;
            }}
            .hv-title {{
                font-size: 0.95rem;
                font-weight: 800;
                color: var(--text-primary);
                letter-spacing: 0.01em;
            }}
            .hv-live {{
                margin-left: auto;
                font-size: 0.62rem;
                font-weight: 800;
                letter-spacing: 0.16em;
                color: #0e7490;
                background: rgba(20, 184, 166, 0.14);
                border: 1px solid rgba(20, 184, 166, 0.30);
                border-radius: 999px;
                padding: 3px 9px;
            }}
            .hv-ring-wrap {{
                position: relative;
                width: 100%;
                max-width: 320px;
                height: auto;
                margin: 6px auto 10px;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            .hv-ring {{
                order: 2;
                width: 100%;
                height: 12px;
                border-radius: 999px;
                background: linear-gradient(90deg, var(--hv-c1) 0%, var(--hv-c2) var(--hv-p, 86%), var(--bg-secondary) var(--hv-p, 86%));
                -webkit-mask: none;
                mask: none;
                animation: hv-sweep 1.7s cubic-bezier(.22, 1, .36, 1) .25s both;
            }}
            .hv-ring-label {{
                order: 1;
                position: static;
                inset: auto;
                display: flex;
                flex-direction: row;
                align-items: baseline;
                justify-content: center;
                gap: 10px;
            }}
            .hv-score {{
                font-size: 2.35rem;
                font-weight: 900;
                line-height: 1;
                background: linear-gradient(120deg, var(--hv-c1), var(--hv-c2));
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
            }}
            .hv-out {{
                font-size: 0.62rem;
                font-weight: 800;
                letter-spacing: 0.14em;
                color: var(--text-muted);
            }}
            .hv-grade {{
                text-align: center;
                font-size: 0.84rem;
                font-weight: 700;
                color: var(--text-secondary);
                margin: 0 0 12px;
            }}
            .hv-bars {{
                position: relative;
                z-index: 1;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            .hv-bar-row {{
                display: flex;
                align-items: center;
                gap: 9px;
                font-size: 0.78rem;
            }}
            .hv-bar-name {{
                flex: none;
                width: 104px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                color: var(--text-primary);
                font-weight: 800;
                letter-spacing: 0.01em;
            }}
            .hv-bar {{
                flex: 1;
                height: 7px;
                border-radius: 999px;
                background: var(--bg-secondary);
                overflow: hidden;
            }}
            .hv-bar-fill {{
                display: block;
                height: 100%;
                width: 0;
                border-radius: 999px;
                background: linear-gradient(90deg, var(--hv-c1), var(--hv-c2));
                animation: hv-grow 1.3s cubic-bezier(.22, 1, .36, 1) both;
            }}
            .hv-bar-row:nth-child(1) .hv-bar-fill {{ animation-delay: .35s; }}
            .hv-bar-row:nth-child(2) .hv-bar-fill {{ animation-delay: .47s; }}
            .hv-bar-row:nth-child(3) .hv-bar-fill {{ animation-delay: .59s; }}
            .hv-bar-row:nth-child(4) .hv-bar-fill {{ animation-delay: .71s; }}
            .hv-bar-val {{
                flex: none;
                width: 40px;
                text-align: right;
                color: var(--text-primary);
                font-weight: 700;
            }}
            .hv-tips {{
                position: relative;
                height: 20px;
                border-top: 1px solid var(--border-color);
                padding-top: 11px;
            }}
            .hv-tip {{
                position: absolute;
                left: 0;
                right: 0;
                top: 11px;
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 0.81rem;
                color: var(--text-secondary);
                opacity: 0;
                animation: hv-cycle 12s ease-in-out infinite;
            }}
            .hv-tip::before {{
                content: "✦";
                flex: none;
                color: #14b8a6;
                font-size: 0.78rem;
            }}
            .hv-tip:nth-child(1) {{ animation-delay: 0s; }}
            .hv-tip:nth-child(2) {{ animation-delay: -4s; }}
            .hv-tip:nth-child(3) {{ animation-delay: -8s; }}
            @keyframes hv-sweep {{
                from {{ --hv-p: 0%; }}
            }}
            @keyframes hv-grow {{
                to {{ width: var(--w, 100%); }}
            }}
            @keyframes hv-pulse {{
                0%   {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.45); }}
                70%  {{ box-shadow: 0 0 0 9px rgba(34, 197, 94, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
            }}
            @keyframes hv-glow-drift {{
                from {{ transform: translateX(-6%); opacity: 0.65; }}
                to   {{ transform: translateX(6%);  opacity: 1; }}
            }}
            @keyframes hv-cycle {{
                0%, 2%    {{ opacity: 0; transform: translateY(7px); }}
                6%, 27%   {{ opacity: 1; transform: translateY(0); }}
                33%, 100% {{ opacity: 0; transform: translateY(-7px); }}
            }}
            body.theme-dark .hv-visual,
            body.theme-dark .hero-visual {{
                box-shadow: 0 24px 60px rgba(2, 8, 23, 0.45);
            }}
            body.theme-dark .hv-live {{
                color: #5eead4;
                background: rgba(20, 184, 166, 0.18);
                border-color: rgba(94, 234, 212, 0.30);
            }}
            body.theme-dark .hv-out {{
                color: #94a3b8;
            }}

            /* Hero columns: align top, zero out Streamlit's default column gap. */
            [data-testid="stHorizontalBlock"]:has(.hero-copy) {{
                margin-top: 0 !important;
                align-items: flex-start !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.hero-copy) > div {{
                margin-top: 0 !important;
                padding-top: 0 !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.hero-copy) > div:last-child [data-testid="stVerticalBlock"] > div:first-child {{
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            .landing-extended {{
                margin-top: 28px;
                padding: 28px;
                border-radius: 24px;
                border: 1px solid var(--border-light);
                background: linear-gradient(140deg, var(--bg-card), var(--bg-secondary));
                box-shadow: 0 18px 48px var(--shadow);
            }}
            .landing-band {{
                max-width: 860px;
                margin-bottom: 18px;
            }}
            .landing-kicker {{
                margin: 0 0 8px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-size: 0.78rem;
                font-weight: 700;
                color: var(--accent-2);
            }}
            .landing-title {{
                margin: 0;
                font-size: clamp(1.7rem, 3vw, 2.4rem);
                line-height: 1.15;
                color: var(--text-primary);
            }}
            .landing-subtitle {{
                margin: 10px 0 0;
                font-size: 1rem;
                line-height: 1.6;
                color: var(--text-secondary);
            }}
            .landing-feature-grid {{
                margin-top: 22px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 14px;
            }}
            .landing-feature-card {{
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 16px;
                transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
            }}
            .landing-feature-card:hover {{
                transform: translateY(-2px);
                border-color: rgba(16, 185, 129, 0.45);
                box-shadow: 0 12px 24px var(--shadow);
            }}
            .landing-feature-card h3 {{
                margin: 0 0 8px;
                font-size: 1.02rem;
                color: var(--text-primary);
            }}
            .landing-feature-card p {{
                margin: 0;
                color: var(--text-secondary);
                line-height: 1.5;
                font-size: 0.94rem;
            }}
            .landing-mode-shell {{
                margin-top: 16px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
            }}
            .landing-mode-card {{
                background: linear-gradient(160deg, var(--bg-sidebar), var(--bg-card));
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 14px;
            }}
            .mode-eyebrow {{
                margin: 0;
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--accent);
                font-weight: 700;
            }}
            .landing-mode-card h4 {{
                margin: 8px 0 6px;
                color: var(--text-primary);
                font-size: 1rem;
            }}
            .landing-mode-card p {{
                margin: 0;
                color: var(--text-secondary);
                line-height: 1.5;
                font-size: 0.9rem;
            }}
            .landing-flow {{
                margin-top: 18px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
            }}
            .landing-step {{
                background: var(--bg-card);
                border: 1px dashed var(--border-color);
                border-radius: 14px;
                padding: 14px;
            }}
            .step-num {{
                display: inline-block;
                margin-bottom: 6px;
                padding: 4px 8px;
                border-radius: 999px;
                background: rgba(16, 185, 129, 0.12);
                color: var(--accent);
                font-size: 0.78rem;
                font-weight: 700;
            }}
            .landing-step h4 {{
                margin: 0 0 6px;
                color: var(--text-primary);
                font-size: 1rem;
            }}
            .landing-step p {{
                margin: 0;
                color: var(--text-secondary);
                font-size: 0.92rem;
                line-height: 1.5;
            }}
            .landing-proof-grid {{
                margin-top: 18px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
                gap: 14px;
            }}
            .proof-tile {{
                background: var(--bg-sidebar);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 12px;
            }}
            .proof-label {{
                margin: 0;
                color: var(--text-secondary);
                font-size: 0.8rem;
            }}
            .proof-value {{
                margin: 6px 0 0;
                color: var(--text-primary);
                font-size: 1rem;
                font-weight: 700;
            }}
            .landing-faq {{
                margin-top: 20px;
                padding-top: 2px;
            }}
            .landing-faq h3 {{
                margin: 0 0 6px;
                color: var(--text-primary);
                font-size: 1.2rem;
            }}
            .landing-faq-item {{
                border: 1px solid var(--border-color);
                border-radius: 12px;
                background: var(--bg-card);
                padding: 12px 14px;
                margin-top: 8px;
            }}
            .landing-faq-item h4 {{
                margin: 0;
                color: var(--text-primary);
                font-weight: 700;
            }}
            .landing-faq-item p {{
                margin: 10px 0 0;
                color: var(--text-secondary);
                line-height: 1.55;
                font-size: 0.92rem;
            }}
            .landing-feature-card,
            .landing-mode-card,
            .landing-step,
            .proof-tile,
            .landing-faq-item {{
                opacity: 0;
                transform: translateY(10px);
                animation: landing-fade-up 0.45s ease forwards;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(1),
            .landing-mode-shell .landing-mode-card:nth-child(1),
            .landing-flow .landing-step:nth-child(1),
            .landing-proof-grid .proof-tile:nth-child(1),
            .landing-faq .landing-faq-item:nth-child(2) {{
                animation-delay: 0.04s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(2),
            .landing-mode-shell .landing-mode-card:nth-child(2),
            .landing-flow .landing-step:nth-child(2),
            .landing-proof-grid .proof-tile:nth-child(2),
            .landing-faq .landing-faq-item:nth-child(3) {{
                animation-delay: 0.08s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(3),
            .landing-mode-shell .landing-mode-card:nth-child(3),
            .landing-flow .landing-step:nth-child(3),
            .landing-proof-grid .proof-tile:nth-child(3),
            .landing-faq .landing-faq-item:nth-child(4) {{
                animation-delay: 0.12s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(4),
            .landing-proof-grid .proof-tile:nth-child(4),
            .landing-faq .landing-faq-item:nth-child(5) {{
                animation-delay: 0.16s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(5) {{
                animation-delay: 0.2s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(6) {{
                animation-delay: 0.24s;
            }}
            @keyframes landing-fade-up {{
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            @media (max-width: 1100px) {{
                .hero-title {{
                    font-size: 2.8rem;
                }}
                .upload-preview {{
                    padding: 18px;
                    margin-top: 10px;
                }}
                .hero-visual {{
                    margin-top: 12px;
                }}
                .landing-extended {{
                    padding: 22px;
                }}
            }}
            @media (max-width: 768px) {{
                .st-key-hero_wrapper {{
                    padding: 28px 22px 24px;
                    margin-top: -16px;
                }}
                .hero-title {{
                    font-size: 2.15rem;
                    line-height: 1.12;
                }}
                .hero-subtitle {{
                    font-size: 1rem;
                }}
                .hero-chip {{
                    font-size: 0.76rem;
                    padding: 6px 9px;
                }}
                .upload-preview {{
                    margin-top: 0;
                }}
                .hero-visual {{
                    padding: 18px 18px 16px;
                }}
                .hv-ring-wrap {{
                    max-width: 100%;
                }}
                .hv-score {{
                    font-size: 2.2rem;
                }}
                .landing-title {{
                    font-size: 1.6rem;
                }}
                .landing-subtitle {{
                    font-size: 0.95rem;
                }}
                .landing-feature-grid,
                .landing-mode-shell,
                .landing-flow {{
                    grid-template-columns: 1fr;
                    gap: 14px;
                }}
            }}
            @media (prefers-reduced-motion: reduce) {{
                .landing-feature-card,
                .landing-mode-card,
                .landing-step,
                .proof-tile,
                .landing-faq-item {{
                    opacity: 1;
                    transform: none;
                    animation: none;
                }}
                .hv-glow,
                .hv-dot,
                .hv-ring,
                .hv-bar-fill,
                .hv-tip {{
                    animation: none !important;
                }}
                .hv-ring {{
                    --hv-p: 86%;
                }}
                .hv-bar-fill {{
                    width: var(--w, 100%) !important;
                }}
                .hv-tip:nth-child(1) {{
                    opacity: 1;
                }}
            }}

            /* ===== Full-width Professional Footer ===== */
            .site-footer-band {{
                position: relative;
                left: 50%;
                transform: translateX(-50%);
                width: 100vw;
                margin-top: 0;
                margin-bottom: 0 !important;
                background: linear-gradient(180deg, var(--bg-card), var(--bg-secondary));
                border-top: 1px solid var(--border-color);
                box-shadow: 0 -12px 30px var(--shadow);
                box-sizing: border-box;
            }}
            .site-footer-inner {{
                width: 100%;
                margin: 0 auto;
                padding: 28px 48px 20px;
                display: flex;
                flex-direction: column;
                gap: 24px;
            }}
            .site-footer-brand-logo {{
                height: 42px;
                width: auto;
                display: block;
                max-width: min(220px, 100%);
                margin-bottom: 10px;
            }}
            .site-footer-divider-text {{
                color: var(--text-secondary);
                font-size: 0.9rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-weight: 700;
                white-space: nowrap;
            }}
            .site-footer-grid {{
                display: grid;
                grid-template-columns: minmax(300px, 1fr) max-content;
                justify-content: space-between;
                column-gap: 26px;
                row-gap: 25px;
                align-items: start;
            }}
            .site-footer-links-grid {{
                width: auto;
                max-width: 100%;
                margin-left: auto;
                margin-right: 0;
                display: grid;
                grid-template-columns: repeat(3, max-content);
                justify-content: end;
                column-gap: 56px;
                row-gap: 16px;
                align-items: start;
            }}
            .site-footer-link-grid-2col {{
                display: grid;
                grid-template-columns: repeat(2, max-content);
                column-gap: 28px;
                row-gap: 8px;
            }}
            .site-footer-link-col--wide .site-footer-link-grid-2col a {{
                display: block;
            }}
            .site-footer-brand-title {{
                font-size: 2rem;
                font-weight: 800;
                color: var(--text-primary);
                line-height: 1;
                margin-bottom: 10px;
            }}
            .site-footer-brand-text {{
                margin: 0;
                max-width: 52ch;
                color: var(--text-secondary);
                line-height: 1.58;
                font-size: 1.02rem;
            }}
            .site-footer-link-col h4 {{
                margin: 0 0 10px;
                color: var(--text-primary);
                font-size: 1.05rem;
                font-weight: 700;
            }}
            .site-footer-link-col {{
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            .site-footer-link-col a {{
                color: var(--text-secondary);
                text-decoration: none;
                font-size: 0.98rem;
                transition: color 0.2s ease;
            }}
            .site-footer-link-col a:hover,
            .site-footer-link-col a:focus-visible {{
                color: var(--accent);
                text-decoration: underline;
            }}
            .site-footer-bottom {{
                border-top: 1px solid var(--border-color);
                padding-top: 14px;
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                gap: 10px;
                color: var(--text-secondary);
                font-size: 0.92rem;
            }}
            .site-footer-sep {{
                opacity: 0.7;
            }}
            .site-footer-band.footer-dark {{
                background: linear-gradient(180deg, rgba(10, 16, 28, 0.95), rgba(7, 12, 22, 0.98));
                border-top: 1px solid rgba(148, 163, 184, 0.26);
                box-shadow: 0 -14px 34px rgba(2, 8, 22, 0.28);
            }}
            .site-footer-band.footer-light {{
                background: linear-gradient(180deg, #eef2f8, #e9edf5);
                border-top: 1px solid rgba(100, 116, 139, 0.3);
                box-shadow: 0 -8px 22px rgba(148, 163, 184, 0.2);
            }}
            [data-testid="stElementContainer"]:has(.site-footer-band),
            [data-testid="stElementContainer"]:has(.site-footer-band) > div {{
                overflow: visible !important;
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }}
            [data-testid="stElementContainer"]:has(style),
            [data-testid="stElementContainer"]:has(script),
            [data-testid="stElementContainer"]:has(iframe[title^="st.iframe"]) {{
                margin-top: 0 !important;
                margin-bottom: 0 !important;
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}
            /* Collapse zero-height injection wrappers (components.html(height=0)) */
            [data-testid="stCustomComponentV1"][style*="height: 0"],
            [data-testid="stCustomComponentV1"][style*="height:0"] {{
                margin: 0 !important;
                padding: 0 !important;
                min-height: 0 !important;
                line-height: 0 !important;
            }}
            [data-testid="stElementContainer"]:has([data-testid="stCustomComponentV1"][style*="height: 0"]),
            [data-testid="stElementContainer"]:has([data-testid="stCustomComponentV1"][style*="height:0"]) {{
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 1px !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
                pointer-events: none !important;
                visibility: hidden !important;
                z-index: -1 !important;
                min-height: 0 !important;
            }}
            /* Collapse component iframes that render at height=0.
               Root cause: Streamlit's stVerticalBlock is a flex column with a
               `gap` between children. Each components.html(height=0) call adds
               a child stElementContainer; even with the wrapper at height: 0,
               the parent's flex gap still applies on both sides of each empty
               child. With 5–6 inject_* helpers called before the footer, that
               accumulates into ~250–300px of blank space above the footer.
               Fix: take these empty wrappers out of normal flow with position:
               absolute so the flex layout treats them as if they aren't there.
               The iframe still loads and its script still runs. */
            [data-testid="stElementContainer"]:has(> [data-testid="stCustomComponentV1"] > iframe[height="0"]),
            [data-testid="stElementContainer"]:has(iframe[height="0"]) {{
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 1px !important;
                height: 0 !important;
                min-height: 0 !important;
                max-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
                line-height: 0 !important;
                pointer-events: none !important;
                visibility: hidden !important;
                z-index: -1 !important;
            }}
            [data-testid="stElementContainer"]:has(iframe[height="0"]) [data-testid="stCustomComponentV1"],
            [data-testid="stElementContainer"]:has(iframe[height="0"]) iframe {{
                height: 0 !important;
                min-height: 0 !important;
                max-height: 0 !important;
                width: 1px !important;
                margin: 0 !important;
                padding: 0 !important;
                display: block !important;
                border: 0 !important;
            }}
            /* Same treatment for style/script-only element containers, which
               also occupy a flex slot in stVerticalBlock and would otherwise
               contribute gap above the footer. */
            [data-testid="stElementContainer"]:has(> style:only-child),
            [data-testid="stElementContainer"]:has(> script:only-child) {{
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 1px !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
                pointer-events: none !important;
                visibility: hidden !important;
                z-index: -1 !important;
            }}
            /* Streamlit's bottom anchor (used internally for iframe-height
               measurement) ships with default margin that opens a large gap
               between the last page block and the footer. Collapse it. */
            [data-testid="stAppIframeResizerAnchor"] {{
                height: 0 !important;
                min-height: 0 !important;
                max-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                line-height: 0 !important;
                font-size: 0 !important;
            }}
            html,
            body {{
                overflow-x: hidden !important;
            }}
            html {{
                overflow-y: scroll !important;
                scrollbar-gutter: stable !important;
            }}
            body {{
                overflow-y: visible !important;
            }}
            html,
            [data-testid="stAppViewContainer"] {{
                scrollbar-width: auto !important;
                scrollbar-color: var(--excelcv-scrollbar-thumb) var(--excelcv-scrollbar-track) !important;
            }}
            html::-webkit-scrollbar,
            [data-testid="stAppViewContainer"]::-webkit-scrollbar {{
                width: 12px !important;
                height: 12px !important;
            }}
            html::-webkit-scrollbar-track,
            [data-testid="stAppViewContainer"]::-webkit-scrollbar-track {{
                background: var(--excelcv-scrollbar-track) !important;
            }}
            html::-webkit-scrollbar-thumb,
            [data-testid="stAppViewContainer"]::-webkit-scrollbar-thumb {{
                background: var(--excelcv-scrollbar-thumb) !important;
                border-radius: 999px !important;
                border: 2px solid var(--excelcv-scrollbar-track) !important;
            }}
            html::-webkit-scrollbar-thumb:hover,
            [data-testid="stAppViewContainer"]::-webkit-scrollbar-thumb:hover {{
                background: var(--excelcv-scrollbar-thumb-hover) !important;
            }}
            [data-testid="stAppViewContainer"],
            [data-testid="stAppViewContainer"] > section.main,
            [data-testid="stMain"] {{
                max-height: none !important;
                overflow-x: hidden !important;
                overflow-y: visible !important;
            }}
            [data-testid="stMainBlockContainer"] > div:last-child,
            .main .block-container > div:last-child {{
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }}
            @media (max-width: 1024px) {{
                .site-footer-inner {{
                    width: calc(100% - 34px);
                }}
                .site-footer-grid {{
                    grid-template-columns: 1fr;
                    gap: 18px 24px;
                }}
                .site-footer-links-grid {{
                    max-width: none;
                    margin-left: 0;
                    grid-template-columns: repeat(2, minmax(160px, 1fr));
                    column-gap: 24px;
                    row-gap: 16px;
                }}
                .site-footer-link-col--wide {{
                    grid-column: span 2;
                }}
            }}
            @media (max-width: 680px) {{
                .site-footer-link-grid-2col {{
                    grid-template-columns: 1fr;
                }}
            }}
            @media (max-width: 680px) {{
                .site-footer-inner {{
                    width: calc(100% - 20px);
                    padding: 24px 0 16px;
                    gap: 18px;
                }}
                .site-footer-brand-logo {{
                    height: 36px;
                }}
                .site-footer-grid {{
                    grid-template-columns: 1fr;
                    gap: 14px;
                }}
                .site-footer-links-grid {{
                    grid-template-columns: 1fr;
                    column-gap: 0;
                    row-gap: 14px;
                }}
                .site-footer-brand-title {{
                    font-size: 1.6rem;
                }}
                .site-footer-brand-text {{
                    font-size: 0.95rem;
                }}
            }}
            .preview-card {{
                background: var(--bg-card) !important;
                border-radius: 18px;
                padding: 18px 18px 12px;
                color: var(--text-primary) !important;
                box-shadow: 0 20px 60px var(--shadow);
                border: 1px solid var(--border-light);
            }}
            
            /* Ensure preview card text is visible in both themes */
            .preview-card * {{
                color: var(--text-primary) !important;
            }}
            .preview-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
            }}
            .preview-badge {{
                background: rgba(16, 185, 129, 0.15);
                color: var(--accent);
                padding: 6px 12px;
                border-radius: 999px;
                font-weight: 700;
                font-size: 0.75rem;
                letter-spacing: 0.5px;
            }}
            .theme-dark .preview-badge {{
                background: rgba(16, 185, 129, 0.25);
                color: #34d399;
            }}
            .preview-score {{
                display: flex;
                align-items: baseline;
                gap: 6px;
                font-weight: 700;
            }}
            .preview-score .num {{ 
                color: var(--accent); 
                font-size: 1.8rem; 
            }}
            .preview-score .den {{ 
                color: var(--text-secondary); 
            }}
            .pill-row {{
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin: 4px 0 10px;
            }}
            .pill {{
                background: var(--bg-secondary);
                color: var(--text-primary);
                padding: 6px 10px;
                border-radius: 14px;
                font-size: 0.98rem;
                font-weight: 700;
            }}
            .progress-shell {{
                margin: 12px 0 6px;
            }}
            .progress-track {{
                width: 100%;
                height: 10px;
                background: var(--bg-secondary);
                border-radius: 12px;
                overflow: hidden;
            }}
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, var(--accent), #22d3ee);
                border-radius: 12px;
            }}
            .list-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid var(--border-color);
                background-color: transparent !important;
            }}
            .list-row:last-child {{ 
                border-bottom: none; 
            }}
            .list-row span {{ 
                font-size: 0.95rem; 
                color: var(--text-primary) !important; 
            }}
            
            /* Fix preview card list items to match theme */
            .preview-card .list-row {{
                background-color: transparent !important;
                color: var(--text-primary) !important;
            }}
            .preview-card .list-row span {{
                color: var(--text-primary) !important;
            }}
            
            /* Ensure icons in list rows are visible and properly colored */
            .list-row span:last-child {{
                font-weight: 700;
                font-size: 1.1rem;
            }}
            
            /* Make sure all text in preview card is visible */
            .preview-card,
            .preview-card * {{
                background-color: var(--bg-card) !important;
            }}
            .preview-card .text-primary,
            .preview-card .text-secondary,
            .preview-card .text-muted {{
                color: var(--text-primary) !important;
            }}

            /* Report page - center theme + Upload buttons with PDF section */
            #report-pdf-row-marker {{
                display: none !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }}
            #report-top-actions-marker {{
                display: none !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }}
            [data-testid="stElementContainer"]:has(#report-pdf-row-marker),
            [data-testid="stElementContainer"]:has(#report-top-actions-marker),
            [data-testid="stElementContainer"]:has(.site-header-rule) {{
                margin: 0 !important;
                padding: 0 !important;
                min-height: 0 !important;
                height: 0 !important;
            }}
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) {{
                margin-top: -44px !important;
                padding-top: 0 !important;
                position: relative;
                z-index: 3;
            }}
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child {{
                display: flex !important;
                flex-direction: column !important;
                justify-content: flex-start !important;
                gap: 8px !important;
                padding-top: 2px !important;
            }}
            .report-topline {{
                margin: 0 0 8px;
            }}
            .report-fileline {{
                display: flex;
                flex-direction: column;
                gap: 10px;
                background: linear-gradient(135deg, var(--bg-card), var(--bg-secondary));
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 10px 14px;
            }}
            .report-mode-label {{
                color: #7c6bff;
                font-size: 0.8rem;
                font-weight: 800;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                line-height: 1;
            }}
            .report-file-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
            }}
            .report-file-title {{ 
                margin: 0; 
                font-size: 2rem; 
                color: var(--text-primary); 
                line-height: 1.12;
                word-break: break-word;
                flex: 1;
                min-width: 0;
            }}
            .score-pill {{
                background: rgba(16,185,129,0.15);
                color: var(--accent);
                padding: 8px 12px;
                border-radius: 12px;
                font-weight: 700;
                min-width: 98px;
                text-align: center;
                flex-shrink: 0;
            }}
            .theme-dark .score-pill {{
                color: #a7f3d0;
            }}
            @media (max-width: 1200px) {{
                .report-file-title {{
                    font-size: 1.75rem;
                }}
                .report-mode-label {{
                    font-size: 0.76rem;
                    letter-spacing: 0.1em;
                }}
            }}
            @media (max-width: 980px) {{
                [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) {{
                    margin-top: -18px !important;
                }}
                .report-file-row {{
                    flex-direction: column;
                    align-items: flex-start;
                }}
                .score-pill {{
                    align-self: flex-start;
                }}
            }}
            .report-shell {{
                display: grid;
                grid-template-columns: 360px 1fr;
                gap: 20px;
            }}
            :root {{
                --excelcv-report-top: 96px;
            }}
            [data-testid="stHorizontalBlock"]:has(.report-sidebar):has(.report-main) {{
                align-items: stretch !important;
                overflow: visible !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.report-sidebar):has(.report-main) > div {{
                overflow: visible !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.report-sidebar):has(.report-main) > div:first-child {{
                position: relative !important;
                min-height: 100% !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.report-sidebar):has(.report-main) > div:first-child [data-testid="stVerticalBlock"] {{
                overflow: visible !important;
                height: 100% !important;
            }}
            .report-sidebar {{
                background: var(--bg-sidebar);
                border: 1px solid var(--border-light);
                border-radius: 18px;
                padding: 18px;
                box-shadow: 0 10px 34px var(--shadow);

                position: sticky !important;
                top: var(--excelcv-report-top, 96px) !important;
                align-self: flex-start !important;

                height: fit-content !important;
                max-height: calc(100vh - var(--excelcv-report-top, 96px) - 12px) !important;

                overflow-y: auto !important;
                overflow-x: hidden !important;

                z-index: 2;
            }}
            @media (max-width: 1099px) {{
                .report-sidebar {{
                    position: relative !important;
                    top: auto !important;
                    max-height: none !important;
                    overflow: visible !important;
                }}
            }}
            .score-card {{
                background: linear-gradient(145deg, var(--bg-card), var(--bg-sidebar));
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 18px;
                margin-bottom: 18px;
                text-align: center;
            }}
            .score-card .score-file {{
                font-size: 0.82rem;
                font-weight: 600;
                margin-bottom: 8px;
                max-width: 100%;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            /* "How this score is calculated" — compact collapsible card under the score. */
            .report-sidebar .score-breakdown-card {{
                margin: 0 0 18px 0;
                padding: 14px 16px;
                background: var(--bg-card);
                box-shadow: none;
            }}
            .report-sidebar .score-breakdown-card .detail-head h3 {{
                font-size: 1rem;
                letter-spacing: 0;
            }}
            .report-sidebar .score-breakdown-card .text-description {{
                font-size: 0.85rem;
            }}
            .report-sidebar .score-breakdown-card .issue-heading {{
                font-size: 0.85rem;
            }}
            .report-sidebar .score-breakdown-card .contact-row {{
                font-size: 0.82rem;
                flex-wrap: wrap;
            }}
            /* Animated score bar — same sweep engine as the homepage hero panel. */
            .report-score-ring-wrap {{
                position: relative;
                width: 100%;
                max-width: 300px;
                height: auto;
                margin: 10px auto 6px;
                display: flex;
                flex-direction: column;
                align-items: stretch;
                gap: 10px;
            }}
            .report-score-ring {{
                order: 2;
                width: 100%;
                height: 12px;
                border-radius: 999px;
                background: linear-gradient(90deg, var(--rsr-c, #f59e0b) 0%, var(--rsr-c, #f59e0b) var(--hv-p, 0%), var(--bg-secondary) var(--hv-p, 0%));
                -webkit-mask: none;
                mask: none;
                animation: hv-sweep 1.6s cubic-bezier(.22, 1, .36, 1) .2s both;
            }}
            .report-score-ring-label {{
                order: 1;
                position: static;
                inset: auto;
                display: flex;
                flex-direction: row;
                align-items: baseline;
                justify-content: center;
                flex-wrap: wrap;
                gap: 6px 8px;
            }}
            .report-score-ring-label .rsr-num {{
                font-size: 2.3rem;
                font-weight: 900;
                line-height: 1;
                color: var(--rsr-c, #f59e0b);
            }}
            .report-score-ring-label .rsr-den {{
                font-size: 0.84rem;
                font-weight: 700;
                color: var(--text-secondary);
            }}
            .report-score-ring-label .rsr-issues {{
                flex-basis: 100%;
                text-align: center;
                margin-top: 2px;
                font-size: 0.85rem;
            }}
            @media (prefers-reduced-motion: reduce) {{
                .report-score-ring {{ animation: none !important; }}
            }}
            .issues-text {{
                color: var(--text-secondary);
                font-size: 0.95rem;
            }}
            .issues-text.clickable {{
                cursor: pointer;
                color: #f87171;
                text-decoration: underline;
                transition: color 0.2s ease;
            }}
            .issues-text.clickable:hover {{
                color: #ef4444;
            }}
            .category {{
                border-top: 1px solid var(--border-light);
                padding: 12px 0;
            }}
            .category:first-of-type {{ 
                border-top: none; 
            }}
            .category-head {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 6px;
                color: var(--text-primary);
                font-weight: 700;
                letter-spacing: 0.02em;
                cursor: pointer;
                user-select: none;
                transition: color 0.2s ease;
                padding: 4px 0;
            }}
            .category-head:hover {{
                color: var(--accent);
            }}
            .category-head .category-title {{
                display: flex;
                align-items: center;
                gap: 8px;
                flex: 1;
            }}
            .category-chevron {{
                display: inline-block;
                transition: transform 0.3s ease;
                font-size: 0.85rem;
                color: var(--text-secondary);
                margin-left: 4px;
            }}
            .category-head.expanded .category-chevron {{
                transform: rotate(180deg);
            }}
            .category-items {{
                overflow: hidden;
                transition: max-height 0.3s ease, opacity 0.2s ease;
            }}
            .category-items.collapsed {{
                max-height: 0;
                opacity: 0;
                margin: 0;
                padding: 0;
            }}
            .category-items.expanded {{
                max-height: 1000px;
                opacity: 1;
            }}
            .category-score {{
                padding: 6px 10px;
                border-radius: 14px;
                font-weight: 700;
                font-size: 0.95rem;
            }}
            .score-good {{ 
                background: rgba(16,185,129,0.12); 
                color: #34d399; 
            }}
            .score-medium {{ 
                background: rgba(234,179,8,0.15); 
                color: #fbbf24; 
            }}
            .score-low {{ 
                background: rgba(239,68,68,0.16); 
                color: #f87171; 
            }}
            .subitem {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
                color: var(--text-secondary);
                padding: 8px 0;
                font-size: 0.92rem;
            }}
            .subitem .subitem-label-wrap {{
                display: flex;
                align-items: center;
                gap: 8px;
                flex: 1;
                min-width: 0;
            }}
            .subitem .subitem-icon {{
                flex-shrink: 0;
                width: 20px;
                height: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                font-size: 12px;
                font-weight: 700;
            }}
            .subitem .subitem-icon.icon-ok {{
                background: rgba(16,185,129,0.2);
                color: #34d399;
            }}
            .subitem .subitem-icon.icon-warn {{
                background: rgba(239,68,68,0.2);
                color: #f87171;
            }}
            .subitem.clickable {{
                cursor: pointer;
                transition: all 0.2s ease;
                border-radius: 6px;
                padding: 8px 10px;
                margin: 0 -10px;
            }}
            .subitem.clickable:hover {{
                background: var(--bg-secondary);
                color: var(--text-primary);
            }}
            .section-anchor {{
                scroll-margin-top: 100px;
            }}
            .badge {{
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 0.8rem;
                font-weight: 700;
            }}
            .badge-ok {{ 
                background: rgba(16,185,129,0.18); 
                color: #34d399; 
            }}
            .badge-warn {{ 
                background: rgba(239,68,68,0.18); 
                color: #f87171; 
            }}
            .badge-lock {{ 
                background: rgba(148,163,184,0.15); 
                color: var(--text-secondary); 
            }}
            body.theme-light .badge,
            .theme-light .badge {{
                border: 1px solid rgba(100, 116, 139, 0.24);
            }}
            body.theme-light .badge-ok,
            .theme-light .badge-ok {{
                background: rgba(16, 185, 129, 0.18);
                border-color: rgba(16, 185, 129, 0.34);
                color: #047857;
            }}
            body.theme-light .badge-warn,
            .theme-light .badge-warn {{
                background: rgba(239, 68, 68, 0.14);
                border-color: rgba(239, 68, 68, 0.3);
                color: #b91c1c;
            }}
            body.theme-light .badge-lock,
            .theme-light .badge-lock {{
                background: rgba(148, 163, 184, 0.22);
                border-color: rgba(100, 116, 139, 0.34);
                color: #334155;
            }}

            .report-main {{
                display: flex;
                flex-direction: column;
                gap: 28px;
            }}
            .detail-card {{
                background: var(--bg-secondary);
                border: 1px solid var(--border-light);
                border-radius: 14px;
                padding: 16px 18px;
                margin-bottom: 12px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            }}
            .report-group-wrap {{
                margin: 0;
            }}
            .report-group-wrap:last-of-type {{
                margin-bottom: 0;
            }}
            .report-group {{
                background: linear-gradient(140deg, var(--bg-card), var(--bg-sidebar));
                border: 1px solid var(--border-light);
                border-radius: 18px;
                padding: 18px;
                box-shadow: 0 12px 34px var(--shadow);
                margin: 0;
            }}
            .report-group-head {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 14px;
                padding: 4px 4px 2px;
            }}
            .report-group-head h3 {{
                margin: 0;
                font-size: 1.55rem;
                color: var(--text-primary);
                letter-spacing: 0.02em;
            }}
            .report-group-pill {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 7px 14px;
                border-radius: 999px;
                font-size: 0.82rem;
                font-weight: 700;
                color: var(--report-pill-text);
                background: var(--report-pill-bg);
                border: 1px solid var(--report-pill-border);
                white-space: nowrap;
            }}
            body.theme-light .report-group-pill,
            .theme-light .report-group-pill {{
                background: rgba(203, 213, 225, 0.72);
                border-color: rgba(100, 116, 139, 0.38);
                color: #1f2937;
            }}
            .report-group-body {{
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            .detail-head {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
            }}
            .detail-head-collapsible {{
                cursor: pointer;
                user-select: none;
            }}
            .detail-head h3 {{ 
                margin: 0; 
                display: inline-flex;
                align-items: center;
                gap: 10px;
            }}
            .detail-chevron {{
                display: inline-block;
                color: var(--text-secondary);
                font-size: 0.82rem;
                transition: transform 0.22s ease;
                transform-origin: center;
            }}
            .detail-card.expanded .detail-chevron {{
                transform: rotate(180deg);
            }}
            .detail-card.collapsed .detail-chevron {{
                transform: rotate(0deg);
            }}
            /* Shared body area for all report sections (Quantifying Impact, Spelling & Grammar, Strengths, etc.) - same as Suggestions */
            .section-body {{
                padding: 0 0 4px 0;
                margin: 0;
                overflow: hidden;
                transition: max-height 0.24s ease, opacity 0.2s ease;
            }}
            .detail-card.collapsed .section-body {{
                max-height: 0 !important;
                opacity: 0;
                padding: 0 !important;
                margin: 0 !important;
                pointer-events: none;
            }}
            .detail-card.expanded .section-body {{
                max-height: 10000px;
                opacity: 1;
                pointer-events: auto;
            }}
            .section-body-item {{
                margin-bottom: 6px;
                line-height: 1.45;
                color: var(--text-primary);
            }}
            .section-body-item:last-child {{
                margin-bottom: 0;
            }}
            .progress-track.dark {{
                background: var(--bg-secondary);
            }}
            .progress-fill.dark {{
                background: linear-gradient(90deg, var(--accent), #0ea5e9);
            }}
            /* Issue detail cards - for showing specific problems */
            .issue-card {{
                background: var(--bg-secondary);
                border: 1px solid var(--border-light);
                border-radius: 12px;
                padding: 20px;
                margin-top: 14px;
                text-align: center;
            }}
            .issue-card .issue-icon {{
                font-size: 1.75rem;
                margin-bottom: 6px;
            }}
            .issue-card .issue-count {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: #ef4444;
                color: #fff;
                border-radius: 50%;
                width: 28px;
                height: 28px;
                font-size: 0.85rem;
                font-weight: 700;
                position: relative;
                top: -15px;
                left: -8px;
            }}
            .issue-card .issue-heading {{
                font-size: 1.15rem;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 6px;
            }}
            .issue-card .issue-desc {{
                color: var(--text-secondary);
                font-size: 0.95rem;
                margin-bottom: 12px;
            }}
            .issue-item {{
                background: rgba(239, 68, 68, 0.12);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 14px;
                padding: 12px 16px;
                margin-top: 8px;
                text-align: left;
                display: flex;
                align-items: flex-start;
                gap: 14px;
                color: var(--text-primary);
                font-size: 0.92rem;
                line-height: 1.5;
            }}
            .issue-item .issue-x {{
                color: #ef4444;
                font-weight: 700;
                font-size: 1rem;
                flex-shrink: 0;
                margin-top: 1px;
            }}
            .issue-item-ok {{
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
            }}
            .issue-item-ok .issue-x {{
                color: #10b981;
            }}
            /* Contact Information rows */
            .contact-row {{
                display: flex;
                align-items: flex-start;
                gap: 12px;
                padding: 14px 18px;
                margin-top: 10px;
                border-radius: 14px;
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
            }}
            .contact-icon {{
                font-size: 1.1rem;
                font-weight: 700;
                flex-shrink: 0;
                margin-top: 1px;
            }}
            .contact-icon.found {{
                color: #10b981;
            }}
            .contact-icon.missing {{
                color: #ef4444;
            }}
            .contact-label {{
                font-weight: 700;
                color: var(--text-primary);
                white-space: nowrap;
            }}
            .contact-sep {{
                color: var(--text-secondary);
                flex-shrink: 0;
            }}
            .contact-value {{
                color: var(--text-primary);
                word-break: break-all;
            }}
            .contact-msg {{
                color: var(--text-secondary);
                font-size: 0.9rem;
                word-break: normal;
            }}
            /* Repeated word tags */
            .repeat-group {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 14px;
                margin-top: 10px;
                margin-bottom: 6px;
                text-align: left;
            }}
            .repeat-word-tag {{
                display: inline-block;
                padding: 6px 14px;
                border-radius: 8px;
                background: #dc2626;
                color: #fff;
                font-weight: 700;
                font-size: 0.9rem;
            }}
            .repeat-suggestion {{
                display: inline-block;
                padding: 6px 12px;
                border-radius: 8px;
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                font-size: 0.88rem;
            }}
            .repeat-label {{
                color: var(--text-secondary);
                font-size: 0.88rem;
                white-space: nowrap;
            }}
            /* Spelling issue tags */
            .spell-issue-row {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 8px;
                margin-top: 8px;
                text-align: left;
            }}
            .spell-tag {{
                display: inline-block;
                padding: 5px 12px;
                border-radius: 8px;
                background: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: var(--text-primary);
                font-size: 0.88rem;
            }}
            .spell-tag-label {{
                font-weight: 700;
                color: #ef4444;
                margin-right: 4px;
            }}
            /* Good status card */
            .good-card {{
                background: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.25);
            }}
            .good-card .issue-heading {{
                color: #10b981;
            }}
            .list-tag {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 14px;
                background: var(--bg-secondary);
                color: var(--text-primary);
                margin-right: 8px;
                margin-bottom: 6px;
                font-size: 0.9rem;
            }}
            .text-primary {{ 
                color: var(--text-primary); 
            }}
            .text-secondary {{ 
                color: var(--text-secondary); 
            }}
            .text-muted {{ 
                color: var(--text-secondary); 
            }}
            .text-description {{ 
                color: var(--text-secondary); 
            }}
            .download-row {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                gap: 12px;
                margin-top: 12px;
            }}
            
            /* Ensure download buttons are clickable */
            .report-sidebar button,
            .report-main button {{
                position: relative;
                z-index: 10;
                pointer-events: auto !important;
            }}
            
            /* Report area buttons (Download Reports, etc.) use theme colors - light in light mode */
            .report-main .stButton > button,
            .report-main .stButton button,
            .report-main button[data-testid="baseButton-primary"],
            .report-main button[data-testid="baseButton-secondary"],
            .report-sidebar .stButton > button,
            .report-sidebar .stButton button,
            .report-sidebar button[data-testid="baseButton-primary"],
            .report-sidebar button[data-testid="baseButton-secondary"],
            .report-main button,
            .report-sidebar button {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border: 1px solid var(--button-border) !important;
                box-shadow: var(--button-shadow) !important;
            }}
            /* Warm Sun hover for buttons in col_actions (Upload another resume, theme toggle) - Boundary-only glow, NO background */
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child button:hover,
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child .stButton > button:hover,
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child button[data-testid]:hover {{
                box-shadow: 0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4) !important;
                border-color: #f5e6a8 !important;
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                background-image: none !important;
            }}
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child button:hover *,
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child .stButton > button:hover *,
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child button[data-testid]:hover * {{
                background-color: transparent !important;
                background: transparent !important;
            }}
            /* Ensure nested text elements remain visible */
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child button:hover div,
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child button:hover span,
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child button:hover p,
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child .stButton > button:hover div,
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child .stButton > button:hover span,
            [data-testid="stHorizontalBlock"]:has(#report-top-actions-marker) > div:last-child .stButton > button:hover p {{
                background-color: transparent !important;
                background: transparent !important;
                color: var(--button-text) !important;
            }}
            .report-main .stButton > button *,
            .report-main .stButton button *,
            .report-main button *,
            .report-sidebar .stButton > button *,
            .report-sidebar .stButton button *,
            .report-sidebar button * {{
                background-color: transparent !important;
                color: var(--button-text) !important;
            }}
            .report-main .stButton > button:hover,
            .report-main .stButton button:hover,
            .report-main button:hover,
            .report-sidebar .stButton > button:hover,
            .report-sidebar .stButton button:hover,
            .report-sidebar button:hover {{
                box-shadow: 0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4) !important;
                border-color: #f5e6a8 !important;
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
            }}
            .report-main .stButton > button:hover *,
            .report-main .stButton button:hover *,
            .report-main button:hover *,
            .report-sidebar .stButton > button:hover *,
            .report-sidebar .stButton button:hover *,
            .report-sidebar button:hover * {{
                background-color: transparent !important;
                color: var(--button-text) !important;
            }}
            
            /* Ensure no overlay blocks buttons */
            .report-main,
            .report-group {{
                position: relative;
                z-index: 1;
            }}
        

            /* ===== Upload Landing Refresh (v2) ===== */
            .hero-copy {{
                position: relative;
                isolation: isolate;
            }}
            .hero-copy::after {{
                content: "";
                position: absolute;
                right: -6%;
                top: -12%;
                width: 230px;
                height: 230px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(20, 184, 166, 0.22) 0%, rgba(20, 184, 166, 0) 72%);
                filter: blur(8px);
                z-index: -1;
                animation: hero-glow-drift 8s ease-in-out infinite alternate;
                pointer-events: none;
            }}
            .hero-title {{
                letter-spacing: -0.02em;
                margin-bottom: 8px;
            }}
            .hero-title span {{
                background: linear-gradient(118deg, #0f6ac9 8%, #14b8a6 92%);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
            }}
            .hero-subtitle {{
                max-width: none;
            }}
            .upload-preview {{
                background: linear-gradient(155deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.88));
                border: 1px solid rgba(148, 163, 184, 0.22);
                border-radius: 24px;
                box-shadow: 0 26px 60px rgba(15, 23, 42, 0.28);
            }}
            .preview-card {{
                border-radius: 18px;
                border: 1px solid rgba(148, 163, 184, 0.16);
                background: linear-gradient(160deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.76)) !important;
            }}

            .landing-extended {{
                margin-top: 34px;
                padding: 0;
                background: transparent;
                border: 0;
                box-shadow: none;
                display: grid;
                gap: 18px;
            }}
            .landing-panel {{
                position: relative;
                overflow: hidden;
                border-radius: 22px;
                border: 1px solid var(--border-light);
                padding: 26px;
                background: linear-gradient(140deg, var(--bg-card), var(--bg-secondary));
                box-shadow: 0 16px 44px var(--shadow);
            }}
            .landing-panel::before {{
                content: "";
                position: absolute;
                inset: 0;
                background: linear-gradient(120deg, rgba(16, 185, 129, 0.06), rgba(34, 211, 238, 0.03) 48%, transparent 70%);
                pointer-events: none;
            }}

            .section-kicker {{
                margin: 0 0 8px;
                text-transform: uppercase;
                letter-spacing: 0.11em;
                font-size: 0.76rem;
                font-weight: 800;
                color: var(--accent-2);
            }}
            .section-title {{
                margin: 0;
                font-size: clamp(1.8rem, 2.8vw, 2.7rem);
                line-height: 1.12;
                color: var(--text-primary);
                max-width: 22ch;
            }}
            .section-subtitle {{
                margin: 12px 0 0;
                color: var(--text-secondary);
                line-height: 1.65;
                max-width: 60ch;
            }}
            .section-head {{
                margin-bottom: 14px;
                position: relative;
                z-index: 1;
            }}
            .section-headline {{
                margin: 0;
                color: var(--text-primary);
                font-size: clamp(1.2rem, 2.1vw, 1.8rem);
                line-height: 1.28;
                max-width: 44ch;
            }}

            .panel-story {{
                display: grid;
                grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
                gap: 22px;
                align-items: stretch;
            }}
            .story-copy {{
                position: relative;
                z-index: 1;
            }}
            .story-chip-row {{
                margin-top: 14px;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}
            .story-chip {{
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 6px 11px;
                background: rgba(15, 23, 42, 0.48);
                border: 1px solid rgba(148, 163, 184, 0.28);
                color: var(--text-primary);
                font-size: 0.78rem;
                font-weight: 700;
            }}
            .story-metric-row {{
                margin-top: 16px;
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 10px;
            }}
            .story-metric {{
                background: linear-gradient(160deg, rgba(15, 23, 42, 0.74), rgba(30, 41, 59, 0.6));
                border: 1px solid rgba(148, 163, 184, 0.22);
                border-radius: 14px;
                padding: 12px 10px;
            }}
            .metric-value {{
                display: block;
                color: #34d399;
                font-weight: 800;
                font-size: 1.28rem;
                line-height: 1;
                margin-bottom: 6px;
            }}
            .metric-label {{
                color: var(--text-secondary);
                font-size: 0.8rem;
                line-height: 1.3;
            }}

            .story-visual {{
                position: relative;
                border-radius: 18px;
                min-height: 230px;
                background: linear-gradient(150deg, rgba(15, 23, 42, 0.72), rgba(30, 41, 59, 0.55));
                border: 1px solid rgba(148, 163, 184, 0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                isolation: isolate;
            }}
            .story-orb {{
                position: absolute;
                border-radius: 999px;
                filter: blur(8px);
                opacity: 0.75;
                pointer-events: none;
            }}
            .orb-a {{
                width: 180px;
                height: 180px;
                top: -34px;
                left: -30px;
                background: radial-gradient(circle, rgba(34, 211, 238, 0.55), rgba(34, 211, 238, 0));
                animation: orb-float-a 7s ease-in-out infinite;
            }}
            .orb-b {{
                width: 170px;
                height: 170px;
                bottom: -42px;
                right: -30px;
                background: radial-gradient(circle, rgba(52, 211, 153, 0.45), rgba(52, 211, 153, 0));
                animation: orb-float-b 8.5s ease-in-out infinite;
            }}
            .story-visual-card {{
                width: min(92%, 320px);
                padding: 16px;
                border-radius: 14px;
                border: 1px solid rgba(148, 163, 184, 0.3);
                background: rgba(15, 23, 42, 0.84);
                box-shadow: 0 16px 40px rgba(15, 23, 42, 0.32);
                position: relative;
                z-index: 1;
            }}
            .visual-title {{
                margin: 0;
                color: var(--text-secondary);
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 700;
            }}
            .visual-score {{
                margin: 8px 0 12px;
                color: #34d399;
                font-size: 1.8rem;
                font-weight: 800;
                line-height: 1;
            }}
            .visual-track {{
                width: 100%;
                height: 10px;
                border-radius: 999px;
                background: rgba(148, 163, 184, 0.2);
                overflow: hidden;
                margin-bottom: 12px;
            }}
            .visual-track > span {{
                display: block;
                height: 100%;
                border-radius: 999px;
                background: linear-gradient(90deg, #34d399, #22d3ee);
            }}
            .visual-lines {{
                display: grid;
                gap: 7px;
            }}
            .visual-lines span {{
                display: block;
                height: 8px;
                border-radius: 999px;
                background: rgba(148, 163, 184, 0.22);
            }}
            .visual-lines span:nth-child(1) {{ width: 94%; }}
            .visual-lines span:nth-child(2) {{ width: 82%; }}
            .visual-lines span:nth-child(3) {{ width: 100%; }}
            .visual-lines span:nth-child(4) {{ width: 70%; }}

            .panel-spectrum {{
                background: linear-gradient(130deg, rgba(15, 23, 42, 0.96), rgba(59, 38, 116, 0.72));
            }}
            .spectrum-grid {{
                position: relative;
                z-index: 1;
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 12px;
            }}
            .spectrum-card {{
                border: 1px solid rgba(148, 163, 184, 0.26);
                border-radius: 14px;
                padding: 14px;
                background: linear-gradient(160deg, rgba(15, 23, 42, 0.64), rgba(30, 41, 59, 0.44));
                transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
            }}
            .spectrum-card:hover {{
                transform: translateY(-3px);
                border-color: rgba(52, 211, 153, 0.55);
                box-shadow: 0 14px 26px rgba(15, 23, 42, 0.34);
            }}
            .spectrum-card h4 {{
                margin: 0 0 6px;
                color: #e2e8f0;
                font-size: 1rem;
            }}
            .spectrum-card p {{
                margin: 0;
                color: rgba(226, 232, 240, 0.82);
                font-size: 0.9rem;
                line-height: 1.5;
            }}

            .panel-walkthrough {{
                background: linear-gradient(145deg, var(--bg-card), rgba(15, 23, 42, 0.9));
            }}
            .walkthrough-grid {{
                position: relative;
                z-index: 1;
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 12px;
            }}
            .walk-card {{
                border: 1px dashed rgba(148, 163, 184, 0.33);
                border-radius: 14px;
                padding: 14px;
                background: rgba(15, 23, 42, 0.34);
            }}
            .walk-index {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 34px;
                height: 34px;
                border-radius: 50%;
                background: rgba(52, 211, 153, 0.16);
                border: 1px solid rgba(52, 211, 153, 0.5);
                color: #34d399;
                font-size: 0.8rem;
                font-weight: 800;
                margin-bottom: 8px;
            }}
            .walk-card h4 {{
                margin: 0 0 6px;
                color: var(--text-primary);
                font-size: 1rem;
            }}
            .walk-card p {{
                margin: 0;
                color: var(--text-secondary);
                font-size: 0.9rem;
                line-height: 1.52;
            }}

            .panel-proof {{
                padding-top: 18px;
                padding-bottom: 18px;
                background: linear-gradient(130deg, rgba(17, 24, 39, 0.95), rgba(30, 41, 59, 0.86));
            }}
            .proof-grid {{
                position: relative;
                z-index: 1;
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 10px;
            }}
            .panel-proof .proof-tile {{
                background: rgba(15, 23, 42, 0.62);
                border: 1px solid rgba(148, 163, 184, 0.24);
                border-radius: 12px;
                padding: 10px 12px;
                min-height: 76px;
            }}
            .panel-proof .proof-label {{
                margin: 0;
                color: #94a3b8;
                font-size: 0.78rem;
            }}
            .panel-proof .proof-value {{
                margin: 6px 0 0;
                color: #e2e8f0;
                font-size: 0.98rem;
                font-weight: 700;
            }}

            .panel-faq {{
                background: linear-gradient(150deg, var(--bg-card), rgba(30, 41, 59, 0.72));
            }}
            .faq-grid {{
                position: relative;
                z-index: 1;
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
            }}
            .faq-card {{
                border: 1px solid rgba(148, 163, 184, 0.24);
                border-radius: 12px;
                padding: 12px 14px;
                background: rgba(15, 23, 42, 0.38);
            }}
            .faq-card h4 {{
                margin: 0;
                color: var(--text-primary);
                font-size: 1rem;
            }}
            .faq-card p {{
                margin: 8px 0 0;
                color: var(--text-secondary);
                line-height: 1.52;
                font-size: 0.9rem;
            }}

            .landing-reveal {{
                opacity: 0;
                transform: translateY(12px);
                animation: landing-reveal-up 0.5s ease forwards;
            }}
            .landing-extended .landing-panel:nth-of-type(1) {{ animation-delay: 0.03s; }}
            .landing-extended .landing-panel:nth-of-type(2) {{ animation-delay: 0.08s; }}
            .landing-extended .landing-panel:nth-of-type(3) {{ animation-delay: 0.13s; }}
            .landing-extended .landing-panel:nth-of-type(4) {{ animation-delay: 0.18s; }}
            .landing-extended .landing-panel:nth-of-type(5) {{ animation-delay: 0.23s; }}

            @keyframes hero-glow-drift {{
                from {{ transform: translate(0, 0); opacity: 0.58; }}
                to {{ transform: translate(24px, -10px); opacity: 0.88; }}
            }}
            @keyframes orb-float-a {{
                0% {{ transform: translate(0, 0); }}
                50% {{ transform: translate(8px, -14px); }}
                100% {{ transform: translate(0, 0); }}
            }}
            @keyframes orb-float-b {{
                0% {{ transform: translate(0, 0); }}
                50% {{ transform: translate(-10px, 12px); }}
                100% {{ transform: translate(0, 0); }}
            }}
            @keyframes landing-reveal-up {{
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}

            @media (max-width: 1200px) {{
                .panel-story {{
                    grid-template-columns: 1fr;
                }}
                .story-visual {{
                    min-height: 200px;
                }}
                .spectrum-grid {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}
                .proof-grid {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}
            }}
            @media (max-width: 820px) {{
                .landing-panel {{
                    padding: 18px;
                    border-radius: 16px;
                }}
                .section-title {{
                    font-size: 1.72rem;
                    max-width: none;
                }}
                .story-metric-row,
                .walkthrough-grid,
                .faq-grid,
                .spectrum-grid,
                .proof-grid {{
                    grid-template-columns: 1fr;
                }}
                .story-chip {{
                    font-size: 0.74rem;
                }}
            }}
            @media (prefers-reduced-motion: reduce) {{
                .hero-copy::after,
                .story-orb,
                .landing-reveal {{
                    animation: none !important;
                    opacity: 1 !important;
                    transform: none !important;
                }}
            }}

            /* Preview card cleanup: keep text/readability consistent in light + dark themes */
            body.theme-light .upload-preview,
            .theme-light .upload-preview {{
                background: linear-gradient(155deg, rgba(241, 245, 249, 0.95), rgba(226, 232, 240, 0.92));
                border-color: rgba(148, 163, 184, 0.36);
            }}
            body.theme-dark .upload-preview,
            .theme-dark .upload-preview {{
                background: linear-gradient(155deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.88));
                border-color: rgba(148, 163, 184, 0.22);
            }}
            body.theme-light .preview-card,
            .theme-light .preview-card {{
                background: linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.95)) !important;
                border-color: rgba(148, 163, 184, 0.36);
            }}
            body.theme-dark .preview-card,
            .theme-dark .preview-card {{
                background: linear-gradient(160deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.76)) !important;
                border-color: rgba(148, 163, 184, 0.3);
            }}
            .preview-card > * {{
                background: transparent !important;
            }}
            .preview-card .list-row,
            .preview-card .list-row span {{
                background: transparent !important;
            }}
            .preview-card .progress-track {{
                background: rgba(148, 163, 184, 0.2) !important;
            }}
            .preview-card .pill {{
                background: rgba(148, 163, 184, 0.18) !important;
            }}

            /* Landing section theme balancing for light mode */
            body.theme-light .panel-spectrum,
            .theme-light .panel-spectrum {{
                background: linear-gradient(130deg, rgba(239, 246, 255, 0.98), rgba(224, 242, 254, 0.96));
            }}
            body.theme-light .spectrum-card,
            .theme-light .spectrum-card {{
                background: linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.95));
                border-color: rgba(148, 163, 184, 0.32);
            }}
            body.theme-light .spectrum-card h4,
            .theme-light .spectrum-card h4 {{
                color: #0f172a;
            }}
            body.theme-light .spectrum-card p,
            .theme-light .spectrum-card p {{
                color: #334155;
            }}
            body.theme-light .panel-proof,
            .theme-light .panel-proof {{
                background: linear-gradient(130deg, rgba(248, 250, 252, 0.98), rgba(241, 245, 249, 0.95));
            }}
            body.theme-light .panel-proof .proof-tile,
            .theme-light .panel-proof .proof-tile {{
                background: rgba(255, 255, 255, 0.94);
                border-color: rgba(148, 163, 184, 0.32);
            }}
            body.theme-light .panel-proof .proof-label,
            .theme-light .panel-proof .proof-label {{
                color: #475569;
            }}
            body.theme-light .panel-proof .proof-value,
            .theme-light .panel-proof .proof-value {{
                color: #0f172a;
            }}
            body.theme-light .story-visual,
            .theme-light .story-visual {{
                background: linear-gradient(150deg, rgba(226, 232, 240, 0.95), rgba(241, 245, 249, 0.94));
                border-color: rgba(148, 163, 184, 0.28);
            }}
            body.theme-light .story-visual-card,
            .theme-light .story-visual-card {{
                background: rgba(255, 255, 255, 0.92);
                border-color: rgba(148, 163, 184, 0.3);
            }}
            body.theme-light .visual-title,
            .theme-light .visual-title {{
                color: #334155;
            }}

            /* ===== Landing Polish (v3): spacing + light-theme readability ===== */
            .landing-extended {{
                margin-top: 42px;
                gap: 24px;
            }}
            .landing-panel {{
                border-radius: 26px;
                padding: 32px 30px;
            }}
            .section-head {{
                margin-bottom: 18px;
            }}
            .panel-story {{
                gap: 26px;
            }}
            .story-metric-row,
            .spectrum-grid,
            .walkthrough-grid,
            .proof-grid,
            .faq-grid {{
                gap: 14px;
            }}
            .spectrum-card,
            .walk-card,
            .faq-card,
            .proof-tile,
            .story-metric {{
                border-radius: 16px;
                padding: 15px;
            }}

            /* Fix preview card nested white boxes and keep semantic accents */
            .preview-card * {{
                background: transparent !important;
            }}
            .preview-card .preview-badge {{
                background: rgba(16, 185, 129, 0.18) !important;
            }}
            .preview-card .pill {{
                background: rgba(148, 163, 184, 0.16) !important;
            }}
            .preview-card .progress-track {{
                background: rgba(148, 163, 184, 0.2) !important;
            }}
            .preview-card .progress-fill {{
                background: linear-gradient(90deg, #34d399, #22d3ee) !important;
            }}

            /* Light mode refinements */
            body.theme-light .landing-panel,
            .theme-light .landing-panel {{
                border-color: rgba(148, 163, 184, 0.32);
                box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
            }}
            body.theme-light .panel-spectrum,
            .theme-light .panel-spectrum {{
                background: linear-gradient(135deg, rgba(238, 242, 255, 0.98), rgba(224, 231, 255, 0.95));
            }}
            body.theme-light .panel-walkthrough,
            .theme-light .panel-walkthrough {{
                background: linear-gradient(135deg, rgba(248, 250, 252, 0.98), rgba(241, 245, 249, 0.95));
            }}
            body.theme-light .panel-faq,
            .theme-light .panel-faq {{
                background: linear-gradient(140deg, rgba(248, 250, 252, 0.98), rgba(226, 232, 240, 0.92));
            }}
            body.theme-light .spectrum-card,
            .theme-light .spectrum-card,
            body.theme-light .walk-card,
            .theme-light .walk-card,
            body.theme-light .faq-card,
            .theme-light .faq-card,
            body.theme-light .story-metric,
            .theme-light .story-metric,
            body.theme-light .panel-proof .proof-tile,
            .theme-light .panel-proof .proof-tile {{
                background: linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94));
                border-color: rgba(148, 163, 184, 0.32);
            }}
            body.theme-light .spectrum-card h4,
            .theme-light .spectrum-card h4,
            body.theme-light .walk-card h4,
            .theme-light .walk-card h4,
            body.theme-light .faq-card h4,
            .theme-light .faq-card h4 {{
                color: #0f172a;
            }}
            body.theme-light .spectrum-card p,
            .theme-light .spectrum-card p,
            body.theme-light .walk-card p,
            .theme-light .walk-card p,
            body.theme-light .faq-card p,
            .theme-light .faq-card p {{
                color: #334155;
            }}
            body.theme-light .story-chip,
            .theme-light .story-chip {{
                background: rgba(255, 255, 255, 0.84);
                border-color: rgba(148, 163, 184, 0.32);
                color: #334155;
            }}
            body.theme-light .metric-label,
            .theme-light .metric-label {{
                color: #475569;
            }}
            body.theme-light .story-visual,
            .theme-light .story-visual {{
                background: linear-gradient(150deg, rgba(226, 232, 240, 0.94), rgba(241, 245, 249, 0.96));
            }}
            body.theme-light .story-visual-card,
            .theme-light .story-visual-card {{
                background: rgba(255, 255, 255, 0.94);
                border-color: rgba(148, 163, 184, 0.34);
                box-shadow: 0 12px 30px rgba(15, 23, 42, 0.09);
            }}
            body.theme-light .visual-title,
            .theme-light .visual-title {{
                color: #475569;
            }}

            body.theme-light .upload-preview,
            .theme-light .upload-preview {{
                background: linear-gradient(155deg, rgba(241, 245, 249, 0.95), rgba(226, 232, 240, 0.9));
                border-color: rgba(148, 163, 184, 0.36);
                box-shadow: 0 16px 36px rgba(15, 23, 42, 0.1);
            }}
            body.theme-light .preview-card,
            .theme-light .preview-card {{
                background: linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.95)) !important;
                border-color: rgba(148, 163, 184, 0.36);
            }}
            body.theme-light .preview-card,
            body.theme-light .preview-card .list-row span,
            body.theme-light .preview-card .text-primary,
            body.theme-light .preview-card .text-secondary,
            .theme-light .preview-card,
            .theme-light .preview-card .list-row span,
            .theme-light .preview-card .text-primary,
            .theme-light .preview-card .text-secondary {{
                color: #0f172a !important;
            }}
            body.theme-light .preview-card .text-muted,
            .theme-light .preview-card .text-muted {{
                color: #475569 !important;
            }}
            body.theme-light .preview-card .list-row,
            .theme-light .preview-card .list-row {{
                border-bottom: 1px solid rgba(148, 163, 184, 0.28);
            }}
            body.theme-light .preview-card .preview-badge,
            .theme-light .preview-card .preview-badge {{
                background: rgba(16, 185, 129, 0.14) !important;
                color: #0f766e !important;
            }}

            @media (max-width: 820px) {{
                .landing-extended {{
                    gap: 18px;
                }}
                .landing-panel {{
                    padding: 22px 18px;
                    border-radius: 18px;
                }}
            }}

            /* ===== Landing Theme-Safe Final Override (v4) ===== */
            [data-testid="stAppViewContainer"] .landing-extended {{
                margin-top: 46px !important;
                gap: 28px !important;
            }}
            [data-testid="stAppViewContainer"] .landing-panel {{
                background: var(--landing-panel-bg) !important;
                border: 1px solid var(--landing-panel-border) !important;
                box-shadow: var(--landing-panel-shadow) !important;
                border-radius: 28px !important;
                padding: 34px 32px !important;
            }}
            [data-testid="stAppViewContainer"] .panel-spectrum {{
                background: var(--landing-spectrum-bg) !important;
            }}
            [data-testid="stAppViewContainer"] .panel-walkthrough {{
                background: var(--landing-walk-bg) !important;
            }}
            [data-testid="stAppViewContainer"] .panel-proof {{
                background: var(--landing-proof-bg) !important;
            }}
            [data-testid="stAppViewContainer"] .panel-faq {{
                background: var(--landing-faq-bg) !important;
            }}
            [data-testid="stAppViewContainer"] .section-title,
            [data-testid="stAppViewContainer"] .section-headline,
            [data-testid="stAppViewContainer"] .spectrum-card h4,
            [data-testid="stAppViewContainer"] .walk-card h4,
            [data-testid="stAppViewContainer"] .faq-card h4,
            [data-testid="stAppViewContainer"] .panel-proof .proof-value {{
                color: var(--landing-heading-text) !important;
            }}
            [data-testid="stAppViewContainer"] .section-subtitle,
            [data-testid="stAppViewContainer"] .metric-label,
            [data-testid="stAppViewContainer"] .spectrum-card p,
            [data-testid="stAppViewContainer"] .walk-card p,
            [data-testid="stAppViewContainer"] .faq-card p,
            [data-testid="stAppViewContainer"] .panel-proof .proof-label {{
                color: var(--landing-body-text) !important;
            }}
            [data-testid="stAppViewContainer"] .story-chip {{
                background: var(--landing-chip-bg) !important;
                border-color: var(--landing-chip-border) !important;
                color: var(--landing-chip-text) !important;
            }}
            [data-testid="stAppViewContainer"] .story-metric,
            [data-testid="stAppViewContainer"] .spectrum-card,
            [data-testid="stAppViewContainer"] .walk-card,
            [data-testid="stAppViewContainer"] .faq-card,
            [data-testid="stAppViewContainer"] .panel-proof .proof-tile {{
                background: var(--landing-card-bg) !important;
                border-color: var(--landing-card-border) !important;
                border-radius: 16px !important;
                padding: 16px !important;
            }}
            [data-testid="stAppViewContainer"] .section-head {{
                margin-bottom: 20px !important;
            }}
            [data-testid="stAppViewContainer"] .story-metric-row,
            [data-testid="stAppViewContainer"] .spectrum-grid,
            [data-testid="stAppViewContainer"] .walkthrough-grid,
            [data-testid="stAppViewContainer"] .proof-grid,
            [data-testid="stAppViewContainer"] .faq-grid {{
                gap: 14px !important;
            }}
            [data-testid="stAppViewContainer"] .story-visual {{
                background: var(--landing-story-visual-bg) !important;
                border-color: var(--landing-panel-border) !important;
                border-radius: 20px !important;
            }}
            [data-testid="stAppViewContainer"] .story-visual-card {{
                background: var(--landing-story-card-bg) !important;
                border-color: var(--landing-story-card-border) !important;
            }}

            /* Preview card inner element cleanup (fix white text boxes) */
            [data-testid="stAppViewContainer"] .preview-card * {{
                background-color: transparent !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card .preview-badge {{
                background-color: rgba(16, 185, 129, 0.18) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card .pill {{
                background-color: rgba(148, 163, 184, 0.2) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card .progress-track {{
                background-color: rgba(148, 163, 184, 0.2) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card .progress-fill {{
                background: linear-gradient(90deg, #34d399, #22d3ee) !important;
            }}

            @media (max-width: 900px) {{
                [data-testid="stAppViewContainer"] .landing-extended {{
                    gap: 20px !important;
                }}
                [data-testid="stAppViewContainer"] .landing-panel {{
                    padding: 22px 18px !important;
                    border-radius: 18px !important;
                }}
            }}

            /* ===== Preview Score Card Final Fix (theme-safe) ===== */
            [data-testid="stAppViewContainer"] .upload-preview {{
                background: var(--preview-shell-bg) !important;
                border-color: var(--preview-shell-border) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card {{
                background: var(--preview-card-bg) !important;
                border-color: var(--preview-card-border) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card,
            [data-testid="stAppViewContainer"] .preview-card .text-primary,
            [data-testid="stAppViewContainer"] .preview-card .text-secondary,
            [data-testid="stAppViewContainer"] .preview-card .list-row span {{
                color: var(--preview-text) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card .text-muted {{
                color: var(--preview-muted) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card * {{
                background-color: transparent !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card .preview-badge {{
                background-color: rgba(16, 185, 129, 0.16) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card .pill {{
                background-color: rgba(148, 163, 184, 0.20) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card .progress-track {{
                background-color: rgba(148, 163, 184, 0.22) !important;
            }}
            [data-testid="stAppViewContainer"] .preview-card .progress-fill {{
                background: linear-gradient(90deg, #34d399, #22d3ee) !important;
            }}
