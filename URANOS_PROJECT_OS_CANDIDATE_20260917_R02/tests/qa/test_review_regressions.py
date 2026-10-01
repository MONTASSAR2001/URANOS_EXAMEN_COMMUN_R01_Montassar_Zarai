"""Acceptance assertions for independently identified defects.

These are intentionally ordinary assertions, not expected-failure/skip markers:
the integration branch must fix a demonstrated defect or retain a red gate.
"""
import pytest
from conftest import FakeDocument, Row


def test_pending_ncr_severity_cannot_be_downgraded_by_raw_write(adapter):
    old = FakeDocument({"doctype": "URANOS NCR", "status": "Pending Verification", "severity": "Critical"})
    doc = adapter.controllers.UranosDocument({**old, "severity": "Low"}, previous=old)
    with pytest.raises((adapter.frappe.PermissionError, adapter.frappe.ValidationError)):
        doc._guard_server_state()


def test_pending_ncr_correction_proof_cannot_change_by_raw_write(adapter):
    old = FakeDocument({"doctype": "URANOS NCR", "status": "Pending Verification", "corrective_action": "Original repair",
                        "before_evidence": [Row(file="BEFORE")], "after_evidence": [Row(file="AFTER")]})
    doc = adapter.controllers.UranosDocument({**old, "corrective_action": "Different repair"}, previous=old)
    with pytest.raises((adapter.frappe.PermissionError, adapter.frappe.ValidationError)):
        doc._guard_server_state()


@pytest.mark.parametrize("allocation,value", [("kit_issue", "KIT-ISSUE-1"), ("cable_reel", "REEL-1")])
def test_progress_correction_preserves_material_lineage(adapter, monkeypatch, allocation, value):
    old = FakeDocument({"doctype": "URANOS Field Progress Entry", "name": "PROGRESS-1", "project": "P-A",
        "work_package": "WP-A", "baseline_version": "B1", "activity": "Cable", "site": "S-A", "zone": "Z1",
        "crew": "C1", "posting_date": "2026-09-17", "status": "Verified", "qty_reported": 100,
        "qty_verified": 100, "reported_by": "reporter@example.invalid", "verifier": "reviewer@example.invalid",
        allocation: value, "evidence": ["EVIDENCE-1"]})
    monkeypatch.setattr(adapter.operations, "_locked", lambda *args: old)
    created = []

    def get_doc(values):
        created.append(FakeDocument(values))
        return created[-1]
    adapter.frappe.get_doc = get_doc
    adapter.operations.report_correction("PROGRESS-1", 80, "Verified damaged cable; replace prior contribution")
    assert created[0].get(allocation) == value


def _commissioning_fixture(adapter, monkeypatch, *, procedure="PROC-APPROVED", system_name="INVERTER-A"):
    dossier = FakeDocument({"project": "P-A", "work_package": "WP-A", "system_name": "INVERTER-A",
        "required_tests": [Row(code="INSULATION", required=1, acceptance_reference="PROC-APPROVED")],
        "required_documents": [Row(document_code="AS-BUILT", mandatory=1)], "punch_list": []})
    records = {
        "URANOS QA Test Result": [FakeDocument({"name": "TEST-A", "project": "P-A", "work_package": "WP-A",
            "system_name": system_name, "test_code": "INSULATION", "status": "Passed", "procedure_reference": procedure,
            "performed_by": "performer@example.invalid", "verifier": "qa@example.invalid", "evidence": ["FILE-A"]})],
        "URANOS Document Register": [FakeDocument({"name": "AS-BUILT-A", "project": "P-A", "document_code": "AS-BUILT",
            "revision": "1", "status": "As-built", "issuer": "issuer@example.invalid", "approver": "engineer@example.invalid",
            "file": "FILE-DOC", "is_current": 1})],
    }
    adapter.frappe.get_list = lambda doctype, **kwargs: [Row(name=record.name) for record in records.get(doctype, [])]
    monkeypatch.setattr(adapter.quality, "scoped_doc", lambda doctype, name: next(
        record for record in records[doctype] if record.name == name))
    return dossier


def test_commissioning_requires_matching_approved_procedure(adapter, monkeypatch):
    dossier = _commissioning_fixture(adapter, monkeypatch, procedure="UNRELATED-PROCEDURE")
    assessment = adapter.quality._dossier_assessment(dossier)
    assert not assessment["ready"], "Passed code alone must not satisfy an unrelated acceptance procedure"


def test_commissioning_cannot_reuse_another_equipment_test(adapter, monkeypatch):
    dossier = _commissioning_fixture(adapter, monkeypatch, system_name="INVERTER-B")
    assessment = adapter.quality._dossier_assessment(dossier)
    assert not assessment["ready"], "INVERTER-B proof must not commission INVERTER-A"
