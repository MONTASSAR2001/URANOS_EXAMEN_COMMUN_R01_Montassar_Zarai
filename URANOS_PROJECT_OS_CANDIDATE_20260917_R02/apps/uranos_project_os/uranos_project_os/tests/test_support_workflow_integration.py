"""Real bench support-workflow tests. Authored; NOT RUN on the Windows host.

Execute only on an isolated synthetic site using bench run-tests. No dependency
is mocked and no test here demonstrates actual browser behavior.
"""
import uuid

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.file_manager import save_file

from uranos_project_os.services import changes, reports


class TestSupportWorkflows(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        self.token = uuid.uuid4().hex[:8]
        self.project = frappe.get_doc({"doctype": "Project", "project_name": "URANOS Workflow Test " + self.token}).insert().name
        self.author = self._user("author", "Team Lead")
        self.controller = self._user("controller", "Site Controller")
        self.engineer = self._user("engineer", "Engineering Director")
        self.manager = self._user("manager", "Project Manager")
        frappe.get_doc({"doctype": "URANOS Project Profile", "project": self.project,
                        "short_code": "WF-" + self.token, "site": "Synthetic Site", "status": "Draft"}).insert()

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def _user(self, name, role):
        user = frappe.get_doc({"doctype": "User", "email": f"wf-{name}-{self.token}@example.invalid",
            "first_name": "Synthetic Workflow", "send_welcome_email": 0,
            "roles": [{"role": "URANOS " + role}]}).insert(ignore_permissions=True).name
        frappe.get_doc({"doctype": "User Permission", "user": user, "allow": "Project",
                        "for_value": self.project, "apply_to_all_doctypes": 1}).insert()
        return user

    def _evidence(self, doctype, name):
        return save_file("synthetic-evidence.txt", b"SYNTHETIC TEST EVIDENCE - NOT AN ENGINEERING CERTIFICATE",
                         doctype, name, is_private=1).name

    def test_report_real_snapshot_freeze_and_independent_approval(self):
        frappe.set_user(self.author)
        doc = frappe.get_doc({"doctype": "URANOS Daily Site Report", "project": self.project,
            "site": "Synthetic Site", "posting_date": frappe.utils.today(), "manpower": 2, "status": "Draft"}).insert()
        reports.submit_daily_report(doc.name)
        frozen = frappe.get_doc(doc.doctype, doc.name)
        self.assertEqual(frozen.status, "Submitted")
        self.assertTrue(frozen.snapshot_hash)
        with self.assertRaises(frappe.PermissionError):
            reports.approve_daily_report(doc.name)  # author lacks the review role
        frozen.notes = "Alter the frozen report"
        with self.assertRaises(frappe.ValidationError):
            frozen.save()
        frappe.set_user(self.controller)
        reports.approve_daily_report(doc.name)
        result = frappe.get_doc(doc.doctype, doc.name)
        self.assertEqual(result.status, "Approved")
        self.assertEqual(result.approved_by, self.controller)
        self.assertEqual(result.progress_summary, frozen.progress_summary)

    def test_rfi_has_named_answerer_private_evidence_and_independent_closure(self):
        frappe.set_user(self.author)
        rfi = frappe.get_doc({"doctype": "URANOS RFI", "project": self.project, "question": "Synthetic routing question", "status": "Open"}).insert()
        frappe.set_user(self.manager)
        reports.assign_rfi(rfi.name, self.engineer)
        frappe.set_user(self.engineer)
        proof = self._evidence(rfi.doctype, rfi.name)
        reports.answer_rfi(rfi.name, "Synthetic approved routing response", [proof])
        with self.assertRaises(frappe.ValidationError):
            reports.close_rfi(rfi.name)
        frappe.set_user(self.author)
        reports.close_rfi(rfi.name)
        closed = frappe.get_doc(rfi.doctype, rfi.name)
        self.assertEqual(closed.status, "Closed")
        self.assertEqual(closed.answered_by, self.engineer)
        self.assertEqual(closed.closed_by, self.author)

    def test_blocker_stays_critical_until_independent_closure(self):
        frappe.set_user(self.author)
        blocker = frappe.get_doc({"doctype": "URANOS Blocker", "project": self.project, "title": "Synthetic obstruction",
            "severity": "Critical", "category": "Access", "status": "Open"}).insert()
        frappe.set_user(self.controller)
        reports.assign_blocker(blocker.name, self.author)
        frappe.set_user(self.author)
        proof = self._evidence(blocker.doctype, blocker.name)
        reports.resolve_blocker(blocker.name, "Synthetic obstruction removed", 2, [proof])
        submitted = frappe.get_doc(blocker.doctype, blocker.name)
        self.assertEqual(submitted.status, "Assigned")
        self.assertEqual(submitted.severity, "Critical")
        frappe.set_user(self.controller)
        reports.close_blocker(blocker.name)
        self.assertEqual(frappe.get_doc(blocker.doctype, blocker.name).status, "Closed")

    def test_change_request_identity_and_cost_cannot_be_forged_by_native_insert(self):
        frappe.set_user(self.engineer)
        doc = frappe.get_doc({"doctype": "URANOS Change Request", "project": self.project,
            "description": "Synthetic change", "reason": "Synthetic reason", "status": "Proposed",
            "requested_by": self.manager}).insert()
        self.assertEqual(doc.requested_by, self.engineer)
        doc.cost_impact = 25
        with self.assertRaises(frappe.PermissionError):
            doc.save()
        with self.assertRaises(frappe.PermissionError):
            changes.assess_change_cost(doc.name, 25, "NONEXISTENT")
