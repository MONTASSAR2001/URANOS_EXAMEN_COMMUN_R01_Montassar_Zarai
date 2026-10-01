"""Synthetic examples only: none of these BOM quantities/thresholds are approved master data."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import unittest

from uranos_project_os.domain.stock import (
    Actor, Approval, ApprovalPolicy, BOMLine, CableReel, Disposition, KitVersion,
    ReelMovement, StockEntryEvidence, StockLine, StockRuleError, VerifiedConsumption,
    apply_reel_movement, approve_kit_version, build_kit_issue, quantity,
    reconcile_kit, reconcile_reel, validate_adjustment,
)


NOW = datetime(2026, 9, 17, 10, tzinfo=timezone.utc)
PROJECT = "DEMO-PV-1MW"


def actor(name, *capabilities, project=PROJECT):
    return Actor(name, frozenset({project}), frozenset(capabilities))


REQUESTER = actor("demo-storekeeper", "stock_request", "stock_issue", "stock_return")
REPORTER = actor("demo-team-lead", "progress_report", "stock_receive")
VERIFIER = actor("demo-controller", "progress_verify")
APPROVER = actor("demo-approval-one", "stock_approve")
APPROVER_TWO = actor("demo-approval-two", "stock_approve")
POLICY = ApprovalPolicy(PROJECT, "DEMO", Decimal("50"))


def disposition(*, kind="variance", subject="ISSUE-1", item="DEMO-CONNECTOR", amount="4", value="40", approvers=(APPROVER,), reference="DISP-1"):
    request = Disposition(reference, PROJECT, subject, item, kind, amount, value, "DEMO",
                          "Synthetic variance explanation", REQUESTER, NOW)
    return replace(request, approvals=tuple(Approval(a, request.payload_digest, NOW + timedelta(minutes=1)) for a in approvers))


def kit(*, items=None, existing=(), version="1", approver=None):
    return approve_kit_version(project=PROJECT, kit_code="DEMO-KIT", kit_version=version,
                               source_bom="DEMO-BOM", source_bom_version=version, source_docstatus=1,
                               items=items or (BOMLine("DEMO-CONNECTOR", "10", "EA", "R3", "5"),),
                               requester=actor("demo-engineer-author", "kit_request"),
                               approver=approver or actor("demo-engineer-reviewer", "kit_approve"),
                               approved_at=NOW, existing=existing)


def transfer(reference, subject, amount, *, item="DEMO-CONNECTOR", uom="EA", source="Available", target="WIP", identity=None, project=PROJECT):
    return StockEntryEvidence(reference, project, subject, 1, "Material Transfer",
                              (StockLine(item, amount, uom, source, target, identity),))


def issue(*, template=None):
    return build_kit_issue(issue_id="ISSUE-1", kit=template or kit(), qty_kits="10",
                           stock_entry=transfer("SE-ISSUE", "ISSUE-1", "100"),
                           issuer=REQUESTER, receiver=REPORTER)


def installed(amount="96", *, subject="ISSUE-1", item="DEMO-CONNECTOR", uom="EA", reference="VERIFIED-ROW-1"):
    return VerifiedConsumption(reference, PROJECT, subject, item, amount, uom, REPORTER, VERIFIER)


class NumericBoundaryTests(unittest.TestCase):
    def test_non_finite_negative_boolean_empty_and_missing_rejected(self):
        for value in ("NaN", "sNaN", "Infinity", "-Infinity", "-1", True, None, "", object()):
            with self.subTest(value=value), self.assertRaises(StockRuleError):
                quantity(value)

    def test_decimal_is_exact(self):
        self.assertEqual(quantity("0.1") + quantity("0.2"), Decimal("0.3"))

    def test_actors_are_immutable_and_scope_is_explicit(self):
        original = {PROJECT}
        scoped = Actor("user", original, {"stock_issue"})
        original.add("OTHER")
        with self.assertRaises(StockRuleError):
            scoped.require("OTHER", "stock_issue")
        with self.assertRaises(StockRuleError):
            Actor("", {PROJECT}, {"stock_issue"})


class ApprovalTests(unittest.TestCase):
    def test_no_threshold_fails_closed_even_for_tiny_adjustment(self):
        with self.assertRaises(StockRuleError):
            validate_adjustment(disposition(value="0.01"), None)

    def test_above_threshold_needs_two_distinct_approvers(self):
        with self.assertRaises(StockRuleError):
            validate_adjustment(disposition(value="50.01"), POLICY)
        self.assertEqual(validate_adjustment(disposition(value="50.01", approvers=(APPROVER, APPROVER_TWO)), POLICY), 2)
        self.assertEqual(validate_adjustment(disposition(value="50"), POLICY), 1)

    def test_no_self_approval_even_when_requester_has_approval_role(self):
        powerful = replace(REQUESTER, capabilities=REQUESTER.capabilities | {"stock_approve"})
        request = replace(disposition(), requested_by=powerful, approvals=())
        request = replace(request, approvals=(Approval(powerful, request.payload_digest, NOW),))
        with self.assertRaisesRegex(StockRuleError, "Self"):
            validate_adjustment(request, POLICY)

    def test_duplicate_identity_cannot_supply_two_signatures(self):
        with self.assertRaisesRegex(StockRuleError, "Duplicate"):
            validate_adjustment(disposition(value="100", approvers=(APPROVER, APPROVER)), POLICY)

    def test_wrong_project_role_currency_and_old_signature_rejected(self):
        for bad_actor in (actor("outsider", "stock_approve", project="OTHER"), actor("admin", "system_admin")):
            with self.subTest(actor=bad_actor.user), self.assertRaises(StockRuleError):
                validate_adjustment(disposition(approvers=(bad_actor,)), POLICY)
        for request in (replace(disposition(), quantity=Decimal(5)), replace(disposition(), value=Decimal(0)), replace(disposition(), currency="OTHER")):
            with self.subTest(request=request), self.assertRaises(StockRuleError):
                validate_adjustment(request, POLICY)

    def test_approval_before_request_and_missing_reason_rejected(self):
        request = disposition()
        with self.assertRaises(StockRuleError):
            validate_adjustment(replace(request, approvals=(replace(request.approvals[0], approved_at=NOW - timedelta(seconds=1)),)), POLICY)
        with self.assertRaises(StockRuleError):
            replace(request, reason=" ")


class KitTests(unittest.TestCase):
    def test_version_snapshot_is_immutable_and_new_versions_preserve_old(self):
        first = kit()
        self.assertIs(kit(existing=(first,)), first)
        with self.assertRaises(FrozenInstanceError):
            first.kit_version = "2"
        with self.assertRaises(StockRuleError):
            kit(items=(BOMLine("DEMO-CONNECTOR", "11", "EA", "R3", "5"),), existing=(first,))
        second = kit(version="2", items=(BOMLine("DEMO-CONNECTOR", "11", "EA", "R3", "5"),), existing=(first,))
        self.assertNotEqual(first.payload_digest, second.payload_digest)
        self.assertEqual(first.items[0].qty_per_unit, Decimal(10))

    def test_unapproved_bom_missing_tolerance_duplicate_and_self_approval_rejected(self):
        with self.assertRaises(StockRuleError):
            approve_kit_version(project=PROJECT, kit_code="K", kit_version="1", source_bom="B", source_bom_version="1",
                                source_docstatus=0, items=kit().items, requester=actor("author", "kit_request"),
                                approver=actor("reviewer", "kit_approve"), approved_at=NOW)
        with self.assertRaises(StockRuleError):
            BOMLine("ITEM", 1, "EA", "R3", None)
        with self.assertRaises(StockRuleError):
            kit(items=(*kit().items, *kit().items))
        with self.assertRaises(StockRuleError):
            kit(approver=actor("demo-engineer-author", "kit_approve"))

    def test_issue_must_match_bom_exactly_and_use_submitted_stock_entry(self):
        for entry in (transfer("SE", "ISSUE-1", "99"), transfer("SE", "ISSUE-1", "100", uom="BOX"),
                      transfer("SE", "ISSUE-1", "100", project="OTHER"), transfer("SE", "OTHER", "100")):
            with self.subTest(entry=entry), self.assertRaises(StockRuleError):
                build_kit_issue(issue_id="ISSUE-1", kit=kit(), qty_kits="10", stock_entry=entry, issuer=REQUESTER, receiver=REPORTER)
        with self.assertRaises(StockRuleError):
            replace(transfer("SE", "ISSUE-1", "100"), docstatus=0)
        with self.assertRaises(StockRuleError):
            replace(transfer("SE", "ISSUE-1", "100"), purpose="Material Issue")

    def test_issued_stock_never_equals_installed_progress(self):
        result = reconcile_kit(issue(), as_of=date(2026, 9, 17))
        self.assertEqual(result.lines[0].verified_installed, 0)
        self.assertEqual(result.lines[0].unexplained, 100)
        self.assertFalse(result.can_close)

    def test_small_r3_variance_alerts_same_day_and_cannot_close_with_unexplained_loss(self):
        result = reconcile_kit(issue(), installed=(installed(),), as_of=date(2026, 9, 17))
        self.assertFalse(result.lines[0].over_tolerance)
        self.assertEqual(result.lines[0].variance, 4)
        self.assertFalse(result.can_close)
        self.assertEqual(result.alerts[0].due_on, date(2026, 9, 17))
        self.assertFalse(result.alerts[0].resolved)

    def test_approved_variance_closes_but_preserves_visible_loss_evidence(self):
        result = reconcile_kit(issue(), installed=(installed(),), dispositions=(disposition(),), policy=POLICY, as_of=date(2026, 9, 17))
        self.assertTrue(result.can_close)
        self.assertEqual(result.lines[0].variance, 4)
        self.assertEqual(result.lines[0].approved_variance, 4)
        self.assertTrue(result.alerts[0].resolved)

    def test_return_plus_approved_scrap_can_reconcile(self):
        result = reconcile_kit(issue(), installed=(installed("90"),),
                               returns=(transfer("SE-RETURN", "ISSUE-1", "8", source="WIP", target="Available"),),
                               dispositions=(disposition(kind="scrap", amount="2"),), policy=POLICY, as_of=date(2026, 9, 17))
        self.assertTrue(result.can_close)
        self.assertEqual(result.lines[0].returned, 8)

    def test_invalid_return_route_duplicate_evidence_and_cross_project_rejected(self):
        kwargs = dict(as_of=date(2026, 9, 17))
        invalid_inputs = [dict(installed=(installed(), installed())),
                          dict(installed=(replace(installed(), subject_id="OTHER"),)),
                          dict(installed=(installed("101"),)),
                          dict(returns=(transfer("RETURN", "ISSUE-1", "4", source="OtherWarehouse", target="Available"),)),
                          dict(dispositions=(replace(disposition(), subject_id="OTHER"),), policy=POLICY)]
        for arguments in invalid_inputs:
            with self.subTest(arguments=arguments), self.assertRaises(StockRuleError):
                reconcile_kit(issue(), **kwargs, **arguments)

    def test_self_verified_or_draft_consumption_rejected(self):
        with self.assertRaises(StockRuleError):
            replace(installed(), reporter=actor("same", "progress_report"), verifier=actor("same", "progress_verify"))
        with self.assertRaises(StockRuleError):
            replace(installed(), docstatus=0)

    def test_tracked_identity_is_preserved_on_kit_return(self):
        tracked = replace(issue(), stock_entry=transfer("SE-ISSUE", "ISSUE-1", "100", identity="SEALED-PACK-1"))
        with self.assertRaisesRegex(StockRuleError, "identity"):
            reconcile_kit(tracked, returns=(transfer("SE-RETURN", "ISSUE-1", "100", source="WIP", target="Available", identity="WRONG-PACK"),), as_of=NOW.date())

    def test_multiple_tracked_packs_sum_to_bom_but_cannot_cross_subsidize_returns(self):
        evidence = StockEntryEvidence("SE-ISSUE", PROJECT, "ISSUE-1", 1, "Material Transfer",
                                      (StockLine("DEMO-CONNECTOR", 60, "EA", "Available", "WIP", "PACK-1"),
                                       StockLine("DEMO-CONNECTOR", 40, "EA", "Available", "WIP", "PACK-2")))
        tracked = replace(issue(), stock_entry=evidence)
        returned = transfer("SE-RETURN", "ISSUE-1", "50", source="WIP", target="Available", identity="PACK-2")
        with self.assertRaisesRegex(StockRuleError, "tracked identity"):
            reconcile_kit(tracked, returns=(returned,), as_of=NOW.date())
        valid = replace(returned, items=(replace(returned.items[0], quantity=40),))
        result = reconcile_kit(tracked, installed=(installed("60"),), returns=(valid,), as_of=NOW.date())
        self.assertTrue(result.can_close)


def reel():
    return CableReel("REEL-1", PROJECT, "DEMO-CABLE", "M", "1000", "Available", "DEMO-PR-1")


def movement(*, reference="MOVE-1", amount="200", kind="Issue", original=None, circuit="CIRCUIT-1", at=NOW):
    evidence = transfer("SE-" + reference, "REEL-1", amount, item="DEMO-CABLE", uom="M", identity="REEL-1",
                        source="Available" if kind == "Issue" else "WIP", target="WIP" if kind == "Issue" else "Available")
    return ReelMovement(reference, "REEL-1", PROJECT, kind, amount, circuit, evidence, REQUESTER, at, original)


class ReelTests(unittest.TestCase):
    def test_issue_preserves_identity_and_retry_is_exactly_once(self):
        first = apply_reel_movement(reel(), movement())
        self.assertEqual(first.current_expected_length, 800)
        self.assertEqual(len(first.movements), 1)
        self.assertIs(apply_reel_movement(first, movement()), first)
        with self.assertRaises(StockRuleError):
            apply_reel_movement(first, movement(amount="201"))

    def test_reel_cannot_over_issue_or_lose_identity(self):
        for invalid in (movement(amount="1001"), replace(movement(), reel_id="REEL-2"),
                        replace(movement(), stock_entry=transfer("SE", "REEL-1", "200", item="DEMO-CABLE", uom="M"))):
            with self.subTest(invalid=invalid), self.assertRaises(StockRuleError):
                apply_reel_movement(reel(), invalid)

    def test_return_tracks_original_circuit_length_and_stock_route(self):
        first = apply_reel_movement(reel(), movement())
        restored = apply_reel_movement(first, movement(reference="RETURN-1", kind="Return", original="MOVE-1", amount="30"))
        self.assertEqual(restored.current_expected_length, 830)
        for invalid in (movement(reference="R", kind="Return", original="MOVE-1", amount="201"),
                        movement(reference="R", kind="Return", original="MISSING", amount="1"),
                        movement(reference="R", kind="Return", original="MOVE-1", amount="1", circuit="WRONG")):
            with self.subTest(invalid=invalid), self.assertRaises(StockRuleError):
                apply_reel_movement(first, invalid)

    def test_history_reuse_and_backdated_movements_rejected(self):
        first = apply_reel_movement(reel(), movement())
        with self.assertRaises(StockRuleError):
            apply_reel_movement(first, replace(movement(), movement_id="DIFFERENT"))
        with self.assertRaises(StockRuleError):
            apply_reel_movement(first, movement(reference="OLDER", amount="1", at=NOW - timedelta(seconds=1)))

    def test_twenty_meter_loss_and_measured_residual_are_separate(self):
        first = apply_reel_movement(reel(), movement())
        evidence = installed("180", subject="REEL-1", item="DEMO-CABLE", uom="M")
        result = reconcile_reel(first, measured_residual="800", installed=(evidence,), as_of=NOW.date())
        self.assertEqual(result.unexplained, 20)
        self.assertFalse(result.can_close)
        self.assertEqual(result.alerts[0].quantity, 20)
        self.assertEqual(result.alerts[0].due_on, NOW.date())
        approval = disposition(subject="REEL-1", item="DEMO-CABLE", amount="20", value="100", approvers=(APPROVER, APPROVER_TWO))
        closed = reconcile_reel(first, measured_residual="800", installed=(evidence,), dispositions=(approval,), policy=POLICY, as_of=NOW.date())
        self.assertTrue(closed.can_close)
        self.assertTrue(closed.alerts[0].resolved)
        residual_mismatch = reconcile_reel(first, measured_residual="799", installed=(evidence,), dispositions=(approval,), policy=POLICY, as_of=NOW.date())
        self.assertFalse(residual_mismatch.can_close)
        self.assertEqual(residual_mismatch.alerts[-1].rule, "reel_residual_mismatch")

    def test_cross_project_verified_reel_data_and_overcount_rejected(self):
        first = apply_reel_movement(reel(), movement())
        for evidence in (installed("201", subject="REEL-1", item="DEMO-CABLE", uom="M"),
                         installed("200", subject="REEL-2", item="DEMO-CABLE", uom="M")):
            with self.assertRaises(StockRuleError):
                reconcile_reel(first, measured_residual="800", installed=(evidence,), as_of=NOW.date())

    def test_reel_conservation_over_many_partial_return_lengths(self):
        for issued in (1, 7, 100, 333, 1000):
            for returned in (0, issued // 2, issued):
                with self.subTest(issued=issued, returned=returned):
                    current = apply_reel_movement(reel(), movement(amount=issued))
                    if returned:
                        current = apply_reel_movement(current, movement(reference="RETURN", amount=returned, kind="Return", original="MOVE-1"))
                    consumed = issued - returned
                    proofs = (installed(consumed, subject="REEL-1", item="DEMO-CABLE", uom="M"),) if consumed else ()
                    result = reconcile_reel(current, measured_residual=1000 - consumed, installed=proofs, as_of=NOW.date())
                    self.assertTrue(result.can_close)
                    self.assertEqual(result.expected_residual + result.issued_net, 1000)


if __name__ == "__main__":
    unittest.main()
