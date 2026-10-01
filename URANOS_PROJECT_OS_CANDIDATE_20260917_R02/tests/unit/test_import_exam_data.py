"""Unit test for import_exam_data.py logic and dataset integrity."""
import json
import unittest
from pathlib import Path

from uranos_project_os.scripts.import_exam_data import (
    CATEGORY_MAP,
    SEVERITY_MAP,
    load_data,
    locate_data_file,
)


class TestImportExamData(unittest.TestCase):
    def test_locate_and_load_data(self):
        data_file = locate_data_file()
        self.assertTrue(data_file.is_file())

        data = load_data(data_file)
        self.assertIn("projects", data)
        self.assertIn("demo_users", data)
        self.assertIn("sample_issues", data)

        # 20 Projects
        self.assertEqual(len(data["projects"]), 20)
        project_ids = [p["id"] for p in data["projects"]]
        self.assertEqual(project_ids[0], "PV-01")
        self.assertEqual(project_ids[-1], "PV-20")

        # 4 Demo Users
        self.assertEqual(len(data["demo_users"]), 4)

        # 5 Sample Issues
        self.assertEqual(len(data["sample_issues"]), 5)
        for issue in data["sample_issues"]:
            self.assertIn(issue["id"], ["B-001", "B-002", "B-003", "B-004", "B-005"])
            mapped_cat = CATEGORY_MAP.get(issue.get("category", ""), "Material")
            mapped_sev = SEVERITY_MAP.get(issue.get("severity", ""), "Low")
            self.assertIn(mapped_cat, ["Document", "Material", "Access", "Equipment", "Quality"])
            self.assertIn(mapped_sev, ["Low", "Medium", "High", "Critical"])


if __name__ == "__main__":
    unittest.main()
