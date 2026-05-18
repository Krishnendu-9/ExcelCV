import unittest

from src.services.scoring import calculate_sections_order


class SectionsOrderTests(unittest.TestCase):
    def test_entry_level_prefers_education_first(self) -> None:
        cv_text = """
John Doe
Summary
Intern with hands-on project experience.
Experience
Built a small college project using Python and SQL.
Education
B.Tech Computer Science 2021 - 2025
Skills
Python, SQL
"""
        score, details = calculate_sections_order(cv_text)
        self.assertLessEqual(score, 80)
        self.assertEqual(details.get("status"), "warn")


if __name__ == "__main__":
    unittest.main()
