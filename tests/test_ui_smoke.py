from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


class UISmokeTests(unittest.TestCase):
    def test_logo_home_navigation_script_targets_upload_reset(self) -> None:
        src = _read("src/ui/css_injection.py")
        self.assertIn("searchParams.set('page', 'upload')", src)
        self.assertIn("searchParams.set('_clear', '1')", src)
        self.assertIn("logo.setAttribute('href', buildHomeHref())", src)

    def test_theme_css_uses_shared_label_color_variable(self) -> None:
        theme_src = _read("src/ui/theme.py")
        css_tpl = _read("src/assets/ui/base_theme.css.tpl")
        self.assertIn('label_text_color = "#1f2937" if is_light else "#f9fafb"', theme_src)
        self.assertIn("color: {label_text_color} !important;", css_tpl)
        self.assertNotIn("{'#1f2937' if is_light else '#f9fafb'}", css_tpl)

    def test_theme_script_is_lightweight_and_observer_free(self) -> None:
        js_tpl = _read("src/assets/ui/base_theme.js.tpl")
        self.assertIn("function applyThemeClass()", js_tpl)
        self.assertIn("theme-light", js_tpl)
        self.assertIn("theme-dark", js_tpl)
        self.assertNotIn("MutationObserver", js_tpl)
        self.assertNotIn("setInterval(", js_tpl)
        self.assertNotIn("location.reload", js_tpl)

    def test_theme_uses_split_external_template_assets(self) -> None:
        src = _read("src/ui/theme.py")
        self.assertIn('_render_ui_markup_template("base_theme.css.tpl", replacements)', src)
        self.assertIn('_render_ui_markup_template("base_theme.js.tpl", replacements)', src)
        self.assertNotIn('base_theme_markup.tpl', src)

    def test_back_button_sync_no_forced_reload(self) -> None:
        theme_src = _read("src/ui/theme.py")
        self.assertIn("Cleanup legacy global listeners/observers", theme_src)
        self.assertNotIn("location.reload()", theme_src)
        self.assertIn("removeEventListener('popstate'", theme_src)

    def test_app_does_not_install_heavy_nav_overrides_each_render(self) -> None:
        app_src = _read("app.py")
        self.assertIn("inject_fixed_top_bar()", app_src)
        self.assertNotIn("inject_logo_home_click_behavior()", app_src)
        self.assertIn("inject_back_button_sync()", app_src)
        self.assertIn("_inject_url_and_anchor_cleanup()", app_src)
        self.assertIn("inject_header_layout_override()", app_src)

    def test_home_url_cleanup_and_anchor_hiding_installed(self) -> None:
        app_src = _read("app.py")
        self.assertIn("excelcv-hide-heading-anchors", app_src)
        self.assertIn("[data-testid='stHeaderActionElements']", app_src)
        self.assertIn("w.history.replaceState(null, \"\", canonical)", app_src)
        self.assertNotIn("__excelcvNavResetObserver", app_src)

    def test_header_css_no_forced_three_column_grid(self) -> None:
        css_src = _read("src/ui/css_injection.py")
        self.assertNotIn('grid-template-columns: minmax(230px, 1.05fr) minmax(420px, 2.15fr) auto', css_src)

    def test_protected_pages_redirect_to_auth_with_next(self) -> None:
        app_src = _read("app.py")
        self.assertIn('PROTECTED_PAGES = {"cv-builder", "resume-builder", "my-cvs", "my-analyses", "compare-cv"}', app_src)
        self.assertIn("def _render_auth_gate(intended_page: str) -> None:", app_src)
        self.assertIn("st.session_state[\"auth_redirect\"] = intended_page", app_src)
        self.assertIn("render_auth_page(theme=_theme)", app_src)
        self.assertIn("is_unauth_protected = url_page in PROTECTED_PAGES and not get_session_user()", app_src)
        self.assertIn("_render_auth_gate(intended)", app_src)
        self.assertIn("if url_page in APP_PAGES and not is_unauth_protected:", app_src)

    def test_header_routes_unauthenticated_protected_links_to_auth(self) -> None:
        layout_src = _read("src/ui/layout.py")
        self.assertIn('PROTECTED_HEADER_PAGES = {"cv-builder", "resume-builder", "my-cvs", "my-analyses", "compare-cv"}', layout_src)
        self.assertIn('if not _user and page_key in PROTECTED_HEADER_PAGES:', layout_src)
        self.assertIn('href = _build_page_href("auth", next_page=page_key)', layout_src)
        self.assertIn("col_brand, col_user, col_nav", layout_src)
        self.assertIn("site-user-dropdown", layout_src)
        self.assertIn("site-nav-item-signin", layout_src)

    def test_split_template_files_exist_and_old_combined_template_removed(self) -> None:
        self.assertTrue((ROOT / "src" / "assets" / "ui" / "base_theme.css.tpl").exists())
        self.assertTrue((ROOT / "src" / "assets" / "ui" / "base_theme.js.tpl").exists())
        self.assertFalse((ROOT / "src" / "assets" / "ui" / "base_theme_markup.tpl").exists())

    def test_mockup_html_files_moved_out_of_templates(self) -> None:
        self.assertFalse((ROOT / "templates" / "resume_checker.html").exists())
        self.assertFalse((ROOT / "templates" / "resume_report_page.html").exists())
        self.assertTrue((ROOT / "docs" / "mockups" / "resume_checker.html").exists())
        self.assertTrue((ROOT / "docs" / "mockups" / "resume_report_page.html").exists())


if __name__ == "__main__":
    unittest.main()
