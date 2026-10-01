import unittest
from copy import deepcopy
from datetime import date
from decimal import Decimal

from uranos_project_os.domain.controls import (
    GATE_CONDITIONS, RuleViolation, aggregate_progress, dashboard_summary,
    evaluate_stage_gate, number, validate_baseline, validate_delegated_approval,
    validate_progress_entry, validate_change_transition,
)


def baseline():
    return validate_baseline("P-A", "B1", [
        {"name": "MODULES", "project": "P-A", "baseline_version": "B1", "qty_planned": "100", "weight": "60"},
        {"name": "DC", "project": "P-A", "baseline_version": "B1", "qty_planned": "200", "weight": "40"},
    ])


def progress(name="E1", **overrides):
    row = {"name": name, "project": "P-A", "work_package": "MODULES", "baseline_version": "B1", "qty_reported": "80", "qty_verified": "50", "reported_by": "team@example.test", "verifier": "controller@example.test", "status": "Verified", "evidence": ["/private/files/proof.jpg"], "activity": "MODULE-POSE", "zone": "A"}
    row.update(overrides)
    return row


class NumericTests(unittest.TestCase):
    def test_decimal_exact(self):
        self.assertEqual(number("0.1", "q") + number("0.2", "q"), Decimal("0.3"))

    def test_bad_numbers(self):
        for value in (True, False, None, "", "NaN", "sNaN", "Infinity", "-Infinity", float("nan"), -1, "-0.01", "1e19", "0.0000000000001", "bad"):
            with self.subTest(value=value), self.assertRaises(RuleViolation):
                number(value, "q")


class BaselineTests(unittest.TestCase):
    def test_weights_and_quantities_normalized(self):
        result = baseline()
        self.assertIsInstance(result["packages"][0]["weight"], Decimal)

    def test_reject_incomplete_baseline(self):
        for field, value in (("weight", "59"), ("qty_planned", "0"), ("baseline_version", "B2"), ("project", "P-B")):
            rows = baseline()["packages"]
            rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(RuleViolation):
                validate_baseline("P-A", "B1", rows)

    def test_duplicate_package_rejected(self):
        row = baseline()["packages"][0]
        with self.assertRaises(RuleViolation):
            validate_baseline("P-A", "B1", [row, row])

    def test_reversed_dates_rejected(self):
        rows = baseline()["packages"]
        rows[0].update(baseline_start="2026-10-10", baseline_finish="2026-09-10")
        with self.assertRaises(RuleViolation):
            validate_baseline("P-A", "B1", rows)


class ProgressTests(unittest.TestCase):
    def test_partial_verification_only(self):
        result = aggregate_progress("P-A", baseline(), [progress()])
        self.assertEqual(result["physical_progress"], Decimal(30))
        self.assertEqual(result["work_packages"][0]["qty_reported"], Decimal(80))
        self.assertEqual(result["work_packages"][0]["qty_verified"], Decimal(50))

    def test_reporting_and_stock_do_not_increase_progress(self):
        reported = progress(status="Pending Verification", qty_verified=0, verifier=None)
        result = aggregate_progress("P-A", baseline(), [reported])
        self.assertEqual(result["physical_progress"], 0)
        reported["stock_issued"] = 1000000
        self.assertEqual(aggregate_progress("P-A", baseline(), [reported])["physical_progress"], 0)

    def test_overrun_capped_at_weight(self):
        result = aggregate_progress("P-A", baseline(), [progress(qty_reported=150, qty_verified=150)])
        self.assertEqual(result["physical_progress"], 60)
        self.assertEqual(result["work_packages"][0]["overrun_qty"], 50)

    def test_no_mutation_of_inputs(self):
        entry = progress()
        original = deepcopy(entry)
        aggregate_progress("P-A", baseline(), [entry])
        self.assertEqual(entry, original)

    def test_correction_replaces_not_adds(self):
        correction = progress("E2", correction_of="E1", revision_reason="10 modules failed inspection", qty_reported=80, qty_verified=40)
        result = aggregate_progress("P-A", baseline(), [progress(), correction])
        self.assertEqual(result["physical_progress"], 24)
        self.assertEqual(result["effective_corrections"], 1)
        restored = progress("E3", correction_of="E2", revision_reason="Rework independently accepted", qty_reported=80, qty_verified=50)
        self.assertEqual(aggregate_progress("P-A", baseline(), [restored, progress(), correction])["physical_progress"], 30)

    def test_zero_correction_removes_previous_progress(self):
        correction = progress("E2", correction_of="E1", revision_reason="Entire installation rejected", qty_verified=0)
        self.assertEqual(aggregate_progress("P-A", baseline(), [progress(), correction])["physical_progress"], 0)

    def test_pending_correction_keeps_verified_truth(self):
        correction = progress("E2", correction_of="E1", revision_reason="Awaiting review", qty_verified=0, verifier=None, status="Pending Verification")
        result = aggregate_progress("P-A", baseline(), [progress(), correction])
        self.assertEqual(result["physical_progress"], 30)
        self.assertEqual(result["work_packages"][0]["qty_reported"], 80)

    def test_invalid_correction_graph(self):
        cases = [
            [progress(), progress("E2", correction_of="missing", revision_reason="x")],
            [progress(), progress("E2", correction_of="E1", revision_reason="x"), progress("E3", correction_of="E1", revision_reason="x")],
            [progress(correction_of="E2", revision_reason="x"), progress("E2", correction_of="E1", revision_reason="x")],
            [progress(), progress("E2", correction_of="E1", revision_reason="x", zone="B")],
            [progress(), progress("E2", correction_of="E1", revision_reason="x", work_package="DC")],
        ]
        for entries in cases:
            with self.subTest(entries=entries), self.assertRaises(RuleViolation):
                aggregate_progress("P-A", baseline(), entries)

    def test_duplicate_identity_invalid(self):
        with self.assertRaises(RuleViolation):
            aggregate_progress("P-A", baseline(), [progress(), progress()])

    def test_cross_project_invalid(self):
        with self.assertRaises(RuleViolation):
            aggregate_progress("P-A", baseline(), [progress(project="P-B")])

    def test_invalid_quantity_or_evidence_or_identity(self):
        for changes in ({"qty_verified": 81}, {"qty_verified": "NaN"}, {"qty_reported": -1}, {"evidence": []}, {"verifier": "team@example.test"}, {"status": "Made Up"}, {"work_package": "MISSING"}, {"baseline_version": "B99"}):
            with self.subTest(changes=changes), self.assertRaises(RuleViolation):
                aggregate_progress("P-A", baseline(), [progress(**changes)])

    def test_unverified_quantities_rejected_not_silently_counted(self):
        with self.assertRaises(RuleViolation):
            aggregate_progress("P-A", baseline(), [progress(status="Cancelled")])

    def test_baseline_revision_explicit_history(self):
        revised = baseline()
        revised["version"] = "B2"
        for package in revised["packages"]:
            package["baseline_version"] = "B2"
        with self.assertRaises(RuleViolation):
            aggregate_progress("P-A", revised, [progress()])
        self.assertEqual(aggregate_progress("P-A", revised, [progress()], approved_versions={"B1", "B2"})["physical_progress"], 30)

    def test_create_and_independently_verify(self):
        pending = progress(status="Pending Verification", qty_verified=0, verifier=None)
        validate_progress_entry(pending, pending["reported_by"], ["P-A"])
        result = validate_progress_entry(progress(), "controller@example.test", ["P-A"], can_verify=True, previous=pending)
        self.assertEqual(result["qty_verified"], 50)

    def test_no_direct_verified_creation(self):
        with self.assertRaises(RuleViolation):
            validate_progress_entry(progress(), "controller@example.test", ["P-A"], can_verify=True)

    def test_actor_scope_and_verifier_enforced(self):
        pending = progress(status="Pending Verification", qty_verified=0, verifier=None)
        for actor, scope, allowed in (("other", ["P-A"], True), ("controller@example.test", ["P-B"], True), ("controller@example.test", ["P-A"], False)):
            with self.subTest(actor=actor, scope=scope, allowed=allowed), self.assertRaises(RuleViolation):
                validate_progress_entry(progress(), actor, scope, can_verify=allowed, previous=pending)

    def test_immutable_verified_record(self):
        with self.assertRaises(RuleViolation):
            validate_progress_entry(progress(qty_verified=20), "controller@example.test", ["P-A"], can_verify=True, previous=progress())

    def test_submitted_quantity_immutable(self):
        pending = progress(status="Pending Verification", qty_verified=0, verifier=None)
        with self.assertRaises(RuleViolation):
            validate_progress_entry(progress(qty_reported=90), "controller@example.test", ["P-A"], can_verify=True, previous=pending)

    def test_submitted_zone_and_evidence_immutable(self):
        pending = progress(status="Pending Verification", qty_verified=0, verifier=None)
        for changes in ({"zone": "B"}, {"evidence": ["replacement.jpg"]}):
            with self.subTest(changes=changes), self.assertRaises(RuleViolation):
                validate_progress_entry(progress(**changes), "controller@example.test", ["P-A"], can_verify=True, previous=pending)

    def test_correction_target_server_loaded(self):
        correction = progress("E2", correction_of="E1", revision_reason="bad modules", status="Pending Verification", qty_verified=0, verifier=None)
        with self.assertRaises(RuleViolation):
            validate_progress_entry(correction, correction["reported_by"], ["P-A"])
        validate_progress_entry(correction, correction["reported_by"], ["P-A"], correction=progress())


class GateTests(unittest.TestCase):
    def test_gate_zero_checklist_machine_readable(self):
        assessment = evaluate_stage_gate("P-A", 0, {})
        self.assertFalse(assessment["ready"])
        self.assertEqual(len(assessment["missing"]), 10)
        self.assertTrue(evaluate_stage_gate("P-A", 0, dict.fromkeys(GATE_CONDITIONS[0], True))["ready"])

    def test_string_true_is_not_evidence(self):
        self.assertFalse(evaluate_stage_gate("P-A", 5, {"civil_scope_verified": "true"}, completed_gates=[0])["ready"])

    def test_gate_dependencies_and_approvals(self):
        conditions = {"civil_scope_verified": True}
        self.assertIn("gate:0", evaluate_stage_gate("P-A", 5, conditions)["missing"])
        result = evaluate_stage_gate("P-A", 5, conditions, completed_gates=[0], prerequisite_gates=[4])
        self.assertIn("gate:4", result["missing"])
        approvals = [{"project": "P-A", "gate": 5, "status": "Approved", "approved_by": "qa", "requested_by": "team"}]
        self.assertTrue(evaluate_stage_gate("P-A", 5, conditions, completed_gates=[0], approvals=approvals, required_approvals=1)["ready"])
        self.assertFalse(evaluate_stage_gate("P-A", 5, conditions, completed_gates=[0], approvals=approvals * 2, required_approvals=2)["ready"])

    def test_self_approval_rejected(self):
        approvals = [{"project": "P-A", "gate": 5, "status": "Approved", "approved_by": "team", "requested_by": "team"}]
        with self.assertRaises(RuleViolation):
            evaluate_stage_gate("P-A", 5, {}, approvals=approvals, required_approvals=1)

    def test_engineering_requires_document_configuration(self):
        result = evaluate_stage_gate("P-A", 1, dict.fromkeys(GATE_CONDITIONS[1], True), completed_gates=[0])
        self.assertIn("required_ifc_configuration", result["missing"])

    def test_hold_and_critical_ncr_block(self):
        result = evaluate_stage_gate("P-A", 5, {"civil_scope_verified": True}, completed_gates=[0], holds=[{"project": "P-A", "name": "H1", "status": "Open"}], ncrs=[{"project": "P-A", "name": "N1", "severity": "Critical", "status": "Assigned"}])
        self.assertEqual(result["missing"], ["hold:H1", "ncr:N1"])


class DashboardTests(unittest.TestCase):
    def summary(self, **kwargs):
        defaults = {"planned_percent": 30, "material_readiness_percent": 100, "today": "2026-09-17"}
        defaults.update(kwargs)
        return dashboard_summary("P-A", aggregate_progress("P-A", baseline(), [progress()]), **defaults)

    def test_material_separate_from_physical(self):
        result = self.summary(material_readiness_percent=80)
        self.assertEqual(result["physical_progress"], 30)
        self.assertEqual(result["material_readiness"], 80)

    def test_critical_blocker_overrides_on_track(self):
        result = self.summary(blockers=[{"name": "BL1", "project": "P-A", "severity": "Critical", "status": "Open"}])
        self.assertEqual(result["status"], "Red")
        self.assertEqual(result["risks"][0]["source_name"], "BL1")

    def test_overdue_high_ncr_cannot_be_green(self):
        result = self.summary(ncrs=[{"name": "NC1", "project": "P-A", "severity": "High", "status": "Corrective Action", "due_date": "2026-09-16"}])
        self.assertEqual(result["status"], "Red")

    def test_critical_stock_variance_visible(self):
        self.assertEqual(self.summary(stock_variances=[{"name": "V1", "project": "P-A", "variance": 4, "risk_class": "R3", "status": "Open"}])["status"], "Red")

    def test_missing_data_is_not_zero_or_green(self):
        result = self.summary(planned_percent=None, material_readiness_percent=None)
        self.assertEqual(result["status"], "Unknown")
        self.assertIsNone(result["progress_delta"])

    def test_finance_allowlisted_and_denied_by_default(self):
        finance = {"project": "P-A", "currency": "TND", "budget": 100, "committed": 110, "bank_secret": "NEVER COPY"}
        self.assertNotIn("finance", self.summary(finance=finance))
        result = self.summary(finance=finance, finance_allowed=True)
        self.assertNotIn("bank_secret", result["finance"])
        self.assertEqual(result["finance"]["budget_remaining"], -10)
        self.assertIsNone(result["finance"]["paid"])

    def test_finance_cross_project_rejected(self):
        with self.assertRaises(RuleViolation):
            self.summary(finance={"project": "P-B", "currency": "TND"}, finance_allowed=True)

    def test_cross_project_alerts_rejected(self):
        with self.assertRaises(RuleViolation):
            self.summary(blockers=[{"name": "BL1", "project": "P-B", "severity": "Critical", "status": "Open"}])


class DelegationTests(unittest.TestCase):
    def approve(self, **changes):
        delegation = {"project": "P-A", "status": "Approved", "delegator": "manager", "delegate": "deputy", "valid_from": "2026-09-01", "valid_to": "2026-09-30", "actions": ["stock_adjustment"], "currency": "TND", "amount_limit": 500}
        args = {"actor": "deputy", "project": "P-A", "action": "stock_adjustment", "on_date": date(2026, 9, 17), "amount": 100, "currency": "TND", "requested_by": "warehouse"}
        args.update(changes)
        return validate_delegated_approval(delegation, **args)

    def test_scoped_valid_delegation(self):
        self.assertTrue(self.approve())

    def test_delegation_scope_limits_and_dates(self):
        for changes in ({"actor": "stranger"}, {"project": "P-B"}, {"action": "contract"}, {"on_date": "2026-10-01"}, {"amount": 501}, {"currency": "USD"}, {"requested_by": "deputy"}):
            with self.subTest(changes=changes), self.assertRaises(RuleViolation):
                self.approve(**changes)


class ChangeTests(unittest.TestCase):
    def change(self, **changes):
        row = {"name": "CH1", "project": "P-A", "requested_by": "team", "description": "Revise cable routing", "reason": "Ground conditions", "status": "Impact Analysis", "cost_impact": "100", "schedule_impact_days": "2", "material_impact": "Approved additional cable", "document_impact": "SLD revision required", "financial_approval_required": True, "affected_records": [{"project": "P-A", "name": "SLD", "type": "Document"}]}
        row.update(changes)
        return row

    def test_full_change_workflow_and_propagation(self):
        analysis = self.change()
        technical = dict(analysis, status="Technical Approval", technical_approver="engineer")
        validate_change_transition(technical, "engineer", ["P-A"], previous=analysis, can_approve_technical=True)
        financial = dict(technical, status="Financial Approval", financial_approver="finance")
        validate_change_transition(financial, "finance", ["P-A"], previous=technical, can_approve_financial=True)
        approved = dict(financial, status="Approved")
        validate_change_transition(approved, "finance", ["P-A"], previous=financial, can_approve_financial=True)
        implemented = dict(approved, status="Implemented", implemented_by="team")
        validate_change_transition(implemented, "team", ["P-A"], previous=approved)
        verified = dict(implemented, status="Verified", verified_by="engineer", verification_evidence=["changed-layout.pdf"])
        validate_change_transition(verified, "engineer", ["P-A"], previous=implemented, can_approve_technical=True)
        self.assertEqual(verified["affected_records"][0]["name"], "SLD")

    def test_technical_self_approval_blocked(self):
        with self.assertRaises(RuleViolation):
            validate_change_transition(self.change(status="Technical Approval", technical_approver="team"), "team", ["P-A"], previous=self.change(), can_approve_technical=True)

    def test_cannot_skip_financial_approval(self):
        technical = self.change(status="Technical Approval", technical_approver="engineer")
        with self.assertRaises(RuleViolation):
            validate_change_transition(dict(technical, status="Approved", financial_approver="finance"), "engineer", ["P-A"], previous=technical, can_approve_technical=True)

    def test_financial_and_technical_approvers_distinct(self):
        technical = self.change(status="Technical Approval", technical_approver="engineer")
        with self.assertRaises(RuleViolation):
            validate_change_transition(dict(technical, status="Financial Approval", financial_approver="engineer"), "engineer", ["P-A"], previous=technical, can_approve_financial=True)

    def test_approved_cost_and_scope_cannot_change(self):
        technical = self.change(status="Technical Approval", technical_approver="engineer")
        with self.assertRaises(RuleViolation):
            validate_change_transition(dict(technical, status="Financial Approval", financial_approver="finance", cost_impact=10000), "finance", ["P-A"], previous=technical, can_approve_financial=True)

    def test_impacted_record_cross_project_rejected(self):
        analysis = self.change(affected_records=[{"project": "P-B", "name": "SLD", "type": "Document"}])
        with self.assertRaises(RuleViolation):
            validate_change_transition(dict(analysis, status="Technical Approval", technical_approver="engineer"), "engineer", ["P-A"], previous=analysis, can_approve_technical=True)

    def test_unknown_policy_cannot_approve(self):
        analysis = self.change(financial_approval_required=None)
        with self.assertRaises(RuleViolation):
            validate_change_transition(dict(analysis, status="Technical Approval", technical_approver="engineer"), "engineer", ["P-A"], previous=analysis, can_approve_technical=True)


if __name__ == "__main__":
    unittest.main()
