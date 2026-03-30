from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


class UISmokeTests(unittest.TestCase):
    def test_logo_home_navigation_script_targets_upload_reset(self) -> None:
        src = _read("app.py")
        self.assertIn("searchParams.set('page', 'upload')", src)
        self.assertIn("searchParams.set('_clear', '1')", src)
        self.assertIn("logo.setAttribute('href', buildHomeHref())", src)

    def test_theme_css_uses_shared_label_color_variable(self) -> None:
        theme_src = _read("src/ui/theme.py")
        css_tpl = _read("src/assets/ui/base_theme.css.tpl")
        self.assertIn('label_text_color = "#1f2937" if is_light else "#f9fafb"', theme_src)
        self.assertIn("color: {label_text_color} !important;", css_tpl)
        self.assertNotIn("{'#1f2937' if is_light else '#f9fafb'}", css_tpl)

    def test_theme_script_view_container_declarations_are_non_conflicting(self) -> None:
        js_tpl = _read("src/assets/ui/base_theme.js.tpl")
        self.assertEqual(
            js_tpl.count("const viewContainer = document.querySelector('[data-testid=\"stAppViewContainer\"]');"),
            1,
        )
        self.assertIn(
            "const viewContainerAllButtons = document.querySelector('[data-testid=\"stAppViewContainer\"]');",
            js_tpl,
        )

    def test_theme_uses_split_external_template_assets(self) -> None:
        src = _read("src/ui/theme.py")
        self.assertIn('_render_ui_markup_template("base_theme.css.tpl", replacements)', src)
        self.assertIn('_render_ui_markup_template("base_theme.js.tpl", replacements)', src)
        self.assertNotIn('base_theme_markup.tpl', src)

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
