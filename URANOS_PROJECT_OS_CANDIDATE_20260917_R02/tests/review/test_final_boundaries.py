"""Final bounded review regressions. Explicit dependency fake, not live ERP."""
import json
import importlib
from datetime import date
from pathlib import Path
import re

import pytest

from conftest import FakeDocument, Row


def test_unrelated_accepted_inspection_cannot_release_a_procedure_specific_hold(adapter, monkeypatch):
    user = adapter.frappe.session.user
    hold = FakeDocument({"doctype": "URANOS Hold Point", "name": "HOLD-INSULATION", "project": "P-A",
        "work_package": "WP-DC", "zone": "Z1", "status": "Open", "inspection": "INSPECT-VISUAL",
        "procedure_reference": "PROC-INSULATION-R1", "performed_by": "installer@example.invalid",
        "evidence": ["FILE-INSULATION"]})
    inspection = FakeDocument({"doctype": "URANOS Field Inspection", "name": "INSPECT-VISUAL", "project": "P-A",
        "work_package": "WP-DC", "zone": "Z1", "status": "Accepted", "verifier": user,
        "inspection_type": "Module Visual", "procedure_reference": "PROC-VISUAL-R1", "hold_point": "HOLD-VISUAL"})
    monkeypatch.setattr(adapter.quality, "_locked", lambda *args: hold)
    monkeypatch.setattr(adapter.quality, "scoped_doc", lambda *args, **kwargs: inspection)
    monkeypatch.setattr(adapter.security, "validate_evidence", lambda doc: None)
    monkeypatch.setattr(adapter.quality, "_save", lambda doc: {"name": doc.name, "status": doc.status})
    with pytest.raises((adapter.frappe.PermissionError, adapter.frappe.ValidationError)):
        adapter.quality.release_hold(hold.name)


def _hold_documents():
    subject = {"project": "P-A", "work_package": "WP-DC", "activity": "ACT-INSULATION", "zone": "Z1",
               "procedure_reference": "PROC-INSULATION-R1", "procedure_document": "DOC-INSULATION-R1"}
    hold = FakeDocument({"doctype": "URANOS Hold Point", "name": "HOLD-INSULATION", **subject})
    inspection = FakeDocument({"doctype": "URANOS Field Inspection", "name": "INSPECT-INSULATION",
                               "hold_point": hold.name, **subject})
    procedure = FakeDocument({"doctype": "URANOS Document Register", "name": "DOC-INSULATION-R1",
        "project": "P-A", "status": "IFC", "is_current": 1, "file": "FILE-PROC",
        "issuer": "engineer@example.invalid", "approver": "reviewer@example.invalid"})
    return hold, inspection, procedure


@pytest.mark.parametrize("field", ["hold_point", "project", "work_package", "activity", "zone",
                                    "procedure_reference", "procedure_document"])
def test_hold_inspection_rejects_each_changed_subject_coordinate(adapter, monkeypatch, field):
    hold, inspection, procedure = _hold_documents()
    inspection[field] = "OTHER"
    monkeypatch.setattr(adapter.quality, "scoped_doc", lambda *args, **kwargs: procedure)
    monkeypatch.setattr(adapter.security, "validate_evidence", lambda doc: None)
    with pytest.raises(adapter.frappe.ValidationError):
        adapter.quality._validate_hold_inspection(hold, inspection)


@pytest.mark.parametrize("change", [{"status": "Draft"}, {"is_current": 0}, {"file": None},
                                   {"approver": None}, {"approver": "engineer@example.invalid"},
                                   {"project": "P-B"}])
def test_hold_inspection_rejects_unapproved_or_unusable_procedure(adapter, monkeypatch, change):
    hold, inspection, procedure = _hold_documents()
    procedure.update(change)
    monkeypatch.setattr(adapter.quality, "scoped_doc", lambda *args, **kwargs: procedure)
    monkeypatch.setattr(adapter.security, "validate_evidence", lambda doc: None)
    with pytest.raises(adapter.frappe.ValidationError):
        adapter.quality._validate_hold_inspection(hold, inspection)


def test_exact_hold_and_independently_approved_procedure_reaches_evidence_check(adapter, monkeypatch):
    hold, inspection, procedure = _hold_documents()
    seen = []
    monkeypatch.setattr(adapter.quality, "scoped_doc", lambda *args, **kwargs: procedure)
    monkeypatch.setattr(adapter.security, "validate_evidence", lambda doc: seen.append(doc.name))
    adapter.quality._validate_hold_inspection(hold, inspection)
    assert seen == ["DOC-INSULATION-R1"]


def test_finance_only_user_is_a_supported_dashboard_actor(adapter):
    assert "Finance Controller" in adapter.api.FIELD_ROLES
    root = Path(adapter.api.__file__).parents[1]
    source = (root / "public" / "field" / "app.js").read_text(encoding="utf-8")
    control = re.search(r"control:\s*\[([^\]]+)\]", source)
    assert control and '"Finance Controller"' in control.group(1)


@pytest.mark.parametrize("doctype", ["Project Profile", "Baseline", "Work Package", "Field Progress Entry",
                                    "Blocker", "NCR", "Shipment", "Executive Alert"])
def test_finance_dashboard_dependencies_have_read_not_write_permission(adapter, doctype):
    root = Path(adapter.api.__file__).parents[1] / "uranos_project_os" / "doctype"
    slug = "uranos_" + doctype.lower().replace(" ", "_")
    schema = json.loads((root / slug / (slug + ".json")).read_text(encoding="utf-8"))
    rows = [row for row in schema["permissions"] if row["role"] == "URANOS Finance Controller" and row.get("permlevel", 0) == 0]
    assert rows and any(row.get("read") for row in rows)
    assert not any(row.get("write") or row.get("create") or row.get("submit") for row in rows)


@pytest.mark.parametrize("status", ["Approved", "Implemented", "Verified", "Closed"])
def test_unrelated_approved_change_cannot_authorize_a_baseline_revision(adapter, monkeypatch, status):
    adapter.frappe.get_roles = lambda user: ["URANOS Engineering Director"]
    monkeypatch.setattr(adapter.security, "allowed_projects", lambda *args, **kwargs: frozenset({"P-A"}))
    wp = FakeDocument({"doctype": "URANOS Work Package", "name": "WP-NEW", "project": "P-A",
        "baseline_version": "2", "code": "050", "uom": "Nos", "qty_planned": 999999, "weight": 100,
        "baseline_start": "2026-09-17", "baseline_finish": "2026-09-18"})
    line = Row({field: wp[field] for field in ("code", "uom", "qty_planned", "weight", "baseline_start", "baseline_finish")})
    line.work_package = wp.name
    baseline = FakeDocument({"doctype": "URANOS Baseline", "name": "BASE-NEW", "project": "P-A",
        "version": "2", "status": "Draft", "owner": "planner@example.invalid", "packages": [line],
        "supersedes": "BASE-OLD", "change_request": "CHANGE-TASK-ONLY"})
    change = FakeDocument({"doctype": "URANOS Change Request", "name": "CHANGE-TASK-ONLY", "project": "P-A",
        "status": status, "impacted_objects": [Row(reference_doctype="Task", reference_name="TASK-SIGNAGE", impact="Signage update only")]})
    previous = FakeDocument({"doctype": "URANOS Baseline", "name": "BASE-OLD", "project": "P-A", "status": "Approved"})
    profile = FakeDocument({"doctype": "URANOS Project Profile", "name": "PROFILE", "project": "P-A", "current_baseline": previous.name})
    project = FakeDocument({"doctype": "Project", "name": "P-A", "company": "DEMO-CO"})
    docs = {doc.name: doc for doc in (wp, baseline, change, previous, profile, project)}
    monkeypatch.setattr(adapter.operations, "_locked", lambda *args: baseline)
    monkeypatch.setattr(adapter.operations, "scoped_doc", lambda doctype, name, **kwargs: docs[name])
    monkeypatch.setattr(adapter.operations, "_save", lambda doc: {"name": doc.name, "status": doc.status})
    adapter.frappe.get_doc = lambda doctype, name: docs[name]
    adapter.frappe.db.get_value = lambda doctype, name, field: "P-A" if (doctype, name, field) == ("Task", "TASK-SIGNAGE", "project") else None
    adapter.frappe.get_list = lambda doctype, **kwargs: [Row(name=profile.name)] if doctype == profile.doctype else []
    with pytest.raises((adapter.frappe.PermissionError, adapter.frappe.ValidationError), match="[Bb]aseline|scope|target|snapshot"):
        adapter.operations.approve_baseline(baseline.name)


def _signed_baseline_fixture(adapter, monkeypatch):
    """Real capture/digest/authorization code; dependency reads are explicit fakes."""
    changes = importlib.import_module("uranos_project_os.services.changes")
    monkeypatch.setattr(adapter.security, "allowed_projects", lambda *args, **kwargs: frozenset({"P-A"}))
    adapter.frappe.utils.getdate = lambda value=None: date.fromisoformat(str(value)) if value else date(2026, 9, 17)
    wp = FakeDocument({"doctype": "URANOS Work Package", "name": "WP-2", "project": "P-A", "baseline_version": "2",
        "code": "050", "uom": "Nos", "qty_planned": 2000, "weight": 100,
        "baseline_start": "2026-09-17", "baseline_finish": "2026-09-30",
        "required_documents": [Row(document_code="IFC-MODULE", required_status="IFC", mandatory=1)]})
    line = Row({field: wp[field] for field in ("code", "uom", "qty_planned", "weight", "baseline_start", "baseline_finish")})
    line.work_package = wp.name
    baseline = FakeDocument({"doctype": "URANOS Baseline", "name": "BASE-2", "project": "P-A", "version": "2",
        "status": "Draft", "supersedes": "BASE-1", "change_request": "CR-BASE-2", "packages": [line]})
    change = FakeDocument({"doctype": "URANOS Change Request", "name": "CR-BASE-2", "project": "P-A", "status": "Approved",
        "requested_by": "planner@example.invalid", "technical_approver": "engineer@example.invalid",
        "description": "Exact new baseline scope", "reason": "Approved synthetic change", "cost_impact": 0,
        "schedule_impact_days": 0, "financial_approval_required": 0, "cost_assessed": 1,
        "cost_assessed_by": "finance@example.invalid", "currency": "DEMO", "policy": "POLICY-1",
        "impacted_objects": [Row(reference_doctype=baseline.doctype, reference_name=baseline.name, impact="Apply exact baseline revision")]})
    previous = FakeDocument({"doctype": baseline.doctype, "name": "BASE-1", "project": "P-A", "status": "Approved"})
    alternative = FakeDocument({"doctype": baseline.doctype, "name": "BASE-OTHER", "project": "P-A", "status": "Superseded"})
    project = FakeDocument({"doctype": "Project", "name": "P-A", "company": "DEMO-CO"})
    policy = FakeDocument({"doctype": "URANOS Approval Policy", "name": "POLICY-1", "project": "P-A",
        "action": "Change Cost", "first_role": "URANOS Finance Controller", "second_role": "URANOS Executive",
        "currency": "DEMO", "threshold": 100, "valid_from": "2026-09-01", "valid_to": "2026-09-30",
        "approved_by": "executive@example.invalid", "owner": "finance@example.invalid"})
    docs = {doc.name: doc for doc in (wp, baseline, previous, alternative, project, change, policy)}
    monkeypatch.setattr(changes, "scoped_doc", lambda doctype, name, **kwargs: docs[name])
    adapter.frappe.get_doc = lambda doctype, name: docs[name]
    adapter.frappe.db.get_value = lambda doctype, name, field: "DEMO" if doctype == "Company" else docs[name].get(field)
    affected = changes._affected(change)
    change.scope_snapshot = json.dumps(changes._capture_scope(change, affected, draft=True))
    change.cost_assessment_hash = change.payload_hash = changes._digest(change, policy, affected)
    return changes, change, baseline, wp, line


@pytest.mark.parametrize("field,value", [("qty_planned", 999999), ("weight", 99), ("uom", "Table"),
    ("baseline_start", "2026-09-18"), ("baseline_finish", "2026-10-01")])
def test_changed_baseline_quantity_unit_weight_or_dates_invalidates_signed_scope(adapter, monkeypatch, field, value):
    changes, change, baseline, wp, line = _signed_baseline_fixture(adapter, monkeypatch)
    wp[field] = line[field] = value
    with pytest.raises((adapter.frappe.ValidationError, ValueError)):
        changes.verify_baseline_authorization(change, baseline)


@pytest.mark.parametrize("mutation", ["documents", "predecessor", "other_target", "legacy_snapshot", "changed_digest"])
def test_baseline_authorization_is_not_reusable_for_different_or_unassessed_scope(adapter, monkeypatch, mutation):
    changes, change, baseline, wp, _line = _signed_baseline_fixture(adapter, monkeypatch)
    if mutation == "documents":
        wp.required_documents[0].mandatory = 0
    elif mutation == "predecessor":
        baseline.supersedes = "BASE-OTHER"
    elif mutation == "other_target":
        baseline = FakeDocument({**baseline, "name": "BASE-3"})
    elif mutation == "legacy_snapshot":
        change.scope_snapshot = None
    else:
        change.payload_hash = "tampered"
    with pytest.raises(adapter.frappe.ValidationError, match="scope|snapshot|baseline|revision|signature"):
        changes.verify_baseline_authorization(change, baseline)


def test_exact_signed_baseline_remains_verifiable_after_application_flags_change(adapter, monkeypatch):
    changes, change, baseline, wp, _line = _signed_baseline_fixture(adapter, monkeypatch)
    changes.verify_baseline_authorization(change, baseline)
    baseline.status = "Approved"
    baseline.approved_at = "2026-09-17 13:00:00"
    wp.baseline, wp.baseline_approved = baseline.name, 1
    changes.verify_baseline_authorization(change, baseline)


@pytest.mark.parametrize("previous_state", ["Receiving", "Quarantine", "WIP", "Returns"])
def test_warehouse_state_cannot_reclassify_recorded_stock_as_available(adapter, monkeypatch, previous_state):
    """Changing metadata must not substitute for a controlled stock release."""
    adapter.frappe.get_roles = lambda user: ["URANOS Project Manager"]
    monkeypatch.setattr(adapter.security, "allowed_projects", lambda *args, **kwargs: frozenset({"P-A"}))
    adapter.frappe.db.exists = lambda *args, **kwargs: True  # Existing ledger/history, if inspected.
    old = FakeDocument({"doctype": "Warehouse", "name": "WH-RECEIVING", "uranos_project": "P-A",
        "company": "DEMO-CO", "uranos_stock_state": previous_state})
    changed = FakeDocument({**old, "uranos_stock_state": "Available"}, previous=old)
    with pytest.raises((adapter.frappe.PermissionError, adapter.frappe.ValidationError)):
        adapter.security.validate_standard_transaction(changed)
