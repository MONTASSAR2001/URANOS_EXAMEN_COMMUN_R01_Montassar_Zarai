"""Real Frappe database/controller tests. NOT EXECUTED on the Windows host.

Run only on a disposable ERPNext v16 test site:
bench --site TEST_SITE run-tests --app uranos_project_os

The setup uses a trusted fixture capability solely to create an approved work
package; baseline approval and actual stock-ledger integration require separate
end-to-end acceptance. Nothing in these tests is a production fixture.
"""
import uuid
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.file_manager import save_file

from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain.offline import OfflineConflict
from uranos_project_os.services import offline, operations


class TestUranosServiceIntegration(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        self.token = uuid.uuid4().hex[:12]
        self.project = frappe.get_doc({"doctype": "Project", "project_name": "Synthetic QA " + self.token,
                                       "status": "Open"}).insert().name
        self.reporter = self._user("reporter")
        self.reviewer = self._user("reviewer")
        self.uom = "Synthetic QA " + self.token
        frappe.get_doc({"doctype": "UOM", "uom_name": self.uom}).insert()
        with authorized_transition():
            self.wp = frappe.get_doc({"doctype": "URANOS Work Package", "project": self.project,
                "code": "WP-050", "title": "Synthetic modules", "discipline": "Electrical", "uom": self.uom,
                "qty_planned": 100, "weight": 100, "baseline_version": "SYNTHETIC-B1",
                "baseline_approved": 1, "status": "Planned"}).insert().name
            baseline = frappe.get_doc({"doctype": "URANOS Baseline", "project": self.project,
                "version": "SYNTHETIC-B1", "status": "Approved", "approved_by": self.reviewer,
                "packages": [{"work_package": self.wp, "code": "WP-050", "uom": self.uom,
                    "qty_planned": 100, "weight": 100}]}).insert()
            frappe.get_doc({"doctype": "URANOS Project Profile", "project": self.project,
                "short_code": self.token, "site": "SYNTHETIC-SITE", "current_baseline": baseline.name,
                "status": "Draft"}).insert()
        self.header_patch = patch("frappe.get_request_header", side_effect=lambda name: frappe.session.user if name == "X-URANOS-User" else None)
        self.header_patch.start()
        self.addCleanup(self.header_patch.stop)

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def _user(self, label):
        name = f"uranos-qa-{label}-{self.token}@example.invalid"
        frappe.get_doc({"doctype": "User", "email": name, "first_name": "Synthetic QA",
            "send_welcome_email": 0, "roles": [{"role": "URANOS Site Controller"}]}).insert()
        frappe.get_doc({"doctype": "User Permission", "user": name, "allow": "Project",
            "for_value": self.project, "apply_to_all_doctypes": 1}).insert()
        return name

    def _progress(self):
        frappe.set_user(self.reporter)
        doc = frappe.get_doc({"doctype": "URANOS Field Progress Entry", "project": self.project,
            "work_package": self.wp, "baseline_version": "SYNTHETIC-B1", "activity": "Modules",
            "zone": "SYNTHETIC-ZONE", "crew": "SYNTHETIC-CREW", "posting_date": "2026-09-17",
            "qty_reported": 10, "qty_verified": 0, "status": "Draft"}).insert()
        proof = save_file("synthetic-proof.txt", b"Synthetic QA proof, not engineering acceptance.",
                          doc.doctype, doc.name, is_private=1)
        doc.append("evidence", {"file": proof.name})
        doc.save()
        return doc.name, proof.name

    def test_reporter_cannot_verify_own_real_persisted_declaration(self):
        name, _ = self._progress()
        operations.submit_progress(name)
        with self.assertRaises((ValueError, frappe.ValidationError, frappe.PermissionError)):
            operations.verify_progress(name, 10)
        self.assertEqual(frappe.db.get_value("URANOS Field Progress Entry", name, "qty_verified"), 0)

    def test_independent_partial_verification_changes_only_verified_quantity(self):
        name, _ = self._progress()
        operations.submit_progress(name)
        frappe.set_user(self.reviewer)
        operations.verify_progress(name, 6)
        doc = frappe.get_doc("URANOS Field Progress Entry", name)
        self.assertEqual(doc.qty_reported, 10)
        self.assertEqual(doc.qty_verified, 6)
        self.assertEqual(doc.verifier, self.reviewer)
        self.assertEqual(doc.reported_by, self.reporter)

    def test_verified_progress_is_immutable_through_native_save(self):
        name, _ = self._progress()
        operations.submit_progress(name)
        frappe.set_user(self.reviewer)
        operations.verify_progress(name, 6)
        doc = frappe.get_doc("URANOS Field Progress Entry", name)
        doc.qty_verified = 10
        doc.flags.uranos_authorized_transition = True
        with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
            doc.save()

    def test_offline_same_uuid_retry_returns_one_persisted_draft(self):
        frappe.set_user(self.reporter)
        envelope = {"uuid": str(uuid.uuid4()), "operation": "progress", "project": self.project,
            "payload": {"work_package": self.wp, "baseline_version": "SYNTHETIC-B1", "activity": "Modules",
                "zone": "SYNTHETIC-ZONE", "crew": "SYNTHETIC-CREW", "posting_date": "2026-09-17", "qty_reported": 7}}
        first = offline.synchronize(envelope)
        second = offline.synchronize(envelope)
        self.assertEqual(first["name"], second["name"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(frappe.db.count("URANOS Offline Sync Receipt", {"sync_user": self.reporter,
            "sync_uuid": envelope["uuid"]}), 1)
        doc = frappe.get_doc(first["doctype"], first["name"])
        self.assertEqual(doc.status, "Draft")
        self.assertEqual(doc.qty_verified, 0)
        envelope["payload"]["qty_reported"] = 8
        with self.assertRaises(OfflineConflict):
            offline.synchronize(envelope)

    def test_raw_ncr_severity_downgrade_requires_controlled_qa_review(self):
        frappe.set_user(self.reporter)
        doc = frappe.get_doc({"doctype": "URANOS NCR", "project": self.project,
            "severity": "Critical", "requirement": "Synthetic procedure", "defect": "Synthetic critical defect",
            "responsible": self.reviewer, "due_date": "2026-09-18", "status": "Open"}).insert()
        doc.severity = "Low"
        with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
            doc.save()

    def test_verified_evidence_file_cannot_be_published_via_native_save(self):
        name, proof_name = self._progress()
        operations.submit_progress(name)
        frappe.set_user(self.reviewer)
        operations.verify_progress(name, 6)
        frappe.set_user(self.reporter)
        proof = frappe.get_doc("File", proof_name)
        proof.is_private = 0
        with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
            proof.save()

    def test_verified_evidence_file_cannot_be_rebound_via_native_save(self):
        name, proof_name = self._progress()
        operations.submit_progress(name)
        frappe.set_user(self.reviewer)
        operations.verify_progress(name, 6)
        frappe.set_user(self.reporter)
        proof = frappe.get_doc("File", proof_name)
        proof.attached_to_doctype = None
        proof.attached_to_name = None
        with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
            proof.save()
