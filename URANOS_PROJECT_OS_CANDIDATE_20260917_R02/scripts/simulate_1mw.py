"""Repeatable SYNTHETIC 1 MW domain oracle; never posts ERPNext transactions.

Run with PYTHONPATH=apps/uranos_project_os. No Frappe/database/network access.
--write-evidence writes only the two declared generated evidence artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import platform
import subprocess
import time
from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from uranos_project_os.domain import controls, logistics, offline, quality, stock


PROJECT = "DEMO-SYNTHETIC-PV-1MW"
NOW = datetime(2026, 9, 17, 8, tzinfo=timezone.utc)
FIELD_AT = NOW + timedelta(days=22)
TODAY = FIELD_AT.date()
VERSION = "DEMO-BASELINE-1"


def json_default(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(type(value).__name__)


def canonical(value):
    return json.dumps(value, default=json_default, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class Observation:
    sequence: int
    action: str
    canonical_snapshot: str
    previous_hash: str
    sha256: str


class EvidenceLog:
    """Append-only test observations, not an operational stock/progress ledger."""

    def __init__(self):
        self._events = ()
        self.checks = []

    def observe(self, action, result):
        previous = self._events[-1].sha256 if self._events else "0" * 64
        snapshot = canonical(result)
        digest = hashlib.sha256(canonical([len(self._events) + 1, action, snapshot, previous]).encode()).hexdigest()
        self._events += (Observation(len(self._events) + 1, action, snapshot, previous, digest),)

    def check(self, condition, label):
        if not condition:
            raise AssertionError(label)
        self.checks.append({"check": label, "status": "PASS"})

    def rejects(self, label, call):
        try:
            call()
        except ValueError as exc:
            self.checks.append({"check": label, "status": "PASS", "rejection": str(exc)})
            return
        raise AssertionError(f"Expected rejection: {label}")

    def verify_chain(self):
        previous = "0" * 64
        for event in self._events:
            if event.previous_hash != previous:
                raise AssertionError("Observation history was modified")
            expected = hashlib.sha256(canonical([event.sequence, event.action, event.canonical_snapshot, previous]).encode()).hexdigest()
            if event.sha256 != expected:
                raise AssertionError("Observation checksum mismatch")
            previous = event.sha256
        return previous

    @property
    def events(self):
        return self._events


def actor(name, capabilities, project=PROJECT):
    return stock.Actor("DEMO-" + name, {project}, set(capabilities))


def demo_baseline(project=PROJECT):
    # Engineering quantities and weights are explicitly invented demo fixtures.
    quantities = [1, 1000, 1000, 100, 2000, 100, 10, 1000, 1000, 1, 1, 1, 100, 1, 1, 1]
    weights = [2, 7, 10, 10, 18, 10, 5, 7, 8, 4, 4, 4, 4, 3, 2, 2]
    units = ["Milestone", "m", "Pile", "Table", "Module", "String", "Unit", "m", "m", "Unit", "Unit", "Unit", "Point", "System", "Milestone", "Milestone"]
    return controls.validate_baseline(project, VERSION, [
        {"name": f"{project}-WP-{index * 10:03}", "code": f"WP-{index * 10:03}", "project": project, "baseline_version": VERSION, "qty_planned": quantity, "weight": weight, "uom": unit}
        for index, (quantity, weight, unit) in enumerate(zip(quantities, weights, units), 1)
    ])


def pending_entry(name, wp, quantity, crew="A", project=PROJECT, **extra):
    row = {"name": name, "project": project, "work_package": wp, "baseline_version": VERSION, "activity": "DEMO-" + wp.rsplit("-", 1)[-1], "zone": "DEMO-ZONE-1", "crew": "DEMO-CREW-" + crew, "posting_date": TODAY.isoformat(), "qty_reported": quantity, "qty_verified": 0, "reported_by": "DEMO-TEAM-" + crew, "verifier": None, "status": "Pending Verification", "evidence": ["DEMO-EVIDENCE-" + name]}
    row.update(extra)
    return row


def verify_entry(pending, quantity, correction=None):
    controls.validate_progress_entry(pending, pending["reported_by"], [pending["project"]], correction=correction)
    return controls.validate_progress_entry(dict(pending, status="Verified", verifier="DEMO-CONTROLLER", qty_verified=quantity), "DEMO-CONTROLLER", [pending["project"]], previous=pending, correction=correction, can_verify=True)


def document(code, revision, status="IFC", project=PROJECT):
    return {"name": f"{project}-{code}-R{revision}", "project": project, "document_code": code, "revision": str(revision), "status": status, "issuer": "DEMO-ENGINEER", "approver": "DEMO-DIRECTOR", "file": f"/private/files/DEMO-{code}-R{revision}.pdf", "is_current": status != "Superseded"}


def run_scenario():
    log = EvidenceLog()
    baseline = demo_baseline()
    packages = {row["code"]: row for row in baseline["packages"]}
    log.observe("approved_synthetic_baseline", baseline)
    log.check(sum(row["weight"] for row in baseline["packages"]) == 100, "approved synthetic baseline weights equal 100")
    suppliers = ("DEMO-SUPPLIER-A", "DEMO-SUPPLIER-B")
    orders = (
        {"name": "DEMO-PO-1", "supplier": suppliers[0], "project": PROJECT, "docstatus": 1, "items": {"DEMO-MODULE-500W": 2000, "DEMO-STRUCTURE": 100, "DEMO-INVERTER": 10}},
        {"name": "DEMO-PO-2", "supplier": suppliers[1], "project": PROJECT, "docstatus": 1, "items": {"DEMO-CONNECTOR": 204, "DEMO-DC-CABLE": 3200}},
        {"name": "DEMO-PO-3", "supplier": suppliers[0], "project": PROJECT, "docstatus": 1, "items": {"DEMO-TRANSFORMER": 1, "DEMO-MV-STATION": 1, "DEMO-SCADA": 1}},
    )
    log.check(2000 * 500 == 1_000_000, "synthetic module nameplate total equals 1 MW DC")
    containers = (
        logistics.Container("DEMO-CONTAINER-1", "DEMO-SEAL-1", "DEMO-SHIP-1", PROJECT),
        logistics.Container("DEMO-CONTAINER-2", "DEMO-SEAL-2", "DEMO-SHIP-1", PROJECT),
        logistics.Container("DEMO-CONTAINER-3", "DEMO-SEAL-3", "DEMO-SHIP-2", PROJECT),
    )
    lines = [[], []]
    for order in orders:
        for index, (item, quantity) in enumerate(order["items"].items(), 1):
            shipment_index = 1 if order["name"] == "DEMO-PO-2" else 0
            container_no = containers[2].container_no if shipment_index else containers[0 if item == "DEMO-MODULE-500W" else 1].container_no
            lines[shipment_index].append(logistics.ShipmentLine(order["name"], f"{order['name']}-ROW-{index}", item, quantity, "m" if item == "DEMO-DC-CABLE" else "EA", container_no))
    shipments = [logistics.Shipment("DEMO-SHIP-1", PROJECT, NOW + timedelta(days=10), containers[:2], tuple(lines[0])), logistics.Shipment("DEMO-SHIP-2", PROJECT, NOW + timedelta(days=10), containers[2:], tuple(lines[1]))]
    tracker = actor("LOGISTICS", {"shipment_update"})

    def event(shipment, key, status, day, *, eta=None, receipts=()):
        at = NOW + timedelta(days=day)
        return logistics.ShipmentEvent(key, "DEMO-MANUAL-PROVIDER", shipment.shipment_id, PROJECT, status, "manual verified", at, at, "DEMO-SOURCE-" + key, tracker, eta, tuple(receipts))

    for index in range(2):
        shipments[index] = logistics.apply_shipment_event(shipments[index], event(shipments[index], f"DEMO-DEPART-{index}", "In Transit", 1))
    log.observe("procurement_and_departure", {"suppliers": suppliers, "orders": orders, "shipments": shipments})
    log.rejects("carrier status cannot manufacture site stock without Purchase Receipt evidence", lambda: logistics.apply_shipment_event(shipments[0], event(shipments[0], "DEMO-FAKE-RECEIPT", "Site Received", 2)))
    readiness_at_sea = logistics.evaluate_material_readiness(project=PROJECT, item_code="DEMO-MODULE-500W", uom="EA", required_qty=2000, need_date=(NOW + timedelta(days=12)).date(), supply=[logistics.PendingSupply("DEMO-ALLOC-MODULE", PROJECT, "DEMO-MODULE-500W", "EA", 2000, "In Transit", (NOW + timedelta(days=10)).date())])
    log.check(readiness_at_sea.on_site_available == 0 and not readiness_at_sea.ready_now, "material in transit does not count as stock on site")

    def receipt(shipment, line, quantity, suffix, day):
        return logistics.PurchaseReceiptEvidence("DEMO-PR-" + suffix, "DEMO-PR-ROW-" + suffix, PROJECT, shipment.shipment_id, line.purchase_order, line.purchase_order_item, line.item_code, quantity, line.uom, line.container_no, NOW + timedelta(days=day))

    module_line = shipments[0].items[0]
    partial_receipt = receipt(shipments[0], module_line, 1000, "PARTIAL-MODULES", 10)
    shipments[0] = logistics.apply_shipment_event(shipments[0], event(shipments[0], "DEMO-PARTIAL", "Trucking", 10, receipts=[partial_receipt]))
    log.check(shipments[0].status == "Trucking" and shipments[0].received_quantities[module_line.allocation_key] == 1000, "partial receipt remains partial and quantity is exact")
    log.rejects("partial receipt cannot close shipment", lambda: logistics.apply_shipment_event(shipments[0], event(shipments[0], "DEMO-PARTIAL-CLOSE", "Site Received", 11)))
    complete_first = [receipt(shipments[0], line, line.quantity - (1000 if line == module_line else 0), f"FINAL-{index}", 12) for index, line in enumerate(shipments[0].items)]
    shipments[0] = logistics.apply_shipment_event(shipments[0], event(shipments[0], "DEMO-SITE-1", "Site Received", 12, receipts=complete_first))
    shipments[1] = logistics.apply_shipment_event(shipments[1], event(shipments[1], "DEMO-DELAY", "In Transit", 5, eta=NOW + timedelta(days=18)))
    delay = logistics.shipment_alerts(shipments[1], threshold=timedelta(days=2), as_of=(NOW + timedelta(days=12)).date(), required_documents=["BL", "packing_list"], available_documents=["BL"], need_date=(NOW + timedelta(days=12)).date())
    log.check({row.rule for row in delay} >= {"eta_delay", "missing_documents", "after_need_date"}, "shipment delay, missing document and late-need alerts are visible")
    log.observe("partial_receipt_and_import_delay", {"received_first_shipment": [{"allocation": key, "quantity": value} for key, value in shipments[0].received_quantities.items()], "delayed_shipment": shipments[1], "alerts": delay})
    final_second = [receipt(shipments[1], line, line.quantity, f"SECOND-{index}", 18) for index, line in enumerate(shipments[1].items)]
    shipments[1] = logistics.apply_shipment_event(shipments[1], event(shipments[1], "DEMO-SITE-2", "Site Received", 18, receipts=final_second))
    for index in range(2):
        shipments[index] = logistics.apply_shipment_event(shipments[index], event(shipments[index], f"DEMO-CLOSE-{index}", "Closed", 19))

    engineering = actor("ENGINEER", {"kit_request"})
    engineering_approver = actor("ENGINEERING-APPROVER", {"kit_approve"})
    storekeeper = actor("STOREKEEPER", {"stock_issue", "stock_return", "stock_request"})
    crews = [actor("TEAM-A", {"stock_receive", "progress_report"}), actor("TEAM-B", {"stock_receive", "progress_report"})]
    controller = actor("CONTROLLER", {"progress_verify"})
    kit = stock.approve_kit_version(project=PROJECT, kit_code="DEMO-CONNECTOR-KIT", kit_version="DEMO-1", source_bom="DEMO-APPROVED-BOM-NOT-FOR-PRODUCTION", source_bom_version="DEMO-1", source_docstatus=1, items=[stock.BOMLine("DEMO-CONNECTOR", 2, "EA", "R3", 0)], requester=engineering, approver=engineering_approver, approved_at=NOW)

    def issue_kit(key, qty, crew):
        proof = stock.StockEntryEvidence("DEMO-STE-" + key, PROJECT, key, 1, "Material Transfer", (stock.StockLine("DEMO-CONNECTOR", Decimal(qty) * 2, "EA", "DEMO-AVAILABLE", "DEMO-WIP-" + crew.user),))
        return stock.build_kit_issue(issue_id=key, kit=kit, qty_kits=qty, stock_entry=proof, issuer=storekeeper, receiver=crew)

    kit_a, kit_b = issue_kit("DEMO-KIT-A", 50, crews[0]), issue_kit("DEMO-KIT-B", 50, crews[1])
    no_progress = controls.aggregate_progress(PROJECT, baseline, [])
    log.check(no_progress["physical_progress"] == 0, "issuing exact approved kits to two crews does not increase progress")
    pending = pending_entry("DEMO-MODULES-PARTIAL", packages["WP-050"]["name"], 1000)
    log.check(controls.aggregate_progress(PROJECT, baseline, [pending])["physical_progress"] == 0, "reported installation does not count before controller verification")
    verified_partial = verify_entry(pending, 800)
    entries = [verified_partial]
    partial_progress = controls.aggregate_progress(PROJECT, baseline, entries)
    log.check(partial_progress["physical_progress"] == Decimal("7.2"), "800 verified of 2000 modules at weight 18 yields 7.2 percent")
    rework_pending = pending_entry("DEMO-MODULES-REWORK", packages["WP-050"]["name"], 1000, correction_of=verified_partial["name"], revision_reason="DEMO: 20 modules require rework")
    rework = verify_entry(rework_pending, 780, verified_partial)
    entries.append(rework)
    log.check(controls.aggregate_progress(PROJECT, baseline, entries)["physical_progress"] == Decimal("7.02"), "rework correction replaces prior quantity without double counting")
    log.rejects("reporter cannot self-verify", lambda: controls.validate_progress_entry(dict(pending, status="Verified", qty_verified=800, verifier=pending["reported_by"]), pending["reported_by"], [PROJECT], previous=pending, can_verify=True))
    log.rejects("actor scoped to another project cannot verify", lambda: controls.validate_progress_entry(dict(pending, status="Verified", qty_verified=800, verifier="DEMO-CONTROLLER"), "DEMO-CONTROLLER", ["DEMO-OTHER-PROJECT"], previous=pending, can_verify=True))

    installed_a = stock.VerifiedConsumption("DEMO-CONSUME-A", PROJECT, kit_a.issue_id, "DEMO-CONNECTOR", 96, "EA", crews[0], controller)
    installed_b = stock.VerifiedConsumption("DEMO-CONSUME-B", PROJECT, kit_b.issue_id, "DEMO-CONNECTOR", 100, "EA", crews[1], controller)
    reconciliation_a = stock.reconcile_kit(kit_a, installed=[installed_a], as_of=TODAY)
    log.check(not reconciliation_a.can_close and reconciliation_a.lines[0].variance == 4, "loss of four connectors blocks kit closure")
    log.check(reconciliation_a.alerts[0].due_on == TODAY and not reconciliation_a.alerts[0].resolved, "high-risk connector variance is visible the same day")
    log.check(stock.reconcile_kit(kit_b, installed=[installed_b], as_of=TODAY).can_close, "second crew kit reconciles independently")
    reel = stock.CableReel("DEMO-REEL-1", PROJECT, "DEMO-DC-CABLE", "m", 3200, "DEMO-AVAILABLE", final_second[1].reference)

    def reel_movement(key, kind, length, crew, day, issue_id=None):
        source, target = ("DEMO-AVAILABLE", "DEMO-WIP-" + crew) if kind == "Issue" else ("DEMO-WIP-" + crew, "DEMO-AVAILABLE")
        proof = stock.StockEntryEvidence("DEMO-STE-" + key, PROJECT, reel.reel_id, 1, "Material Transfer", (stock.StockLine("DEMO-DC-CABLE", length, "m", source, target, reel.reel_id),))
        return stock.ReelMovement(key, reel.reel_id, PROJECT, kind, length, "DEMO-CIRCUIT-" + crew, proof, storekeeper, NOW + timedelta(days=day), issue_id)

    first_move = reel_movement("DEMO-CABLE-A", "Issue", 1600, "A", 20)
    reel = stock.apply_reel_movement(reel, first_move)
    reel = stock.apply_reel_movement(reel, reel_movement("DEMO-CABLE-B", "Issue", 1500, "B", 20))
    before_return = reel.current_expected_length
    reel = stock.apply_reel_movement(reel, reel_movement("DEMO-CABLE-RETURN-A", "Return", 80, "A", 21, first_move.movement_id))
    log.check(reel.current_expected_length == before_return + 80 == 180, "return preserves reel identity and restores 80 m to expected residual")
    log.rejects("reel cannot issue more than remaining length", lambda: stock.apply_reel_movement(reel, reel_movement("DEMO-CABLE-OVERISSUE", "Issue", 181, "A", 22)))
    cable_installation = [stock.VerifiedConsumption("DEMO-CABLE-CONSUME-" + crew.user, PROJECT, reel.reel_id, reel.item_code, 1500, "m", crew, controller) for crew in crews]
    cable_variance = stock.reconcile_reel(reel, measured_residual=180, installed=cable_installation, as_of=TODAY)
    log.check(cable_variance.unexplained == 20 and not cable_variance.can_close, "loss of 20 m cable blocks reel closure with identity retained")

    # Artificial currency/threshold values are test data, not URANOS policy/prices.
    policy = stock.ApprovalPolicy(PROJECT, "DEMO", Decimal(100))
    approvers = [actor("STOCK-APPROVER-1", {"stock_approve"}), actor("STOCK-APPROVER-2", {"stock_approve"})]

    def variance_disposition(key, subject, item, quantity):
        request = stock.Disposition(key, PROJECT, subject, item, "variance", Decimal(quantity), Decimal(101), "DEMO", "DEMO loss investigated; retain exception in history", storekeeper, FIELD_AT)
        log.rejects("unapproved loss cannot be authorized: " + key, lambda: stock.validate_adjustment(request, policy))
        one = replace(request, approvals=(stock.Approval(approvers[0], request.payload_digest, FIELD_AT + timedelta(hours=1)),))
        log.rejects("above synthetic threshold requires two approvers: " + key, lambda: stock.validate_adjustment(one, policy))
        approved = replace(request, approvals=tuple(stock.Approval(user, request.payload_digest, FIELD_AT + timedelta(hours=1)) for user in approvers))
        log.check(stock.validate_adjustment(approved, policy) == 2, "two named independent approvals bind exact loss: " + key)
        return approved

    approved_connector_loss = variance_disposition("DEMO-LOSS-4-CONNECTORS", kit_a.issue_id, "DEMO-CONNECTOR", 4)
    approved_cable_loss = variance_disposition("DEMO-LOSS-20M-CABLE", reel.reel_id, reel.item_code, 20)
    closed_a = stock.reconcile_kit(kit_a, installed=[installed_a], dispositions=[approved_connector_loss], policy=policy, as_of=TODAY)
    closed_reel = stock.reconcile_reel(reel, measured_residual=180, installed=cable_installation, dispositions=[approved_cable_loss], policy=policy, as_of=TODAY)
    log.check(closed_a.can_close and closed_reel.can_close, "approved losses permit reconciliation without deleting original variances")
    log.check(closed_a.lines[0].variance == 4 and closed_reel.approved_variance == 20, "loss quantities remain in immutable audit evidence")
    replacement_kit = issue_kit("DEMO-KIT-A-REPLACEMENT", 2, crews[0])
    replacement_consumption = stock.VerifiedConsumption("DEMO-CONSUME-REPLACEMENT", PROJECT, replacement_kit.issue_id, "DEMO-CONNECTOR", 4, "EA", crews[0], controller)
    log.check(stock.reconcile_kit(replacement_kit, installed=[replacement_consumption], as_of=TODAY).can_close, "four replacement connectors are issued and independently consumed")
    log.observe("losses_returns_and_independent_approvals", {"initial_connector_variance": reconciliation_a, "initial_cable_variance": cable_variance, "approved_connector_loss": approved_connector_loss, "approved_cable_loss": approved_cable_loss, "final_kit": closed_a, "final_reel": closed_reel})

    blocker = {"name": "DEMO-BLOCKER-CABLE", "project": PROJECT, "severity": "Critical", "status": "Open", "due_date": TODAY.isoformat()}
    ncr = {"name": "DEMO-NCR-TORQUE", "project": PROJECT, "status": "Open", "severity": "Critical", "requirement": "DEMO approved torque procedure reference, no numeric engineering limit", "defect": "DEMO test failure", "responsible": "DEMO-TEAM-A", "reported_by": "DEMO-QA", "corrected_by": "DEMO-TEAM-A", "due_date": TODAY.isoformat()}
    quality.validate_ncr_transition(ncr, "DEMO-QA", [PROJECT])
    before_dashboard = controls.dashboard_summary(PROJECT, partial_progress, planned_percent=20, material_readiness_percent=80, blockers=[blocker], ncrs=[ncr], stock_variances=[{"name": "DEMO-VARIANCE-CONNECTORS", "project": PROJECT, "risk_class": "R3", "variance": 4, "status": "Open"}], today=TODAY)
    log.check(before_dashboard["status"] == "Red" and before_dashboard["physical_progress"] != before_dashboard["material_readiness"], "critical blocker/NCR/variance cannot display green; material and physical KPIs differ")
    blocked_gate = controls.evaluate_stage_gate(PROJECT, 14, dict.fromkeys(controls.GATE_CONDITIONS[14], True), completed_gates=[0], ncrs=[ncr])
    log.check(not blocked_gate["ready"] and "ncr:DEMO-NCR-TORQUE" in blocked_gate["missing"], "critical NCR blocks commissioning milestone despite checked conditions")
    old_ifc = document("DEMO-SLD", 1)
    superseded = dict(old_ifc, status="Superseded", is_current=False)
    quality.validate_document_transition(superseded, "DEMO-DIRECTOR", [PROJECT], previous=old_ifc, can_approve=True)
    new_draft = dict(document("DEMO-SLD", 2, "Draft"), approver=None, supersedes=old_ifc["name"])
    quality.validate_document_transition(new_draft, "DEMO-ENGINEER", [PROJECT], supersedes=old_ifc)
    reviewed = dict(new_draft, status="Internal Review")
    quality.validate_document_transition(reviewed, "DEMO-ENGINEER", [PROJECT], previous=new_draft, supersedes=old_ifc)
    approved = dict(reviewed, status="Approved", approver="DEMO-DIRECTOR")
    quality.validate_document_transition(approved, "DEMO-DIRECTOR", [PROJECT], previous=reviewed, can_approve=True, supersedes=old_ifc)
    new_ifc = dict(approved, status="IFC")
    quality.validate_document_transition(new_ifc, "DEMO-DIRECTOR", [PROJECT], previous=approved, can_approve=True, supersedes=old_ifc)
    log.check(quality.current_ifc(PROJECT, "DEMO-SLD", [superseded, new_ifc])["revision"] == "2", "new IFC selected while superseded drawing cannot be current")
    log.check(quality.current_ifc(PROJECT, "DEMO-SLD", [superseded]) is None, "superseded drawing alone cannot satisfy IFC gate")
    missing_ifc = controls.evaluate_stage_gate(PROJECT, 1, dict.fromkeys(controls.GATE_CONDITIONS[1], True), completed_gates=[0], required_ifc_codes=["DEMO-SLD"], documents=[superseded])
    log.check(not missing_ifc["ready"], "engineering gate blocks missing current IFC")

    envelope_input = {"uuid": "974eb320-c38f-42cc-85ef-21099cfd7caa", "operation": "progress", "project": PROJECT, "payload": {key: value for key, value in pending.items() if key in offline.OPERATIONS["progress"]}}
    envelope = offline.validate_envelope(envelope_input)
    sync_receipt = {"sync_user": pending["reported_by"], "project": PROJECT, "payload_hash": envelope.payload_hash, "status": "Accepted", "reference_doctype": "URANOS Field Progress Entry", "reference_name": "DEMO-OFFLINE-DRAFT-1"}
    accepted_drafts = [sync_receipt["reference_name"]]
    for _ in range(3):
        retry = offline.check_retry(sync_receipt, pending["reported_by"], offline.validate_envelope(envelope_input))
        log.check(retry["duplicate"] and retry["docstatus"] == 0, "offline exact retry returns existing draft, never submits an approval")
    changed_envelope = offline.validate_envelope(dict(envelope_input, payload=dict(envelope_input["payload"], qty_reported=999)))
    log.rejects("offline reused UUID with changed payload conflicts", lambda: offline.check_retry(sync_receipt, pending["reported_by"], changed_envelope))
    log.check(len(accepted_drafts) == 1 and offline.receipt_identity(pending["reported_by"], envelope.uuid) != offline.receipt_identity("DEMO-OTHER-USER", envelope.uuid), "offline oracle preserves one draft identity and scopes UUID by actor")
    log.observe("offline_retry_oracle", {"drafts": accepted_drafts, "retry": retry, "payload_hash": envelope.payload_hash, "database_uniqueness_tested": False})

    # Resolve every physical work package with independently validated entries.
    repaired_pending = pending_entry("DEMO-MODULES-REPAIRED", packages["WP-050"]["name"], 1000, correction_of=rework["name"], revision_reason="DEMO rework inspected and original partial scope completed")
    entries.append(verify_entry(repaired_pending, 1000, rework))
    entries.append(verify_entry(pending_entry("DEMO-MODULES-B", packages["WP-050"]["name"], 1000, crew="B"), 1000))
    for code, package in packages.items():
        if code == "WP-050":
            continue
        entries.append(verify_entry(pending_entry("DEMO-COMPLETE-" + code, package["name"], package["qty_planned"]), package["qty_planned"]))
    final_progress = controls.aggregate_progress(PROJECT, baseline, entries)
    log.check(final_progress["physical_progress"] == 100 and all(row["completion_percent"] == 100 for row in final_progress["work_packages"]), "all sixteen packages reach exactly 100 percent verified without correction double counting")

    for status in ("Assigned", "Corrective Action"):
        candidate = dict(ncr, status=status)
        quality.validate_ncr_transition(candidate, "DEMO-TEAM-A", [PROJECT], previous=ncr)
        ncr = candidate
    candidate = dict(ncr, status="Pending Verification", corrective_action="DEMO corrective procedure performed", before_evidence=["DEMO-BEFORE"], after_evidence=["DEMO-AFTER"])
    quality.validate_ncr_transition(candidate, "DEMO-TEAM-A", [PROJECT], previous=ncr)
    ncr = candidate
    candidate = dict(ncr, status="Closed", closure_verifier="DEMO-QA", closure_verification="DEMO independent retest accepted")
    quality.validate_ncr_transition(candidate, "DEMO-QA", [PROJECT], previous=ncr, can_close=True)
    ncr = candidate
    blocker = dict(blocker, status="Resolved")
    hold = {"name": "DEMO-HOLD-ENERGIZATION", "project": PROJECT, "work_package": packages["WP-120"]["name"], "status": "Released", "result": "Passed", "procedure_reference": "DEMO-APPROVED-PROCEDURE", "performed_by": "DEMO-ELECTRICIAN", "verifier": "DEMO-QA", "evidence": ["DEMO-HOLD-RECORD"]}
    quality.validate_hold_release(hold, "DEMO-QA", [PROJECT], can_release=True)
    required_tests = ["DEMO-EARTHING", "DEMO-DC-INSULATION", "DEMO-POLARITY", "DEMO-AC-TERMINATION", "DEMO-INVERTER", "DEMO-MV", "DEMO-SCADA-PPC"]
    tests = [{"project": PROJECT, "test_code": code, "status": "Passed", "procedure_reference": "DEMO-APPROVED-PROCEDURE-" + code, "performed_by": "DEMO-ELECTRICIAN", "verifier": "DEMO-QA", "evidence": ["DEMO-TEST-EVIDENCE-" + code]} for code in required_tests]
    as_built_draft = dict(document("DEMO-SLD", "AB1", "Draft"), approver=None)
    quality.validate_document_transition(as_built_draft, "DEMO-ENGINEER", [PROJECT])
    as_built_review = dict(as_built_draft, status="Internal Review")
    quality.validate_document_transition(as_built_review, "DEMO-ENGINEER", [PROJECT], previous=as_built_draft)
    as_built = dict(as_built_review, status="As-built", approver="DEMO-DIRECTOR")
    quality.validate_document_transition(as_built, "DEMO-DIRECTOR", [PROJECT], previous=as_built_review, can_approve=True)
    dossier = quality.evaluate_commissioning(PROJECT, required_tests=required_tests, tests=tests, required_documents=["DEMO-SLD"], documents=[superseded, as_built], holds=[hold], ncrs=[ncr], punchlist=[{"name": "DEMO-PUNCH-1", "project": PROJECT, "status": "Closed"}])
    log.check(dossier["ready"], "seven evidenced engineering tests, as-built, hold release and QA closure satisfy commissioning")
    accepted = quality.validate_commissioning_acceptance({"project": PROJECT, "prepared_by": "DEMO-ELECTRICAL-MANAGER", "accepted_by": "DEMO-DIRECTOR", "acceptance_evidence": ["DEMO-ACCEPTANCE-RECORD"]}, dossier, actor="DEMO-DIRECTOR", permitted_projects=[PROJECT], can_accept=True)
    # Derive gate checklists from named scenario evidence, not an unconditional
    # "all true" shortcut. The underlying evidence remains explicitly synthetic.
    progress_by_code = {row["work_package"].rsplit("-WP-", 1)[-1]: row["completion_percent"] == 100 for row in final_progress["work_packages"]}
    complete = lambda code: progress_by_code[code]
    qa_clear = ncr["status"] == "Closed" and hold["status"] == "Released"
    test_pass = {row["test_code"]: row["status"] == "Passed" and bool(row["evidence"]) for row in tests}
    site_inspections = {code: {"project": PROJECT, "status": "Passed", "evidence": "DEMO-SITE-INSPECTION-" + code} for code in ("access", "safety", "resources")}
    layout_ifc = document("DEMO-LAYOUT", 1)
    gate_conditions = {
        0: {"project_identity": bool(PROJECT), "site_location": bool("DEMO-SITE-LOCATION"), "capacity": 2000 * 500 == 1_000_000, "client": bool("DEMO-CLIENT"), "responsible_people": len(crews) == 2, "scope": len(baseline["packages"]) == 16, "approved_baseline": sum(row["weight"] for row in baseline["packages"]) == 100, "warehouses": bool(reel.warehouse), "work_package_template": len(packages) == 16, "equipment_list": bool(orders)},
        1: {"layout_approved": quality.current_ifc(PROJECT, "DEMO-LAYOUT", [layout_ifc]) is not None, "sld_approved": quality.current_ifc(PROJECT, "DEMO-SLD", [superseded, new_ifc]) is not None, "material_lists_approved": bool(kit.source_bom and kit.approved_by), "revision_control": new_ifc.get("supersedes") == superseded["name"]},
        2: {"requirements_approved": bool(kit.approved_by), "purchase_orders_released": all(order["docstatus"] == 1 for order in orders)},
        3: {"shipments_registered": len(shipments) == 2, "transport_documents": all(shipment.status == "Closed" for shipment in shipments), "eta_reviewed": all(shipment.current_eta is not None for shipment in shipments)},
        4: {"site_warehouse": bool(reel.warehouse), "responsible_people": bool(crews), **{key + "_ready": site_inspections[key]["status"] == "Passed" and bool(site_inspections[key]["evidence"]) for key in site_inspections}},
        5: {"civil_scope_verified": complete("020")},
        6: {"piling_scope_verified": complete("030"), "piling_inspections_passed": qa_clear},
        7: {"structures_verified": complete("040"), "alignment_torque_passed": qa_clear},
        8: {"modules_verified": complete("050"), "module_inspections_passed": qa_clear},
        9: {"dc_scope_verified": complete("060"), "polarity_insulation_passed": test_pass["DEMO-POLARITY"] and test_pass["DEMO-DC-INSULATION"]},
        10: {"inverters_installed_verified": complete("070"), "connections_verified": qa_clear, "precommissioning_passed": test_pass["DEMO-INVERTER"]},
        11: {"trenches_verified": complete("080"), "cables_verified": complete("090"), "pre_backfill_inspections_passed": qa_clear},
        12: {"station_scope_verified": complete("100") and complete("110"), "mv_scope_verified": complete("120") and test_pass["DEMO-MV"], "earthing_tests_passed": complete("130") and test_pass["DEMO-EARTHING"]},
        13: {"communications_verified": complete("140"), "scada_ppc_tests_passed": test_pass["DEMO-SCADA-PPC"], "weather_integration_verified": complete("140") and qa_clear},
        14: {"commissioning_tests_passed": all(test_pass.values()), "commissioning_documents_complete": dossier["ready"], "punchlist_resolved": dossier["ready"]},
        15: {"as_built_complete": as_built["status"] == "As-built", "equipment_dossiers_complete": dossier["ready"], "certificates_complete": all(bool(row["evidence"]) for row in tests), "residual_stock_reconciled": closed_a.can_close and closed_reel.can_close, "handover_accepted": bool(accepted["acceptance_evidence"])},
    }
    completed_gates = []
    for gate in range(16):
        conditions = gate_conditions[gate]
        approvals = [{"project": PROJECT, "gate": gate, "status": "Approved", "approved_by": "DEMO-DIRECTOR", "requested_by": "DEMO-PROJECT-MANAGER"}]
        assessment = controls.evaluate_stage_gate(PROJECT, gate, conditions, completed_gates=completed_gates, prerequisite_gates=[gate - 1] if gate else [], required_ifc_codes=["DEMO-SLD"] if gate == 1 else [], documents=[superseded, new_ifc], holds=[hold], ncrs=[ncr], approvals=approvals, required_approvals=1)
        log.check(assessment["ready"], f"synthetic stage gate {gate} satisfies prerequisites and independent approval")
        completed_gates.append(gate)
    final_dashboard = controls.dashboard_summary(PROJECT, final_progress, planned_percent=100, material_readiness_percent=100, blockers=[blocker], ncrs=[ncr], stock_variances=[{"name": "DEMO-VARIANCE-CONNECTORS", "project": PROJECT, "risk_class": "R3", "variance": 4, "status": "Resolved"}], today=TODAY, finance={"project": PROJECT, "currency": "DEMO", "budget": 100, "committed": 90}, finance_allowed=False)
    log.check(final_dashboard["status"] == "Green" and "finance" not in final_dashboard, "final operational dashboard green only after risks resolved; finance absent for field view")
    daily_reports = [
        {"project": PROJECT, "day": "DEMO-PARTIAL", "progress": partial_progress, "stock_variances": {"connectors": 4, "cable_m": 20}, "dashboard": before_dashboard},
        {"project": PROJECT, "day": "DEMO-HANDOVER", "progress": final_progress, "stock_variances": {"approved_connectors": 4, "approved_cable_m": 20}, "dashboard": final_dashboard},
    ]
    log.observe("verified_handover_and_management_views", {"commissioning": dossier, "acceptance": accepted, "gate_conditions": gate_conditions, "gates": completed_gates, "daily_reports": daily_reports})
    digest = log.verify_chain()
    log.check(bool(digest), "append-only scenario observation hash chain verifies")
    return {"classification": "SYNTHETIC DOMAIN ORACLE ONLY", "project": PROJECT, "capacity_mw_dc": "1", "suppliers": len(suppliers), "purchase_orders": len(orders), "shipments": len(shipments), "containers": len(containers), "crews": len(crews), "kit_issues": 3, "reported_partial": "1000", "verified_partial": "800", "partial_progress_percent": partial_progress["physical_progress"], "final_progress_percent": final_progress["physical_progress"], "connector_loss": 4, "cable_loss_m": 20, "reel_remaining_m": reel.current_expected_length, "completed_gates": completed_gates, "commissioning_tests": len(required_tests), "offline_unique_drafts_in_oracle": len(accepted_drafts), "initial_risk_status": before_dashboard["status"], "final_risk_status": final_dashboard["status"], "checks": log.checks, "observations": [asdict(row) for row in log.events], "observation_chain_sha256": digest, "not_run": ["actual ERPNext supplier/PO/receipt/stock postings", "database concurrency and idempotency unique constraints", "Frappe User Permissions and production identities", "browser workflow and offline IndexedDB", "migrations", "backup and full DB/files restore", "engineering validation of real BOMs/test limits", "production deployment"]}


def run_benchmark(project_count=25, originals_per_project=400, movements_per_project=200, document_codes_per_project=25):
    """Measure domain workloads, never claim page/network/database response time."""
    started = time.perf_counter()
    progress_ms = stock_ms = document_ms = dashboard_ms = 0.0
    entry_count = movement_count = document_count = correction_count = 0
    percentages = []
    for index in range(project_count):
        project = f"DEMO-BENCH-{index:02}"
        wp = project + "-WP"
        baseline = controls.validate_baseline(project, VERSION, [{"name": wp, "project": project, "baseline_version": VERSION, "qty_planned": 1000, "weight": 100}])
        entries = []
        corrected_originals = 0
        restored_originals = 0
        for number in range(originals_per_project):
            original = dict(pending_entry(f"{project}-E-{number}", wp, 1, project=project), status="Verified", verifier="DEMO-CONTROLLER", qty_verified=1)
            entries.append(original)
            if number % 4 == 0:
                correction = dict(original, name=original["name"] + "-C1", correction_of=original["name"], revision_reason="DEMO correction benchmark", qty_verified="0.8")
                entries.append(correction)
                corrected_originals += 1
                correction_count += 1
                if number < 80:
                    for step, amount in ((2, "0.9"), (3, "1")):
                        correction = dict(correction, name=original["name"] + f"-C{step}", correction_of=correction["name"], qty_verified=amount)
                        entries.append(correction)
                        correction_count += 1
                    restored_originals += 1
        begin = time.perf_counter()
        progress = controls.aggregate_progress(project, baseline, entries)
        progress_ms += (time.perf_counter() - begin) * 1000
        expected = (Decimal(originals_per_project) - Decimal("0.2") * (corrected_originals - restored_originals)) / 10
        if progress["physical_progress"] != min(expected, Decimal(100)):
            raise AssertionError("benchmark correction lineage changed quantities")
        percentages.append(progress["physical_progress"])
        entry_count += len(entries)
        warehouse_actor = actor(f"BENCH-WAREHOUSE-{index}", {"stock_issue", "stock_return"}, project)
        reel = stock.CableReel(project + "-REEL", project, "DEMO-CABLE", "m", movements_per_project + 100, project + "-AVAILABLE", project + "-PR")
        begin = time.perf_counter()
        for number in range(movements_per_project):
            proof = stock.StockEntryEvidence(f"{project}-STE-{number}", project, reel.reel_id, 1, "Material Transfer", (stock.StockLine("DEMO-CABLE", 1, "m", reel.warehouse, project + "-WIP", reel.reel_id),))
            movement = stock.ReelMovement(f"{project}-MOVE-{number}", reel.reel_id, project, "Issue", 1, project + "-CIRCUIT", proof, warehouse_actor, NOW + timedelta(seconds=number))
            reel = stock.apply_reel_movement(reel, movement)
        stock_ms += (time.perf_counter() - begin) * 1000
        if reel.current_expected_length != 100:
            raise AssertionError("benchmark reel residual changed")
        movement_count += len(reel.movements)
        docs = [document(f"DEMO-DOC-{code}", revision, "IFC" if revision == 3 else "Superseded", project) for code in range(document_codes_per_project) for revision in range(4)]
        begin = time.perf_counter()
        for code in range(document_codes_per_project):
            if quality.current_ifc(project, f"DEMO-DOC-{code}", docs)["revision"] != "3":
                raise AssertionError("benchmark served superseded IFC")
        document_ms += (time.perf_counter() - begin) * 1000
        document_count += len(docs)
        begin = time.perf_counter()
        summary = controls.dashboard_summary(project, progress, planned_percent=50, material_readiness_percent=80, today=TODAY)
        dashboard_ms += (time.perf_counter() - begin) * 1000
        if summary["status"] == "Green":
            raise AssertionError("benchmark dashboard hid known delay")
    return {"classification": "SYNTHETIC DOMAIN PERFORMANCE ONLY", "projects": project_count, "progress_entries": entry_count, "correction_entries": correction_count, "stock_movements": movement_count, "documents": document_count, "ifc_lookups": project_count * document_codes_per_project, "portfolio_cards": project_count, "verified_percent_each_project": percentages, "timings_ms": {"all_work_including_fixture_construction": round((time.perf_counter() - started) * 1000, 3), "progress_aggregates": round(progress_ms, 3), "stock_movement_validation": round(stock_ms, 3), "document_current_ifc_lookup": round(document_ms, 3), "dashboard_projection": round(dashboard_ms, 3)}, "page_latency_tested": False, "sql_load_tested": False, "parallel_requests_tested": False}


def domain_fingerprints():
    result = {}
    for module in (controls, quality, stock, logistics, offline):
        path = Path(inspect.getfile(module)).resolve()
        result[module.__name__] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "source_file": path.relative_to(Path(__file__).resolve().parents[1]).as_posix()}
    return result


def render_report(result):
    scenario, benchmark = result["scenario"], result["benchmark"]
    checks = "\n".join(f"| {row['status']} | {row['check']} |" for row in scenario["checks"])
    timings = "\n".join(f"| {name} | {duration} |" for name, duration in benchmark["timings_ms"].items())
    omissions = "\n".join(f"- NOT RUN: {item}." for item in scenario["not_run"])
    hashes = "\n".join(f"- `{name}`: `{value['sha256']}`" for name, value in result["domain_sources"].items())
    return f"""# SYNTHETIC 1 MW domain simulation and 25-project benchmark

Generated by `scripts/simulate_1mw.py --write-evidence`, not a predetermined acceptance narrative. Evidence level: **pure domain oracle only**. All names, BOMs, quantities, approvals, currency values and engineering test references are DEMO fixtures. No ERPNext records were posted and no real engineering acceptance limit was inferred. The 1 MW DC label comes from 2,000 fictional 500 W modules.

Run UTC: {result['run_at_utc']}. Python: {result['python']}. Platform: {result['platform']}. Source repository revision observed: `{result['git_revision']}`. Root working files may contain uncommitted changes; module hashes below identify the exact tested domain source. Full machine-readable results and hash-chained observations: `domain_benchmark.json`.

## Reproduction

```powershell
$env:PYTHONPATH = 'apps/uranos_project_os'
.venv/Scripts/python.exe scripts/simulate_1mw.py --write-evidence
.venv/Scripts/python.exe -m unittest discover -s tests/scenarios -p 'test_1mw.py' -v
```

An isolated worktree may instead set PYTHONPATH to the integrating repository's absolute app path and use its absolute `.venv/Scripts/python.exe`; this run used that configuration. The script imports no Frappe/database implementation and requires only Python's standard library plus the five app domain modules.

## Observed scenario

{scenario['suppliers']} suppliers, {scenario['purchase_orders']} purchase orders, {scenario['shipments']} shipments and {scenario['containers']} containers; partial then full receipt; {scenario['crews']} crews and {scenario['kit_issues']} connector kit issues including an explicit replacement issue; partial verification; traceable rework; 4 connector and 20 m cable losses; independent bound approvals; identity-preserving cable return; delayed shipment; critical blocker/NCR; IFC revision; offline retry/conflict oracle; seven commissioning tests; gates 0–15; two generated daily-report projections and a management dashboard.

Partial physical progress: {scenario['partial_progress_percent']}%. Final verified physical progress: {scenario['final_progress_percent']}%. Initial risk status: {scenario['initial_risk_status']}; final: {scenario['final_risk_status']}. Reel measured/expected residual: {scenario['reel_remaining_m']} m. Field dashboard excludes finance. Independent loss approval permits closure while retaining the loss in the evidence history; it does not convert a loss into installation.

{len(scenario['checks'])} executed assertions/rejection checks passed. Append-only observation chain: `{scenario['observation_chain_sha256']}`. Snapshot JSON is serialized at observation time, so subsequent in-memory state changes cannot rewrite earlier evidence.

| Result | Executed assertion |
| --- | --- |
{checks}

## Measured domain benchmark

{benchmark['projects']} projects; {benchmark['progress_entries']} progress records including {benchmark['correction_entries']} correction records and multi-level lineage; {benchmark['stock_movements']} identity-preserving reel movements; {benchmark['documents']} document revisions; {benchmark['ifc_lookups']} current-IFC lookups and {benchmark['portfolio_cards']} dashboard projections. Quantities, residual lengths, correction contributions and IFC selection were asserted during the benchmark.

| Workload | Measured milliseconds |
| --- | ---: |
{timings}

These timings measure local deterministic Python, including repeated immutable reel validation. They are **not** browser page, SQL, concurrent request or production capacity timings. No production performance target is claimed.

## Exact tested source fingerprints

{hashes}

## Outstanding acceptance evidence

{omissions}

The offline check exercises `validate_envelope`, `receipt_identity` and `check_retry` against one synthetic existing receipt. It proves deterministic retry/conflict semantics; it does not prove transactional uniqueness, server rollback or simultaneous requests. Kit/receipt/approval evidence objects are synthetic substitutes for server-loaded submitted ERPNext documents. Gate conditions and test results are synthetic attestations, not real engineering inspection. Supplier/PO counts and daily reports are scenario projections, not ERP DocTypes or persisted reports. Live end-to-end acceptance and go-live remain separate gates.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    revision = "UNAVAILABLE (snapshot without Git history)"
    if (repository / ".git").exists():
        try:
            revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=False).stdout.strip() or "UNAVAILABLE"
        except FileNotFoundError:
            revision = "UNAVAILABLE (Git executable not installed)"
    result = {"run_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(), "platform": platform.platform(), "git_revision": revision, "domain_sources": domain_fingerprints(), "scenario": run_scenario(), "benchmark": run_benchmark()}
    if args.write_evidence:
        destination = repository / "docs" / "evidence"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "DOMAIN_1MW_SIMULATION.md").write_text(render_report(result), encoding="utf-8")
        (destination / "domain_benchmark.json").write_text(json.dumps(result, default=json_default, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scenario": {key: value for key, value in result["scenario"].items() if key not in {"checks", "observations"}}, "assertions_passed": len(result["scenario"]["checks"]), "benchmark": result["benchmark"]}, default=json_default, indent=2))


if __name__ == "__main__":
    main()
