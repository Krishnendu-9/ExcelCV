            {theme_base_css}
            
            {css_variables}
            
            /* ===== FIX STICKY SIDEBAR (FINAL) ===== */

            [data-testid="stMainBlockContainer"] {{
                overflow: visible !important;
            }}

            [data-testid="stVerticalBlock"] {{
                overflow: visible !important;
                height: auto !important;
            }}

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
            .stFileUploader button,
            .stFileUploader button *,
            .stFileUploader [data-baseweb="button"],
            .stFileUploader [data-baseweb="button"] * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-border) !important;
            }}
            .stFileUploader button,
            .stFileUploader [data-baseweb="button"] {{
                border: 1px solid var(--button-border) !important;
                border-radius: 8px !important;
                padding: 8px 16px !important;
                font-weight: 600 !important;
                min-height: 36px !important;
                box-shadow: var(--button-shadow) !important;
            }}
            .stFileUploader button:hover,
            .stFileUploader [data-baseweb="button"]:hover,
            .stFileUploader button:hover *,
            .stFileUploader [data-baseweb="button"]:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
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
                border-radius: 12px;
                padding: 4px 6px;
                line-height: 1;
            }}
            body.theme-dark .site-logo-shell {{
                background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(244, 249, 255, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.7);
                box-shadow: 0 8px 18px rgba(0, 0, 0, 0.28);
            }}
            .site-logo-wordmark {{
                height: 50px;
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
                gap: 12px;
                flex-wrap: nowrap;
                padding-top: 4px;
            }}
            .site-nav-item {{
                display: inline-flex;
                align-items: center;
                padding: 10px 16px;
                border-radius: 999px;
                border: 1px solid var(--border-color);
                background: var(--bg-card);
                color: var(--text-secondary);
                font-size: 1.04rem;
                font-weight: 700;
                line-height: 1;
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
                    padding: 3px 5px;
                }}
                .site-logo-wordmark {{
                    height: 44px;
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
                    padding: 2px 4px;
                }}
                .site-logo-wordmark {{
                    height: 38px;
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
            
            /* Style file uploader (Upload PDF/browse file) - LIGHT MODE */
            body.theme-light .stFileUploader {{
                border: 1px solid rgba(0, 0, 0, 0.1) !important;
                border-radius: 12px;
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

            /* Upload page */
            .hero-shell {{
                background: linear-gradient(135deg, var(--bg-hero), var(--bg-secondary));
                border: 1px solid var(--border-light);
                border-radius: 24px;
                padding: 40px 40px 32px;
                box-shadow: 0 30px 90px var(--shadow-lg);
                margin-top: 16px;
            }}
            .hero-copy {{
                padding-right: 12px;
                margin-top: 0 !important;
            }}
            .eyebrow {{
                text-transform: uppercase;
                letter-spacing: 0.14em;
                font-size: 0.75rem;
                color: var(--accent-2);
                margin-bottom: 12px;
                font-weight: 700;
            }}
            .hero-title {{
                font-size: 3.5rem;
                line-height: 1.05;
                margin: 0 0 6px;
                font-weight: 900;
                color: var(--text-primary);
            }}
            .hero-title span {{ 
                color: var(--accent); 
            }}
            .hero-subtitle {{
                color: var(--text-secondary);
                font-size: 1.1rem;
                margin-bottom: 6px;
                line-height: 1.6;
            }}
            .hero-chip-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin: 6px 0 0;
            }}
            .hero-chip {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                border-radius: 999px;
                padding: 6px 11px;
                background: linear-gradient(145deg, var(--bg-card), var(--bg-secondary));
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.01em;
                margin: 0;
            }}
            .privacy-note {{
                color: var(--text-secondary);
                font-size: 0.85rem;
                margin-top: 8px;
                margin-bottom: 12px;
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
            /* Keep hero text and scorecard aligned higher on first fold. */
            [data-testid="stHorizontalBlock"]:has(.hero-copy) {{
                margin-top: -44px !important;
                align-items: flex-start !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.hero-copy) > div {{
                margin-top: 0 !important;
                padding-top: 0 !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.hero-copy) > div:last-child [data-testid="stVerticalBlock"] > div {{
                margin-top: 0 !important;
                margin-bottom: 6px !important;
            }}
            @media (max-width: 980px) {{
                [data-testid="stHorizontalBlock"]:has(.hero-copy) {{
                    margin-top: -18px !important;
                }}
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
                .landing-extended {{
                    padding: 22px;
                }}
            }}
            @media (max-width: 768px) {{
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
                overflow-x: visible !important;

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
            .score-number {{ 
                font-size: 2.8rem; 
                font-weight: 900; 
                color: #fcd34d; 
            }}
            .score-number span {{ 
                font-size: 1rem; 
                color: var(--text-secondary); 
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
            .detail-head h3 {{ 
                margin: 0; 
            }}
            /* Shared body area for all report sections (Quantifying Impact, Spelling & Grammar, Strengths, etc.) - same as Suggestions */
            .section-body {{
                padding: 0 0 4px 0;
                margin: 0;
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
                width: 220px;
                height: 220px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(56, 189, 248, 0.24) 0%, rgba(56, 189, 248, 0) 72%);
                filter: blur(6px);
                z-index: -1;
                animation: hero-glow-drift 8s ease-in-out infinite alternate;
                pointer-events: none;
            }}
            .hero-title {{
                letter-spacing: -0.02em;
                margin-bottom: 10px;
            }}
            .hero-title span {{
                background: linear-gradient(90deg, #34d399, #22d3ee);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
            }}
            .hero-subtitle {{
                max-width: 58ch;
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
