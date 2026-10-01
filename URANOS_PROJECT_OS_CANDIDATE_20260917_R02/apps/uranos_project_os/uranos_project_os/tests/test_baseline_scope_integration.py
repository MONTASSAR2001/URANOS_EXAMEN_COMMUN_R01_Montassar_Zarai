"""Real ERPNext/Frappe IR-F03 scenarios: AUTHORED, NOT RUN on Windows.

Run only in a disposable synthetic v16 bench. No mocks, production accounts or
implicit approval thresholds are used. These tests do not prove SQL concurrency.
"""
import json
import uuid

import frappe
from frappe.tests import IntegrationTestCase

from uranos_project_os.services import changes, operations
from uranos_project_os.services.common import scoped_doc


class TestBaselineScopeIntegration(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        self.token = uuid.uuid4().hex[:8]
        self.company = frappe.get_doc({"doctype": "Company", "company_name": "Synthetic Scope " + self.token,
            "abbr": "S" + self.token[:4], "default_currency": "USD", "country": "Tunisia"}).insert().name
        self.project = frappe.get_doc({"doctype": "Project", "project_name": "Synthetic Scope " + self.token,
                                      "company": self.company}).insert().name
        self.author = self._user("author", "Project Manager")
        self.engineer = self._user("engineer", "Engineering Director")
        self.finance = self._user("finance", "Finance Controller")
        self.executive = self._user("executive", "Executive")
        if not frappe.db.exists("UOM", "Nos"):
            frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert()
        frappe.set_user(self.author)
        self.profile = frappe.get_doc({"doctype": "URANOS Project Profile", "project": self.project,
            "short_code": "BS-" + self.token, "site": "Synthetic Site", "status": "Draft"}).insert()
        self.first = self._baseline("1", None, None)
        frappe.set_user(self.engineer)
        operations.approve_baseline(self.first.name)
        frappe.set_user(self.author)
        self.change = frappe.get_doc({"doctype": "URANOS Change Request", "project": self.project,
            "description": "Synthetic exact proposed quantities", "reason": "Synthetic design revision",
            "technical_impact": "Layout", "material_impact": "Modules", "document_impact": "Layout revision",
            "schedule_impact_days": 0, "status": "Proposed"}).insert()
        self.target = self._baseline("2", self.first.name, self.change.name)
        self.change.append("impacted_objects", {"reference_doctype": self.target.doctype,
            "reference_name": self.target.name, "impact": "Explicit target quantities"})
        self.change.save()
        changes.transition_change(self.change.name, "Impact Analysis")
        frappe.set_user(self.finance)
        self.policy = frappe.get_doc({"doctype": "URANOS Approval Policy", "project": self.project,
            "policy_code": "SYNTHETIC-SCOPE-" + self.token,
            "action": "Change Cost", "currency": "USD", "threshold": 100, "first_role": "URANOS Finance Controller",
            "second_role": "URANOS Executive", "enabled": 1, "valid_from": frappe.utils.today(), "status": "Draft"}).insert()
        frappe.set_user(self.executive)
        changes.approve_change_policy(self.policy.name)

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def _user(self, prefix, role):
        user = frappe.get_doc({"doctype": "User", "email": f"scope-{prefix}-{self.token}@example.invalid",
            "first_name": "Synthetic Scope", "send_welcome_email": 0,
            "roles": [{"role": "URANOS " + role}]}).insert(ignore_permissions=True).name
        frappe.get_doc({"doctype": "User Permission", "user": user, "allow": "Project",
            "for_value": self.project, "apply_to_all_doctypes": 1}).insert()
        return user

    def _baseline(self, version, supersedes, change_request):
        fields = {"code": "MODULES", "uom": "Nos", "qty_planned": 100, "weight": 100,
                  "baseline_start": "2026-09-01", "baseline_finish": "2026-10-01"}
        wp = frappe.get_doc({"doctype": "URANOS Work Package", "project": self.project,
            "baseline_version": version, "title": "Synthetic modules", "discipline": "Electrical",
            "required_documents": [{"document_code": "LAYOUT", "required_status": "IFC", "mandatory": 1}],
            **fields}).insert()
        return frappe.get_doc({"doctype": "URANOS Baseline", "project": self.project, "version": version,
            "supersedes": supersedes, "change_request": change_request, "revision_reason": "Synthetic test",
            "packages": [{"work_package": wp.name, **fields}], "status": "Draft"}).insert()

    def _assess(self):
        frappe.set_user(self.finance)
        changes.assess_change_cost(self.change.name, 0, self.policy.name)

    def _approve_change(self):
        self._assess()
        frappe.set_user(self.engineer)
        changes.transition_change(self.change.name, "Technical Approval")
        changes.transition_change(self.change.name, "Approved")

    def test_exact_signed_revision_applies_and_history_remains_valid(self):
        self._approve_change()
        original = frappe.get_doc(self.change.doctype, self.change.name)
        scope = json.loads(original.scope_snapshot)
        self.assertEqual(scope["baselines"][0]["name"], self.target.name)
        operations.approve_baseline(self.target.name)
        scoped_doc("Project", self.project, lock=True)
        changes.verify_baseline_authorization(scoped_doc(self.change.doctype, self.change.name, lock=True),
                                             scoped_doc(self.target.doctype, self.target.name, lock=True))
        self.assertEqual(frappe.db.get_value(self.profile.doctype, self.profile.name, "current_baseline"), self.target.name)
        self.assertEqual(frappe.db.get_value(self.change.doctype, self.change.name, "payload_hash"), original.payload_hash)

    def test_post_assessment_quantity_change_blocks_technical_approval(self):
        self._assess()
        frappe.set_user(self.author)
        wp = frappe.get_doc("URANOS Work Package", self.target.packages[0].work_package)
        wp.qty_planned = 200
        wp.save()
        self.target.reload()
        self.target.packages[0].qty_planned = 200
        self.target.save()
        frappe.set_user(self.engineer)
        with self.assertRaises(frappe.ValidationError):
            changes.transition_change(self.change.name, "Technical Approval")
        self.assertEqual(frappe.db.get_value(self.profile.doctype, self.profile.name, "current_baseline"), self.first.name)

    def test_approved_work_package_impact_cannot_authorize_baseline(self):
        frappe.set_user(self.author)
        self.change.reload()
        self.change.impacted_objects = []
        self.change.append("impacted_objects", {"reference_doctype": "URANOS Work Package",
            "reference_name": self.target.packages[0].work_package, "impact": "Work package only"})
        self.change.save()
        self._approve_change()
        with self.assertRaises(frappe.ValidationError):
            operations.approve_baseline(self.target.name)
        self.assertEqual(frappe.db.get_value(self.target.doctype, self.target.name, "status"), "Draft")

    def test_scope_snapshot_cannot_be_seeded_or_modified_by_native_save(self):
        frappe.set_user(self.author)
        self.change.reload()
        self.change.scope_snapshot = '{"version":1,"baselines":[]}'
        with self.assertRaises(frappe.PermissionError):
            self.change.save()
