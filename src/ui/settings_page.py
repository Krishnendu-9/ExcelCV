"""Settings page - profile, preferences, notifications, login info, account deletion."""

from datetime import timezone

import streamlit as st

from src.auth_utils import (
    get_session_user,
    hash_password,
    logout_user,
    verify_password,
)
from src.database import (
    CV,
    Analysis,
    Comparison,
    PasswordResetToken,
    User,
    get_db,
)

# ─── DB helpers ────────────────────────────────────────────────────────────────


def _load_db_user(user_id: str):
    db = get_db()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def _get_user_stats(user_id: str) -> dict[str, int]:
    """Lightweight counts to power the profile card stats row."""
    db = get_db()
    try:
        return {
            "cvs": db.query(CV).filter(CV.user_id == user_id).count(),
            "analyses": db.query(Analysis).filter(Analysis.user_id == user_id).count(),
            "comparisons": db.query(Comparison).filter(Comparison.user_id == user_id).count(),
        }
    finally:
        db.close()


def _change_email(user_id: str, current_password: str, new_email: str) -> tuple[bool, str]:
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found."
        if user.hashed_password == "GOOGLE_OAUTH":
            return False, "Google-only accounts cannot change email here."
        if not verify_password(current_password, user.hashed_password):
            return False, "Current password is incorrect."
        cleaned = new_email.lower().strip()
        if db.query(User).filter(User.email == cleaned).first():
            return False, "This email is already in use."
        user.email = cleaned
        db.commit()
        return True, "Email updated successfully."
    except Exception as exc:
        db.rollback()
        return False, f"Could not update email: {exc}"
    finally:
        db.close()


def _change_password(user_id: str, current_password: str, new_password: str) -> tuple[bool, str]:
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found."
        if user.hashed_password == "GOOGLE_OAUTH":
            return False, "Google-only accounts cannot change password here."
        if not verify_password(current_password, user.hashed_password):
            return False, "Current password is incorrect."
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters."
        user.hashed_password = hash_password(new_password)
        db.commit()
        return True, "Password updated successfully."
    except Exception as exc:
        db.rollback()
        return False, f"Could not update password: {exc}"
    finally:
        db.close()


def _disconnect_google(user_id: str) -> tuple[bool, str]:
    """Unlink the Google identity. Refuses if it would lock the user out (no password set)."""
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found."
        if user.hashed_password == "GOOGLE_OAUTH":
            return False, "Set a password first — disconnecting Google would lock you out."
        if not user.google_id:
            return False, "Google account is not connected."
        user.google_id = None
        db.commit()
        return True, "Google account disconnected."
    except Exception as exc:
        db.rollback()
        return False, f"Could not disconnect Google: {exc}"
    finally:
        db.close()


def _delete_account(user_id: str) -> tuple[bool, str]:
    db = get_db()
    try:
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete()
        db.query(Analysis).filter(Analysis.user_id == user_id).delete()
        db.query(CV).filter(CV.user_id == user_id).delete()
        db.query(Comparison).filter(Comparison.user_id == user_id).delete()
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found."
        db.delete(user)
        db.commit()
        return True, "Account deleted."
    except Exception as exc:
        db.rollback()
        return False, f"Could not delete account: {exc}"
    finally:
        db.close()


# ─── Inline SVG icons (Lucide-style) ───────────────────────────────────────────

# Each returns the inner <path>/<polyline>/etc. The wrapper supplies <svg>.
_ICON_GEAR = (
    "<circle cx='12' cy='12' r='3'/>"
    "<path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 "
    "1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 "
    "1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 "
    "1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 "
    "1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 "
    "0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'/>"
)
_ICON_USER = "<path d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/><circle cx='12' cy='7' r='4'/>"
_ICON_BELL = (
    "<path d='M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9'/><path d='M13.73 21a2 2 0 0 1-3.46 0'/>"
)
_ICON_SLIDERS = (
    "<line x1='4' x2='4' y1='21' y2='14'/><line x1='4' x2='4' y1='10' y2='3'/>"
    "<line x1='12' x2='12' y1='21' y2='12'/><line x1='12' x2='12' y1='8' y2='3'/>"
    "<line x1='20' x2='20' y1='21' y2='16'/><line x1='20' x2='20' y1='12' y2='3'/>"
    "<line x1='2' x2='6' y1='14' y2='14'/><line x1='10' x2='14' y1='8' y2='8'/><line x1='18' x2='22' y1='16' y2='16'/>"
)
_ICON_LOCK = (
    "<rect width='18' height='11' x='3' y='11' rx='2' ry='2'/><path d='M7 11V7a5 5 0 0 1 10 0v4'/>"
)
_ICON_TRASH = (
    "<polyline points='3 6 5 6 21 6'/>"
    "<path d='M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6'/>"
    "<path d='M10 11v6M14 11v6'/>"
    "<path d='M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2'/>"
)
_ICON_CHECK = "<polyline points='20 6 9 17 4 12'/>"
_ICON_MAIL = (
    "<rect width='20' height='16' x='2' y='4' rx='2'/>"
    "<path d='m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7'/>"
)
_ICON_KEY = (
    "<circle cx='7.5' cy='15.5' r='5.5'/>"
    "<path d='m21 2-9.6 9.6'/>"
    "<path d='m15.5 7.5 3 3L22 7l-3-3'/>"
)


def _svg(inner: str, *, size: int = 18) -> str:
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 24 24' "
        f"fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
        f"{inner}</svg>"
    )


def _section_header(icon_svg: str, title: str, subtitle: str = "", *, danger: bool = False) -> str:
    icon_cls = "settings-sec-icon settings-sec-icon-danger" if danger else "settings-sec-icon"
    title_cls = "settings-sec-title-danger" if danger else "settings-sec-title"
    sub_html = f'<p class="settings-sec-sub">{subtitle}</p>' if subtitle else ""
    return (
        f'<div class="settings-sec-header">'
        f'  <span class="{icon_cls}">{icon_svg}</span>'
        f'  <div class="settings-sec-title-wrap">'
        f'    <p class="{title_cls}">{title}</p>'
        f"    {sub_html}"
        f"  </div>"
        f"</div>"
    )


# ─── Page renderer ─────────────────────────────────────────────────────────────


def render_settings_page() -> None:
    user = get_session_user()
    if not user:
        st.warning("Please sign in to view your settings.")
        return

    # Frontend-only styles for homepage-like settings presentation.
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell {
            display: flex !important;
            flex-direction: column !important;
            gap: 14px !important;
            margin-top: -72px !important;
            max-width: 1100px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .landing-clean-tag {
            display: none !important;
        }
        [data-testid="stAppViewContainer"] .settings-main-head {
            margin-top: 0 !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.45rem;
        }
        [data-testid="stAppViewContainer"] .settings-main-head .landing-clean-title {
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
        }
        [data-testid="stAppViewContainer"] .settings-main-head .landing-clean-title svg {
            width: 28px;
            height: 28px;
            color: var(--text-primary);
            opacity: 0.85;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_sec_profile,
        [data-testid="stAppViewContainer"] .st-key-settings_sec_notifications,
        [data-testid="stAppViewContainer"] .st-key-settings_sec_preferences,
        [data-testid="stAppViewContainer"] .st-key-settings_sec_login,
        [data-testid="stAppViewContainer"] .st-key-settings_sec_delete {
            background: linear-gradient(160deg, var(--bg-card), var(--bg-secondary)) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 18px !important;
            padding: 22px 24px !important;
            box-shadow: 0 12px 24px var(--shadow) !important;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_sec_delete {
            border-color: rgba(239, 68, 68, 0.34) !important;
            background: linear-gradient(160deg, rgba(239, 68, 68, 0.06), rgba(239, 68, 68, 0.02)) !important;
        }

        /* ─── Section header (icon + title + subtitle) ─── */
        [data-testid="stAppViewContainer"] .settings-sec-header {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin: 0 0 0.85rem;
        }
        [data-testid="stAppViewContainer"] .settings-sec-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: rgba(37, 99, 235, 0.10);
            color: #2563eb;
            flex-shrink: 0;
        }
        [data-testid="stAppViewContainer"] .settings-sec-icon-danger {
            background: rgba(239, 68, 68, 0.10);
            color: #dc2626;
        }
        [data-testid="stAppViewContainer"] .settings-sec-title-wrap {
            display: flex;
            flex-direction: column;
            gap: 2px;
            flex: 1;
            min-width: 0;
        }
        [data-testid="stAppViewContainer"] .settings-sec-title {
            color: var(--text-primary);
            font-size: 1.12rem;
            font-weight: 700;
            margin: 0;
        }
        [data-testid="stAppViewContainer"] .settings-sec-title-danger {
            color: #ef4444;
            font-size: 1.12rem;
            font-weight: 700;
            margin: 0;
        }
        [data-testid="stAppViewContainer"] .settings-sec-sub {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin: 0;
            line-height: 1.5;
        }

        /* ─── Profile card: single horizontal row (avatar | info | stats) ─── */
        [data-testid="stAppViewContainer"] .settings-profile-row {
            display: flex;
            align-items: center;
            gap: 18px;
            flex-wrap: wrap;
        }
        [data-testid="stAppViewContainer"] .settings-profile-avatar {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2563eb, #0d9488);
            color: #ffffff;
            font-size: 1.35rem;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            letter-spacing: 0.02em;
        }
        [data-testid="stAppViewContainer"] .settings-profile-info {
            flex: 1 1 220px;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        [data-testid="stAppViewContainer"] .settings-profile-name {
            margin: 0;
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-primary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        [data-testid="stAppViewContainer"] .settings-profile-meta {
            margin: 0;
            font-size: 0.86rem;
            color: var(--text-secondary);
        }
        [data-testid="stAppViewContainer"] .settings-profile-stats {
            display: flex;
            gap: 24px;
            padding-left: 22px;
            border-left: 1px solid var(--border-light, var(--border-color));
            margin-left: auto;
            flex-shrink: 0;
        }
        [data-testid="stAppViewContainer"] .settings-profile-stat {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        [data-testid="stAppViewContainer"] .settings-profile-stat-num {
            font-size: 1.28rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.1;
        }
        [data-testid="stAppViewContainer"] .settings-profile-stat-label {
            font-size: 0.7rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 600;
            white-space: nowrap;
        }
        /* Equal-height side-by-side cards (Notifications + Preferences) */
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell [data-testid="stHorizontalBlock"]:has(.st-key-settings_sec_notifications) {
            align-items: stretch !important;
            gap: 14px !important;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .st-key-settings_sec_notifications,
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .st-key-settings_sec_preferences {
            height: 100% !important;
        }

        /* ─── Field labels + email row ─── */
        [data-testid="stAppViewContainer"] .settings-field-label {
            color: var(--text-primary);
            font-size: 0.92rem;
            font-weight: 600;
            margin: 0.9rem 0 0.4rem;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
        }
        [data-testid="stAppViewContainer"] .settings-email-row {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin: 0 0 0.75rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        [data-testid="stAppViewContainer"] .settings-email-row b {
            color: var(--text-primary);
        }

        /* Verified pill */
        [data-testid="stAppViewContainer"] .settings-verified {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 2px 8px;
            border-radius: 999px;
            background: rgba(34, 197, 94, 0.10);
            border: 1px solid rgba(34, 197, 94, 0.25);
            color: #16a34a;
            font-size: 0.72rem;
            font-weight: 600;
        }
        [data-testid="stAppViewContainer"] .settings-verified svg {
            width: 12px;
            height: 12px;
        }

        /* Google chip + disconnect button */
        [data-testid="stAppViewContainer"] .settings-google-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            background: rgba(34, 197, 94, 0.09);
            border: 1px solid rgba(34, 197, 94, 0.25);
            border-radius: 0.55rem;
            padding: 0.5rem 0.9rem;
            font-size: 0.875rem;
            color: var(--text-primary);
            margin-bottom: 0.75rem;
        }
        [data-testid="stAppViewContainer"] .settings-google-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            flex-shrink: 0;
        }
        /* ─── Variant: destructive (red-tinted ghost) — unified pattern ───
           Uses the doubled-class [class*="..."][class*="..."] selector pattern
           (same as list_pages.py's lp_action_delete_ / lp_confirm_yes_ rules) to
           guarantee specificity wins over the base ghost rule's hover declaration,
           regardless of declaration order. */
        [data-testid="stAppViewContainer"] [class*="st-key-settings_disconnect_google"][class*="st-key-settings_disconnect_google"] button,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_disconnect_google"][class*="st-key-settings_disconnect_google"] button:focus,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_disconnect_google"][class*="st-key-settings_disconnect_google"] button:focus-visible,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_disconnect_google"][class*="st-key-settings_disconnect_google"] [data-baseweb="button"],
        [data-testid="stAppViewContainer"] [class*="st-key-settings_delete_btn"][class*="st-key-settings_delete_btn"] button,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_delete_btn"][class*="st-key-settings_delete_btn"] button:focus,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_delete_btn"][class*="st-key-settings_delete_btn"] button:focus-visible,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_delete_btn"][class*="st-key-settings_delete_btn"] [data-baseweb="button"],
        [data-testid="stAppViewContainer"] [class*="st-key-settings_do_delete"][class*="st-key-settings_do_delete"] button,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_do_delete"][class*="st-key-settings_do_delete"] button:focus,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_do_delete"][class*="st-key-settings_do_delete"] button:focus-visible,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_do_delete"][class*="st-key-settings_do_delete"] [data-baseweb="button"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            color: #ef4444 !important;
            border: 1px solid rgba(239, 68, 68, 0.45) !important;
            box-shadow: none !important;
            filter: none !important;
            font-weight: 600 !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-settings_disconnect_google"][class*="st-key-settings_disconnect_google"] button *,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_disconnect_google"][class*="st-key-settings_disconnect_google"] button p,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_disconnect_google"][class*="st-key-settings_disconnect_google"] button span,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_delete_btn"][class*="st-key-settings_delete_btn"] button *,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_delete_btn"][class*="st-key-settings_delete_btn"] button p,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_delete_btn"][class*="st-key-settings_delete_btn"] button span,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_do_delete"][class*="st-key-settings_do_delete"] button *,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_do_delete"][class*="st-key-settings_do_delete"] button p,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_do_delete"][class*="st-key-settings_do_delete"] button span {
            background: transparent !important;
            background-color: transparent !important;
            color: #ef4444 !important;
        }
        /* ── Red hover for Disconnect Google + Delete Account + Yes Delete ── */
        [data-testid="stAppViewContainer"] [class*="st-key-settings_disconnect_google"][class*="st-key-settings_disconnect_google"] button:hover,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_delete_btn"][class*="st-key-settings_delete_btn"] button:hover,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_do_delete"][class*="st-key-settings_do_delete"] button:hover {
            background: rgba(239, 68, 68, 0.12) !important;
            background-color: rgba(239, 68, 68, 0.12) !important;
            border-color: rgba(239, 68, 68, 0.65) !important;
            color: #b91c1c !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-settings_disconnect_google"][class*="st-key-settings_disconnect_google"] button:hover *,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_delete_btn"][class*="st-key-settings_delete_btn"] button:hover *,
        [data-testid="stAppViewContainer"] [class*="st-key-settings_do_delete"][class*="st-key-settings_do_delete"] button:hover * {
            color: #b91c1c !important;
        }

        /* ─── Unified ghost-button style for ALL settings buttons ───
           Matches the My CVs page button language (transparent bg, theme text,
           subtle border, soft wash on hover). The base rule wins on specificity
           via the doubled .st-key-settings_page_shell.st-key-settings_page_shell
           selector so it outranks base_theme.css.tpl's global filled-button rules.
           Variant rules below this block tint for destructive (red) and positive
           (blue) intents. */
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell.st-key-settings_page_shell button,
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell.st-key-settings_page_shell button:focus,
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell.st-key-settings_page_shell button:focus-visible,
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell.st-key-settings_page_shell [data-baseweb="button"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-color) !important;
            box-shadow: none !important;
            font-weight: 600 !important;
            filter: none !important;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell.st-key-settings_page_shell button *,
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell.st-key-settings_page_shell button p,
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell.st-key-settings_page_shell button span {
            background: transparent !important;
            background-color: transparent !important;
            color: inherit !important;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell.st-key-settings_page_shell button:hover {
            background: rgba(37, 99, 235, 0.06) !important;
            background-color: rgba(37, 99, 235, 0.06) !important;
            border-color: rgba(37, 99, 235, 0.40) !important;
            color: #1d4ed8 !important;
        }

        /* Login button icons (envelope / key) — both buttons share neutral ghost style */
        [data-testid="stAppViewContainer"] .st-key-settings_open_email button,
        [data-testid="stAppViewContainer"] .st-key-settings_open_pass button {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.5rem !important;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_open_email button::before,
        [data-testid="stAppViewContainer"] .st-key-settings_open_pass button::before {
            content: "";
            display: inline-block;
            width: 16px;
            height: 16px;
            background-color: currentColor;
            -webkit-mask-repeat: no-repeat;
            -webkit-mask-position: center;
            -webkit-mask-size: 16px 16px;
            mask-repeat: no-repeat;
            mask-position: center;
            mask-size: 16px 16px;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_open_email button::before {
            -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='20' height='16' x='2' y='4' rx='2'/%3E%3Cpath d='m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7'/%3E%3C/svg%3E");
            mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='20' height='16' x='2' y='4' rx='2'/%3E%3Cpath d='m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7'/%3E%3C/svg%3E");
        }
        [data-testid="stAppViewContainer"] .st-key-settings_open_pass button::before {
            -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='7.5' cy='15.5' r='5.5'/%3E%3Cpath d='m21 2-9.6 9.6'/%3E%3Cpath d='m15.5 7.5 3 3L22 7l-3-3'/%3E%3C/svg%3E");
            mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='7.5' cy='15.5' r='5.5'/%3E%3Cpath d='m21 2-9.6 9.6'/%3E%3Cpath d='m15.5 7.5 3 3L22 7l-3-3'/%3E%3C/svg%3E");
        }

        /* ─── Variant: positive action (blue-tinted ghost) — Save Email / Save Password ─── */
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .st-key-settings_save_email button,
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .st-key-settings_save_pass button {
            color: #2563eb !important;
            border-color: rgba(37, 99, 235, 0.45) !important;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .st-key-settings_save_email button *,
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .st-key-settings_save_pass button * {
            color: #2563eb !important;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .st-key-settings_save_email button:hover,
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .st-key-settings_save_pass button:hover {
            background: rgba(37, 99, 235, 0.10) !important;
            background-color: rgba(37, 99, 235, 0.10) !important;
            border-color: rgba(37, 99, 235, 0.65) !important;
            color: #1d4ed8 !important;
        }

        /* ─── Notifications: stacked toggle rows ─── */
        [data-testid="stAppViewContainer"] .settings-notif-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            padding: 0.55rem 0;
            border-top: 1px solid var(--border-light, var(--border-color));
        }
        [data-testid="stAppViewContainer"] .settings-notif-row:first-of-type {
            border-top: 0;
            padding-top: 0;
        }
        [data-testid="stAppViewContainer"] .settings-notif-text {
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 0;
        }
        [data-testid="stAppViewContainer"] .settings-notif-title {
            margin: 0;
            color: var(--text-primary);
            font-size: 0.95rem;
            font-weight: 600;
        }
        [data-testid="stAppViewContainer"] .settings-notif-desc {
            margin: 0;
            color: var(--text-secondary);
            font-size: 0.82rem;
            line-height: 1.45;
        }

        /* ─── Divider ─── */
        [data-testid="stAppViewContainer"] .settings-divider {
            border: none;
            border-top: 1px solid var(--border-light, var(--border-color));
            margin: 1rem 0;
            opacity: 0.6;
        }

        /* ─── Delete confirm panel ─── */
        [data-testid="stAppViewContainer"] .settings-delete-confirm {
            display: flex;
            align-items: flex-start;
            gap: 0.85rem;
            padding: 0.9rem 1rem;
            margin: 0.4rem 0 0.9rem;
            background: linear-gradient(180deg, rgba(239, 68, 68, 0.08), rgba(239, 68, 68, 0.02));
            border: 1px solid rgba(239, 68, 68, 0.32);
            border-radius: 12px;
        }
        [data-testid="stAppViewContainer"] .settings-delete-confirm-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 999px;
            background: rgba(239, 68, 68, 0.22);
            color: #dc2626;
            font-weight: 800;
            flex-shrink: 0;
        }
        [data-testid="stAppViewContainer"] .settings-delete-confirm-title {
            margin: 0;
            font-weight: 700;
            color: var(--text-primary);
            font-size: 0.95rem;
        }
        [data-testid="stAppViewContainer"] .settings-delete-confirm-sub {
            margin: 0.2rem 0 0;
            color: var(--text-secondary);
            font-size: 0.84rem;
            line-height: 1.5;
        }

        /* (Delete Account + Yes/Cancel buttons inherit the unified destructive
           ghost style defined above near .st-key-settings_disconnect_google.) */

        @media (max-width: 820px) {
            [data-testid="stAppViewContainer"] .st-key-settings_page_shell {
                margin-top: -38px !important;
                max-width: 100% !important;
            }
            [data-testid="stAppViewContainer"] .settings-main-head {
                margin-top: 0 !important;
            }
            [data-testid="stAppViewContainer"] .st-key-settings_sec_profile,
            [data-testid="stAppViewContainer"] .st-key-settings_sec_notifications,
            [data-testid="stAppViewContainer"] .st-key-settings_sec_preferences,
            [data-testid="stAppViewContainer"] .st-key-settings_sec_login,
            [data-testid="stAppViewContainer"] .st-key-settings_sec_delete {
                padding: 16px 14px !important;
            }
            [data-testid="stAppViewContainer"] .settings-profile-row {
                gap: 12px;
            }
            [data-testid="stAppViewContainer"] .settings-profile-avatar {
                width: 52px;
                height: 52px;
                font-size: 1.25rem;
            }
            /* Stats wrap below avatar+info on narrow screens (avoid horizontal overflow) */
            [data-testid="stAppViewContainer"] .settings-profile-stats {
                gap: 18px;
                padding-left: 0;
                border-left: 0;
                margin-left: 0;
                margin-top: 14px;
                padding-top: 14px;
                border-top: 1px solid var(--border-light, var(--border-color));
                width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="settings_page_shell"):
        st.markdown(
            f"""
            <div class="landing-clean-head settings-main-head">
                <h2 class="landing-clean-title">{_svg(_ICON_GEAR, size=26)}Account & preferences</h2>
                <p class="landing-clean-subtitle">
                    Profile, security, and notification preferences.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_id = user.get("id", "")
        user_email = user.get("email", "")
        user_name = user.get("full_name") or user_email.split("@")[0]

        db_user = _load_db_user(user_id)
        is_google = bool(db_user and db_user.google_id)
        is_password_account = bool(db_user and db_user.hashed_password != "GOOGLE_OAUTH")
        member_since = db_user.created_at if db_user and db_user.created_at else None
        stats = _get_user_stats(user_id)

        # ─── Profile card ─────────────────────────────────────────────────────
        initials = "".join([part[0] for part in user_name.split()[:2] if part]).upper() or "U"
        member_since_label = "—"
        if member_since:
            ms = member_since if member_since.tzinfo else member_since.replace(tzinfo=timezone.utc)
            member_since_label = ms.strftime("%b %Y")

        with st.container(key="settings_sec_profile"):
            st.markdown(
                f"""
                <div class="settings-profile-row">
                    <div class="settings-profile-avatar">{initials}</div>
                    <div class="settings-profile-info">
                        <p class="settings-profile-name">{user_name}</p>
                        <p class="settings-profile-meta">{user_email} &middot; Member since {member_since_label}</p>
                    </div>
                    <div class="settings-profile-stats">
                        <div class="settings-profile-stat">
                            <span class="settings-profile-stat-num">{stats["cvs"]}</span>
                            <span class="settings-profile-stat-label">Saved CVs</span>
                        </div>
                        <div class="settings-profile-stat">
                            <span class="settings-profile-stat-num">{stats["analyses"]}</span>
                            <span class="settings-profile-stat-label">Analyses</span>
                        </div>
                        <div class="settings-profile-stat">
                            <span class="settings-profile-stat-num">{stats["comparisons"]}</span>
                            <span class="settings-profile-stat-label">Comparisons</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ─── Notifications + Preferences side-by-side ─────────────────────────
        notif_col, pref_col = st.columns(2, gap="small")
        with notif_col:
            with st.container(key="settings_sec_notifications"):
                st.markdown(
                    _section_header(
                        _svg(_ICON_BELL),
                        "Notifications",
                        "Choose what we email you about. Toggle anything off to stop those messages.",
                    ),
                    unsafe_allow_html=True,
                )

                notif_options = [
                    (
                        "settings_notif_career",
                        "Career tips",
                        "Weekly resume best-practices and job-search advice.",
                    ),
                    (
                        "settings_notif_product",
                        "Product updates",
                        "New features, templates, and improvements.",
                    ),
                    (
                        "settings_notif_security",
                        "Security alerts",
                        "Sign-ins from new devices and important account events.",
                    ),
                ]
                for key, title, desc in notif_options:
                    row_l, row_r = st.columns([5, 1])
                    with row_l:
                        st.markdown(
                            f"""
                            <div class="settings-notif-text" style="padding-top:0.35rem;">
                                <p class="settings-notif-title">{title}</p>
                                <p class="settings-notif-desc">{desc}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with row_r:
                        st.checkbox(
                            title,
                            key=key,
                            value=st.session_state.get(key, key == "settings_notif_security"),
                            label_visibility="collapsed",
                        )

        with pref_col:
            with st.container(key="settings_sec_preferences"):
                st.markdown(
                    _section_header(
                        _svg(_ICON_SLIDERS),
                        "Preferences",
                        "Personalize how ExcelCV looks.",
                    ),
                    unsafe_allow_html=True,
                )
                current_theme = st.session_state.get("theme", "light")
                options = ["light", "dark"]
                chosen = st.radio(
                    "Theme",
                    options=options,
                    index=options.index(current_theme) if current_theme in options else 0,
                    horizontal=True,
                    key="settings_theme_radio",
                    format_func=lambda v: "Light" if v == "light" else "Dark",
                )
                if chosen != current_theme:
                    st.session_state["theme"] = chosen
                    st.rerun()

        # ─── Login card ───────────────────────────────────────────────────────
        with st.container(key="settings_sec_login"):
            st.markdown(
                _section_header(
                    _svg(_ICON_LOCK),
                    "Login & security",
                    "Manage how you sign in to ExcelCV.",
                ),
                unsafe_allow_html=True,
            )

            if is_google:
                st.markdown(
                    '<p class="settings-field-label">Google Account</p>', unsafe_allow_html=True
                )
                st.markdown(
                    f'<div class="settings-google-chip">'
                    f'<span class="settings-google-dot"></span>'
                    f"Connected &mdash; {user_email}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                # Only show the disconnect button when the user also has a password set,
                # otherwise disconnecting would lock them out of the account entirely.
                if is_password_account:
                    dc_col, _ = st.columns([1, 3])
                    with dc_col:
                        if st.button(
                            "Disconnect Google", key="settings_disconnect_google", width="stretch"
                        ):
                            ok, msg = _disconnect_google(user_id)
                            (st.success if ok else st.error)(msg)
                            if ok:
                                st.rerun()
                else:
                    st.caption(
                        "Set a password below before disconnecting Google — otherwise you'll be locked out."
                    )
                st.markdown('<hr class="settings-divider"/>', unsafe_allow_html=True)

            st.markdown(
                '<p class="settings-field-label">Email &amp; Password</p>', unsafe_allow_html=True
            )
            verified_pill = (
                f'<span class="settings-verified">{_svg(_ICON_CHECK, size=12)}Verified</span>'
            )
            st.markdown(
                f'<p class="settings-email-row">Your account email: <b>{user_email}</b>{verified_pill}</p>',
                unsafe_allow_html=True,
            )

            panel = st.session_state.get("settings_panel", "")

            if not panel:
                c_e, c_p, _ = st.columns([1, 1, 2])
                with c_e:
                    if st.button("Change Email", key="settings_open_email", width="stretch"):
                        st.session_state["settings_panel"] = "email"
                        st.rerun()
                with c_p:
                    if st.button("Change Password", key="settings_open_pass", width="stretch"):
                        st.session_state["settings_panel"] = "password"
                        st.rerun()

            elif panel == "email":
                st.markdown('<hr class="settings-divider"/>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="settings-field-label">Change Email</p>', unsafe_allow_html=True
                )
                if not is_password_account:
                    st.info("Google-only accounts cannot change email here.")
                    if st.button("Cancel", key="settings_cancel_email_info"):
                        st.session_state.pop("settings_panel", None)
                        st.rerun()
                else:
                    new_email = st.text_input(
                        "New email address", key="settings_new_email", placeholder="new@example.com"
                    )
                    cur_pass = st.text_input(
                        "Current password", type="password", key="settings_cur_pass_email"
                    )
                    fc1, fc2, _ = st.columns([1, 1, 2])
                    with fc1:
                        if st.button(
                            "Save Email", key="settings_save_email", type="primary", width="stretch"
                        ):
                            if new_email and cur_pass:
                                ok, msg = _change_email(user_id, cur_pass, new_email)
                                if ok:
                                    st.session_state["user"]["email"] = new_email.lower().strip()
                                    st.session_state.pop("settings_panel", None)
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.warning("Please fill in all fields.")
                    with fc2:
                        if st.button("Cancel", key="settings_cancel_email", width="stretch"):
                            st.session_state.pop("settings_panel", None)
                            st.rerun()

            elif panel == "password":
                st.markdown('<hr class="settings-divider"/>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="settings-field-label">Change Password</p>', unsafe_allow_html=True
                )
                if not is_password_account:
                    st.info("Google-only accounts cannot change password here.")
                    if st.button("Cancel", key="settings_cancel_pass_info"):
                        st.session_state.pop("settings_panel", None)
                        st.rerun()
                else:
                    cur_pass = st.text_input(
                        "Current password", type="password", key="settings_cur_pass"
                    )
                    new_pass = st.text_input(
                        "New password (min 8 chars)", type="password", key="settings_new_pass"
                    )
                    conf_pass = st.text_input(
                        "Confirm new password", type="password", key="settings_conf_pass"
                    )
                    pc1, pc2, _ = st.columns([1, 1, 2])
                    with pc1:
                        if st.button(
                            "Save Password",
                            key="settings_save_pass",
                            type="primary",
                            width="stretch",
                        ):
                            if cur_pass and new_pass and conf_pass:
                                if new_pass != conf_pass:
                                    st.error("New passwords do not match.")
                                else:
                                    ok, msg = _change_password(user_id, cur_pass, new_pass)
                                    if ok:
                                        st.session_state.pop("settings_panel", None)
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            else:
                                st.warning("Please fill in all fields.")
                    with pc2:
                        if st.button("Cancel", key="settings_cancel_pass", width="stretch"):
                            st.session_state.pop("settings_panel", None)
                            st.rerun()

        # ─── Delete Account card ──────────────────────────────────────────────
        with st.container(key="settings_sec_delete"):
            st.markdown(
                _section_header(
                    _svg(_ICON_TRASH),
                    "Delete account",
                    "Permanently remove your account, saved CVs, analyses, and comparison history.",
                    danger=True,
                ),
                unsafe_allow_html=True,
            )
            if st.session_state.get("settings_confirm_delete"):
                st.markdown(
                    """
                    <div class="settings-delete-confirm">
                        <span class="settings-delete-confirm-icon">!</span>
                        <div>
                            <p class="settings-delete-confirm-title">Permanently delete your account?</p>
                            <p class="settings-delete-confirm-sub">
                                We'll remove your saved CVs, analyses, and comparisons. This cannot be undone.
                            </p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                dc1, dc2, _ = st.columns([1.4, 1, 2])
                with dc1:
                    if st.button(
                        "Yes, Delete My Account",
                        key="settings_do_delete",
                        type="primary",
                        width="stretch",
                    ):
                        ok, msg = _delete_account(user_id)
                        if ok:
                            logout_user()
                            st.rerun()
                        else:
                            st.error(msg)
                with dc2:
                    if st.button("Cancel", key="settings_cancel_delete", width="stretch"):
                        st.session_state.pop("settings_confirm_delete", None)
                        st.rerun()
            else:
                if st.button("Delete Account", key="settings_delete_btn"):
                    st.session_state["settings_confirm_delete"] = True
                    st.rerun()
