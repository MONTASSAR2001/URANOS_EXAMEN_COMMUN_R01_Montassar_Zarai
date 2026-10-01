"""Portable structural contract tests; these are NOT database integration tests."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("schema_generator", ROOT / "scripts/generate_doctypes.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class SchemaContractTests(unittest.TestCase):
    def test_all_generated_files_match_source(self):
        for path, expected in generator.expected_files():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_text(encoding="utf-8"), expected)

    def test_scoped_types_have_required_project(self):
        for name, schema in generator.SCHEMAS.items():
            if schema["istable"] or name == "URANOS Offline Identity Key":
                continue
            fields = {field["fieldname"]: field for field in schema["fields"]}
            with self.subTest(doctype=name):
                self.assertEqual(fields["project"]["options"], "Project")
                self.assertEqual(fields["project"]["reqd"], 1)

    def test_all_custom_links_resolve_and_field_names_are_unique(self):
        for name, schema in generator.SCHEMAS.items():
            fields = schema["fields"]
            with self.subTest(doctype=name):
                self.assertEqual(len(fields), len({field["fieldname"] for field in fields}))
                self.assertEqual(schema["field_order"], [field["fieldname"] for field in fields])
                for field in fields:
                    if field["fieldtype"] in {"Link", "Table"} and field.get("options", "").startswith("URANOS "):
                        self.assertIn(field["options"], generator.SCHEMAS)

    def test_no_normal_role_can_delete_cancel_or_export_critical_records(self):
        for schema in generator.SCHEMAS.values():
            for row in schema["permissions"]:
                self.assertFalse(row.get("delete"))
                self.assertFalse(row.get("cancel"))
                self.assertFalse(row.get("export"))

    def test_finance_level_only_granted_to_explicit_finance_roles(self):
        permitted = {"URANOS Executive", "URANOS Finance Controller"}
        for schema in generator.SCHEMAS.values():
            for row in schema["permissions"]:
                if row.get("permlevel") == 1:
                    self.assertIn(row["role"], permitted)
                    self.assertTrue(any(base["role"] == row["role"] and not base.get("permlevel")
                                        for base in schema["permissions"]))

    def test_offline_key_is_server_only_password_with_unique_user(self):
        schema = generator.SCHEMAS["URANOS Offline Identity Key"]
        fields = {field["fieldname"]: field for field in schema["fields"]}
        self.assertEqual(schema["permissions"], [])
        self.assertEqual(fields["encryption_key"]["fieldtype"], "Password")
        self.assertEqual(fields["user"]["unique"], 1)

    def test_verification_fields_are_not_editable_form_fields(self):
        schema = generator.SCHEMAS["URANOS Field Progress Entry"]
        fields = {row["fieldname"]: row for row in schema["fields"]}
        for name in ("qty_verified", "verifier", "verified_at", "reported_by", "sync_uuid"):
            self.assertEqual(fields[name]["read_only"], 1)

    def test_no_permission_or_real_master_data_fixture(self):
        for schema in generator.SCHEMAS.values():
            for field in schema["fields"]:
                self.assertNotIn("@", str(field.get("default", "")))
        self.assertNotIn("default", next(f for f in generator.SCHEMAS["URANOS Approval Policy"]["fields"]
                                         if f["fieldname"] == "threshold"))


if __name__ == "__main__":
    unittest.main()
