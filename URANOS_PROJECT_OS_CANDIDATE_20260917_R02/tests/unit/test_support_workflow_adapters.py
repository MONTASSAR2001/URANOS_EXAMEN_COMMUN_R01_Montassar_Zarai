"""Portable tests of actual adapters with observed boundary stubs, NOT ERP evidence."""
import importlib.util
import json
import sys
import unittest
from contextlib import nullcontext
from copy import deepcopy
from datetime import date
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import uranos_project_os

SERVICES = Path(__file__).resolve().parents[2] / "apps/uranos_project_os/uranos_project_os/services"


class Row(dict):
    def __getattr__(self, key):
        if key.startswith("__"):
            raise AttributeError(key)
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value

    def set(self, key, value):
        self[key] = value

    def append(self, key, value):
        self.setdefault(key, []).append(Row(value))

    def as_dict(self):
        return deepcopy(dict(self))

    def save(self, **kwargs):
        self["saved"] = True
        return self

    def insert(self, **kwargs):
        self["inserted"] = True
        return self


def load():
    fake = ModuleType("frappe")
    fake.whitelist = lambda *args, **kwargs: lambda fn: fn
    fake.PermissionError = PermissionError
    fake.throw = lambda message, *args: (_ for _ in ()).throw(ValueError(message))
    fake.session = SimpleNamespace(user="engineer")
    fake.utils = SimpleNamespace(now=lambda: "2026-09-17 12:00:00", getdate=lambda value=None: date.fromisoformat(str(value)) if value else date(2026, 9, 17))
    fake.db = Mock()
    fake.get_roles = Mock(return_value=["URANOS Engineering Director"])
    fake.get_all = Mock(return_value=[])
    fake.get_list = Mock(return_value=[])
    fake.get_doc = Mock(side_effect=lambda values: Row(values))
    security = ModuleType("uranos_project_os.security")
    security.require_roles = Mock(return_value="engineer")
    security.require_project = Mock()
    security.validate_evidence = Mock()
    security.SCOPED_FIELDS = {"BOM": "uranos_project", "Task": "project", "URANOS Work Package": "project"}
    controller = ModuleType("uranos_project_os.controllers")
    controller.authorized_transition = nullcontext
    common = ModuleType("uranos_project_os.services.common")
    common.require_post = Mock()
    common.scoped_doc = Mock()
    modules = {"frappe": fake, "uranos_project_os.security": security,
               "uranos_project_os.controllers": controller, "uranos_project_os.services.common": common}
    loaded = []
    with patch.dict(sys.modules, modules), patch.object(uranos_project_os, "security", security, create=True):
        for name in ("reports", "changes"):
            spec = importlib.util.spec_from_file_location("uranos_project_os.services."+name, SERVICES/(name+".py"))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            loaded.append(module)
    return (*loaded, fake, security, common)


def policy(**values):
    return Row(name="POL", project="P", status="Approved", action="Change Cost", enabled=1, currency="TND",
               first_role="URANOS Finance Controller", second_role="URANOS Executive", threshold=10,
               approved_by="policy-reviewer", owner="policy-author", valid_from="2026-01-01", valid_to="2027-01-01", **values)


def change(**values):
    data = {"doctype": "URANOS Change Request", "name": "CH", "project": "P", "status": "Impact Analysis", "requested_by": "requester",
        "description": "Route revision", "reason": "Ground conditions", "technical_impact": "Cable route", "schedule_impact_days": 1,
        "material_impact": "Revised cable route", "document_impact": "SLD revision", "cost_impact": 5, "cost_assessed": 1,
        "cost_assessed_by": "cost-controller", "currency": "TND", "policy": "POL", "financial_approval_required": 0,
        "impacted_objects": [Row(reference_doctype="URANOS Work Package", reference_name="WP", impact="Route")],
        "modified": "now", "technical_approver": None, "financial_approver": None}
    data["scope_snapshot"] = '{"version":1,"baselines":[]}'
    data.update(values)
    return Row(data)


class ChangeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.reports, self.changes, self.frappe, self.security, self.common = load()
        self.frappe.db.get_value.return_value = "P"

    def test_denied_actor_stops_before_documents(self):
        self.security.require_roles.side_effect = PermissionError()
        with self.assertRaises(PermissionError):
            self.changes.transition_change("CH", "Technical Approval")
        self.common.scoped_doc.assert_not_called()
        self.common.require_post.assert_called_once()

    def test_missing_cost_assessment_cannot_approve(self):
        with patch.object(self.changes, "_locked", return_value=change(cost_assessed=0)), patch.object(self.changes, "_save") as save:
            with self.assertRaisesRegex(ValueError, "explicit financial cost assessment"):
                self.changes.transition_change("CH", "Technical Approval")
            save.assert_not_called()

    def test_affected_document_project_is_checked_without_financial_dump(self):
        self.frappe.db.get_value.return_value = "OTHER"
        with self.assertRaisesRegex(ValueError, "outside the change project"):
            self.changes._affected(change())
        self.frappe.get_doc.assert_not_called()

    def test_unknown_affected_type_is_rejected(self):
        doc = change(impacted_objects=[Row(reference_doctype="User", reference_name="Administrator", impact="bad")])
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            self.changes._affected(doc)
        self.frappe.db.get_value.assert_not_called()

    def test_policy_requires_matching_company_currency(self):
        self.frappe.get_doc.side_effect = None
        self.frappe.get_doc.return_value = policy()
        self.common.scoped_doc.return_value = Row(company="CO")
        self.frappe.db.get_value.return_value = "USD"
        with self.assertRaisesRegex(ValueError, "company currency"):
            self.changes._policy("POL", "P")

    def test_disabled_policy_fails_closed(self):
        doc = policy()
        doc.enabled = 0
        self.frappe.get_doc.side_effect = None
        self.frappe.get_doc.return_value = doc
        self.common.scoped_doc.return_value = Row(company="CO")
        self.frappe.db.get_value.return_value = "TND"
        with self.assertRaisesRegex(ValueError, "enabled, current"):
            self.changes._policy("POL", "P")

    def test_above_threshold_requires_two_distinct_financial_signatures(self):
        doc = change(cost_impact=11)
        both = {"URANOS Finance Controller", "URANOS Executive"}
        self.assertFalse(self.changes._financial_ready(doc, policy(), {"one-person": both}))
        self.assertTrue(self.changes._financial_ready(doc, policy(), {"first": {"URANOS Finance Controller"}, "second": {"URANOS Executive"}}))

    def test_negative_cost_does_not_avoid_dual_approval(self):
        self.assertFalse(self.changes._financial_ready(change(cost_impact=-11), policy(), {"first": {"URANOS Finance Controller"}}))

    def test_changed_proposal_invalidates_cost_assessment(self):
        doc = change()
        affected = self.changes._affected(doc)
        doc.cost_assessment_hash = self.changes._digest(doc, policy(), affected)
        doc.description = "Changed scope after cost review"
        with patch.object(self.changes, "_locked", return_value=doc), patch.object(self.changes, "_policy", return_value=policy()), patch.object(self.changes, "_save") as save:
            with self.assertRaisesRegex(ValueError, "changed after cost assessment"):
                self.changes.transition_change("CH", "Technical Approval")
            save.assert_not_called()

    def test_technical_self_approval_is_rejected_by_real_domain_rule(self):
        doc = change(requested_by="engineer")
        doc.cost_assessment_hash = self.changes._digest(doc, policy(), self.changes._affected(doc))
        with patch.object(self.changes, "_locked", return_value=doc), patch.object(self.changes, "_policy", return_value=policy()), patch.object(self.changes, "_save") as save:
            with self.assertRaisesRegex(ValueError, "self-approved"):
                self.changes.transition_change("CH", "Technical Approval")
            save.assert_not_called()

    def test_public_result_does_not_leak_money(self):
        result = self.changes._result(change())
        self.assertEqual(set(result), {"doctype", "name", "status", "modified"})

    def test_no_signature_can_be_reused_for_another_payload(self):
        doc = change(payload_hash="new", technical_approver="engineer")
        self.frappe.get_all.return_value = [Row(policy="POL", requester="requester", approver="finance",
            payload_hash="old", approved_roles='["URANOS Finance Controller"]')]
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.changes._signed_roles(doc)

    def test_complete_change_flow_uses_real_domain_and_never_updates_affected_record(self):
        doc = change()
        doc.cost_assessment_hash = self.changes._digest(doc, policy(), self.changes._affected(doc))
        with patch.object(self.changes, "_locked", return_value=doc), patch.object(self.changes, "_policy", return_value=policy()), \
             patch.object(self.changes, "_signed_roles", return_value={}) as signatures, \
             patch.dict(sys.modules, {"uranos_project_os.services.reports": self.reports}):
            self.changes.transition_change("CH", "Technical Approval")
            self.security.require_roles.return_value = "finance"
            self.frappe.get_roles.return_value = ["URANOS Finance Controller"]
            self.changes.transition_change("CH", "Financial Approval", "Reviewed impacts")
            signatures.return_value = {"finance": {"URANOS Finance Controller"}}
            self.changes.transition_change("CH", "Approved")
            self.security.require_roles.return_value = "builder"
            self.frappe.get_roles.return_value = ["URANOS Project Manager"]
            self.changes.transition_change("CH", "Implemented", "Implemented approved route")
            self.security.require_roles.return_value = "engineer"
            self.frappe.get_roles.return_value = ["URANOS Engineering Director"]
            self.changes.transition_change("CH", "Verified", "Inspected approved route", ["FILE"])
            result = self.changes.transition_change("CH", "Closed")
        self.assertEqual(result["status"], "Closed")
        self.assertEqual(doc.implemented_by, "builder")
        self.assertEqual(doc.verified_by, "engineer")
        self.frappe.db.set_value.assert_not_called()
        self.assertEqual([call.args[0]["doctype"] for call in self.frappe.get_doc.call_args_list], ["URANOS Approval"])


class ReportAdapterTests(unittest.TestCase):
    def setUp(self):
        self.reports, self.changes, self.frappe, self.security, self.common = load()
        self.packages = {"WP": {"name": "WP", "project": "P", "uom": "Nos", "code": "WP-050"}}

    def entry(self, **values):
        row = {"name": "E1", "project": "P", "work_package": "WP", "activity": "Modules", "zone": "Z", "crew": "C",
            "posting_date": "2026-09-17", "baseline_version": "1", "qty_reported": 50, "qty_verified": 40,
            "reported_by": "team", "verifier": "controller", "status": "Verified", "site": "Site"}
        row.update(values)
        return row

    def snapshot(self, entries):
        return self.reports.effective_daily_progress("P", "Site", "2026-09-17", entries, self.packages)

    def test_only_verified_leaf_counts_and_pending_replacement_adds_nothing(self):
        initial = self.entry()
        correction = self.entry(name="E2", correction_of="E1", qty_reported=30, qty_verified=25)
        pending = self.entry(name="E3", correction_of="E2", qty_reported=20, qty_verified=0, verifier=None, status="Pending Verification")
        result = self.snapshot([initial, correction, pending])
        self.assertEqual([row["name"] for row in result["verified_installed"]], ["E2"])
        self.assertEqual(result["verified_installed"][0]["qty_verified"], "25")
        self.assertEqual(result["pending_declarations"], [])

    def test_self_verified_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "independent verification"):
            self.snapshot([self.entry(verifier="team")])

    def test_forked_corrections_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "fork"):
            self.snapshot([self.entry(), self.entry(name="E2", correction_of="E1"), self.entry(name="E3", correction_of="E1")])

    def test_foreign_project_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cross-project"):
            self.snapshot([self.entry(project="OTHER")])

    def test_unverified_declaration_does_not_become_progress(self):
        result = self.snapshot([self.entry(status="Pending Verification", qty_verified=0, verifier=None)])
        self.assertEqual(result["verified_installed"], [])
        self.assertEqual(len(result["pending_declarations"]), 1)

    def test_different_day_is_not_counted(self):
        self.assertEqual(self.snapshot([self.entry(posting_date="2026-09-16")])["verified_installed"], [])

    def test_report_self_approval_does_not_save(self):
        doc = Row(status="Submitted", recorded_by="engineer", submitted_by="engineer")
        with patch.object(self.reports, "_locked", return_value=doc), patch.object(self.reports, "_save") as save:
            with self.assertRaisesRegex(ValueError, "independent reviewer"):
                self.reports.approve_daily_report("REPORT")
            save.assert_not_called()

    def test_report_tampering_is_detected(self):
        doc = Row(status="Submitted", recorded_by="author", submitted_by="author", snapshot_hash="tampered", evidence=[])
        with patch.object(self.reports, "_locked", return_value=doc), patch.object(self.reports, "_save") as save:
            with self.assertRaisesRegex(ValueError, "integrity"):
                self.reports.approve_daily_report("REPORT")
            save.assert_not_called()

    def test_native_stock_projection_discards_rate_even_if_source_has_it(self):
        parent = Row(name="SE1", posting_date="2026-09-17", purpose="Material Transfer")
        child = Row(name="ROW1", parent="SE1", item_code="MC4", transfer_qty=10, stock_uom="Nos",
                    s_warehouse="A", t_warehouse="WIP", valuation_rate=123, amount=1230)
        self.frappe.get_all.return_value = [child]
        with patch.object(self.reports, "_rows", side_effect=[[parent], []]):
            result = self.reports._stock_summary("P", date(2026, 9, 17))
        output = json.dumps(result)
        self.assertNotIn("valuation_rate", output)
        self.assertNotIn("1230", output)
        self.assertEqual(result["physical_progress_effect"], "none")

    def test_resolver_cannot_close_own_blocker(self):
        doc = Row(status="Assigned", resolution_submitted_at="now", resolution="Fixed", responsible="engineer", resolved_by="engineer")
        with patch.object(self.reports, "_locked", return_value=doc), patch.object(self.reports, "_save") as save:
            with self.assertRaisesRegex(ValueError, "independent review"):
                self.reports.close_blocker("B")
            save.assert_not_called()

    def test_critical_blocker_stays_open_while_resolution_waits(self):
        doc = Row(doctype="URANOS Blocker", name="B", status="Assigned", responsible="engineer", resolution_submitted_at=None, modified="now")
        with patch.object(self.reports, "_locked", return_value=doc), patch.object(self.reports, "_set_evidence"), patch.object(self.reports, "_save"):
            result = self.reports.resolve_blocker("B", "Corrected", 2, ["FILE"])
        self.assertEqual(doc.status, "Assigned")
        self.assertTrue(result["pending_independent_review"])

    def test_rfi_answer_requires_actual_assignee(self):
        with patch.object(self.reports, "_locked", return_value=Row(status="Assigned", assignee="someone-else")), patch.object(self.reports, "_save") as save:
            with self.assertRaisesRegex(ValueError, "named RFI assignee"):
                self.reports.answer_rfi("RFI", "Answer", ["F"])
            save.assert_not_called()

    def test_rfi_answerer_cannot_close_their_own_answer(self):
        with patch.object(self.reports, "_locked", return_value=Row(status="Answered", answered_by="engineer", assignee="engineer")), self.assertRaisesRegex(ValueError, "independent reviewer"):
            self.reports.close_rfi("RFI")

    def test_evidence_strings_cannot_inject_arbitrary_attributes(self):
        with self.assertRaises(ValueError):
            self.reports._set_evidence(Row(), "answer_evidence", [{"file": "F", "owner": "Administrator"}])


if __name__ == "__main__":
    unittest.main()
