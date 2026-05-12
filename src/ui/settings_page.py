"""Settings page - notifications, login info, email/password change, account deletion."""

import streamlit as st

from src.auth_utils import get_session_user, hash_password, logout_user, verify_password
from src.database import CV, Analysis, User, get_db


# DB helpers
def _load_db_user(user_id: str):
    db = get_db()
    try:
        return db.query(User).filter(User.id == user_id).first()
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


def _delete_account(user_id: str) -> tuple[bool, str]:
    db = get_db()
    try:
        db.query(Analysis).filter(Analysis.user_id == user_id).delete()
        db.query(CV).filter(CV.user_id == user_id).delete()
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


# Page renderer
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
        }
        [data-testid="stAppViewContainer"] .st-key-settings_page_shell .landing-clean-tag {
            display: none !important;
        }
        [data-testid="stAppViewContainer"] .settings-main-head {
            margin-top: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-settings_sec_notifications,
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
        [data-testid="stAppViewContainer"] .settings-sec-title {
            color: var(--text-primary);
            font-size: 1.12rem;
            font-weight: 700;
            margin: 0 0 0.2rem;
        }
        .settings-sec-title-danger {
            color: #ef4444;
            font-size: 1.12rem;
            font-weight: 700;
            margin: 0 0 0.2rem;
        }
        [data-testid="stAppViewContainer"] .settings-sec-sub {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin: 0 0 0.85rem;
            line-height: 1.55;
        }
        [data-testid="stAppViewContainer"] .settings-field-label {
            color: var(--text-primary);
            font-size: 0.92rem;
            font-weight: 600;
            margin: 0.9rem 0 0.4rem;
        }
        [data-testid="stAppViewContainer"] .settings-email-row {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin: 0 0 0.75rem;
        }
        [data-testid="stAppViewContainer"] .settings-email-row b {
            color: var(--text-primary);
        }
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
        [data-testid="stAppViewContainer"] .settings-divider {
            border: none;
            border-top: 1px solid var(--border-light, var(--border-color));
            margin: 1rem 0;
            opacity: 0.6;
        }
        @media (max-width: 820px) {
            [data-testid="stAppViewContainer"] .st-key-settings_page_shell {
                margin-top: -38px !important;
            }
            [data-testid="stAppViewContainer"] .settings-main-head {
                margin-top: 0 !important;
            }
            [data-testid="stAppViewContainer"] .st-key-settings_sec_notifications,
            [data-testid="stAppViewContainer"] .st-key-settings_sec_login,
            [data-testid="stAppViewContainer"] .st-key-settings_sec_delete {
                padding: 16px 14px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="settings_page_shell"):
        st.markdown(
            """
            <div class="landing-clean-head settings-main-head">
                <h2 class="landing-clean-title">Settings and preferences</h2>
                <p class="landing-clean-subtitle">
                    Manage notifications, login credentials, and account controls from one place.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_id = user.get("id", "")
        user_email = user.get("email", "")

        db_user = _load_db_user(user_id)
        is_google = bool(db_user and db_user.google_id)
        is_password_account = bool(db_user and db_user.hashed_password != "GOOGLE_OAUTH")

        with st.container(key="settings_sec_notifications"):
            st.markdown('<p class="settings-sec-title">Notifications</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="settings-sec-sub">Stay informed about career updates and new features.</p>',
                unsafe_allow_html=True,
            )
            st.checkbox(
                "Get latest updates for your career",
                key="settings_notif",
                value=st.session_state.get("settings_notif", False),
            )

        with st.container(key="settings_sec_login"):
            st.markdown('<p class="settings-sec-title">Login</p>', unsafe_allow_html=True)

            if is_google:
                st.markdown('<p class="settings-field-label">Google Account</p>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="settings-google-chip">'
                    f'<span class="settings-google-dot"></span>'
                    f'Connected &mdash; {user_email}'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown('<hr class="settings-divider"/>', unsafe_allow_html=True)

            st.markdown('<p class="settings-field-label">Email &amp; Password</p>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="settings-email-row">Your account email: <b>{user_email}</b></p>',
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
                st.markdown('<p class="settings-field-label">Change Email</p>', unsafe_allow_html=True)
                if not is_password_account:
                    st.info("Google-only accounts cannot change email here.")
                    if st.button("Cancel", key="settings_cancel_email_info"):
                        st.session_state.pop("settings_panel", None)
                        st.rerun()
                else:
                    new_email = st.text_input("New email address", key="settings_new_email", placeholder="new@example.com")
                    cur_pass = st.text_input("Current password", type="password", key="settings_cur_pass_email")
                    fc1, fc2, _ = st.columns([1, 1, 2])
                    with fc1:
                        if st.button("Save Email", key="settings_save_email", type="primary", width="stretch"):
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
                st.markdown('<p class="settings-field-label">Change Password</p>', unsafe_allow_html=True)
                if not is_password_account:
                    st.info("Google-only accounts cannot change password here.")
                    if st.button("Cancel", key="settings_cancel_pass_info"):
                        st.session_state.pop("settings_panel", None)
                        st.rerun()
                else:
                    cur_pass = st.text_input("Current password", type="password", key="settings_cur_pass")
                    new_pass = st.text_input("New password (min 8 chars)", type="password", key="settings_new_pass")
                    conf_pass = st.text_input("Confirm new password", type="password", key="settings_conf_pass")
                    pc1, pc2, _ = st.columns([1, 1, 2])
                    with pc1:
                        if st.button("Save Password", key="settings_save_pass", type="primary", width="stretch"):
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

        with st.container(key="settings_sec_delete"):
            st.markdown('<p class="settings-sec-title-danger">Delete Account</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="settings-sec-sub">Permanently removes your account, all saved CVs, '
                "and analysis history. This action cannot be undone.</p>",
                unsafe_allow_html=True,
            )
            if st.session_state.get("settings_confirm_delete"):
                st.warning("This will permanently delete your account and all data. Are you sure?")
                dc1, dc2, _ = st.columns([1.4, 1, 2])
                with dc1:
                    if st.button("Yes, Delete My Account", key="settings_do_delete", type="primary", width="stretch"):
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
