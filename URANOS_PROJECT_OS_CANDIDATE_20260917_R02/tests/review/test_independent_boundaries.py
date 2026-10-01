"""Independent acceptance regressions; no skip/xfail and no real ERP claim."""
import importlib
import json
from pathlib import Path
import sys

import pytest

from conftest import FakeDocument, Row
from uranos_project_os.domain.quality import evaluate_commissioning


@pytest.mark.parametrize("purpose", ["Repack", "Manufacture", "Material Consumption for Manufacture"])
def test_native_stock_transformations_cannot_bypass_controlled_approval(adapter, monkeypatch, purpose):
    """A raw Finance-role stock POST must not become an alternate loss write-off."""
    adapter.frappe.get_roles = lambda user: ["URANOS Finance Controller"]
    monkeypatch.setattr(adapter.security, "validate_project_links", lambda doc: None)
    doc = FakeDocument({"doctype": "Stock Entry", "project": "P-A", "purpose": purpose})
    with pytest.raises((adapter.frappe.PermissionError, adapter.frappe.ValidationError)):
        adapter.security.validate_standard_transaction(doc)


def _retest_inputs():
    original = {"name": "TEST-FAILED", "project": "P-A", "test_code": "INSULATION",
                "system_name": "INVERTER-A", "procedure_reference": "APPROVED-PROC-1",
                "status": "Failed", "performed_by": "electrician@example.invalid",
                "verifier": "qa@example.invalid", "evidence": ["FAILED-EVIDENCE"]}
    replacement = {**original, "name": "TEST-RETEST", "status": "Passed", "supersedes": original["name"],
                   "revision_reason": "Repair completed; same controlled procedure repeated", "evidence": ["RETEST-EVIDENCE"]}
    document = {"name": "AS-BUILT-1", "project": "P-A", "document_code": "AS-BUILT",
                "revision": "1", "status": "As-built", "is_current": 1,
                "issuer": "drafter@example.invalid", "approver": "engineer@example.invalid", "file": "PLAN-1"}
    return original, replacement, document


def test_explicit_independent_retest_can_resolve_failed_commissioning_test():
    """An attributable replacement, not deletion/overwriting, must allow recovery.

    This expresses the required retest lineage contract. The adapter must load
    these records itself, validate immutable subject/procedure and serialize
    competing successor approvals; a client-supplied supersedes flag is not proof.
    """
    original, replacement, document = _retest_inputs()
    result = evaluate_commissioning("P-A", required_tests=["INSULATION"], tests=[original, replacement],
                                   required_documents=["AS-BUILT"], documents=[document])
    assert result["ready"] is True


def test_unrelated_duplicate_test_is_not_silently_selected():
    original, replacement, document = _retest_inputs()
    replacement.pop("supersedes")
    with pytest.raises(ValueError):
        evaluate_commissioning("P-A", required_tests=["INSULATION"], tests=[original, replacement],
                               required_documents=["AS-BUILT"], documents=[document])


@pytest.mark.parametrize("field,value", [("system_name", "INVERTER-B"), ("procedure_reference", "OTHER-PROCEDURE"),
                                        ("test_code", "OTHER-TEST")])
def test_retest_cannot_change_controlled_subject(adapter, field, value):
    original, replacement, document = _retest_inputs()
    replacement[field] = value
    with pytest.raises(ValueError):
        evaluate_commissioning("P-A", required_tests=["INSULATION"], tests=[original, replacement],
                               required_documents=["AS-BUILT"], documents=[document])


def test_retest_cannot_fork_an_accepted_result():
    original, replacement, document = _retest_inputs()
    competitor = {**replacement, "name": "SECOND-RETEST"}
    with pytest.raises(ValueError):
        evaluate_commissioning("P-A", required_tests=["INSULATION"], tests=[original, replacement, competitor],
                               required_documents=["AS-BUILT"], documents=[document])


def test_finance_approver_reaches_stock_policy_without_generic_write_grant(adapter, monkeypatch):
    """Use generated role rows, not an unconditional mocked permission success."""
    materials = importlib.import_module("uranos_project_os.services.materials")
    schema_path = Path(materials.__file__).parents[1] / "uranos_project_os" / "doctype" / "uranos_stock_disposition" / "uranos_stock_disposition.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    role = "URANOS Finance Controller"
    adapter.frappe.get_roles = lambda user: [role]
    disposition = FakeDocument({"doctype": schema["name"], "name": "LOSS-1", "project": "P-A",
                                "status": "Pending Approval", "requester": "store@example.invalid", "policy": "POLICY-1"})

    def scoped(doctype, name, *, permission="read", **kwargs):
        if doctype == "Project":
            return FakeDocument({"name": "P-A", "doctype": "Project"})
        if not any(row.get("role") == role and row.get("permlevel", 0) == 0 and row.get(permission)
                   for row in schema["permissions"]):
            raise adapter.frappe.PermissionError("Generated schema denies " + permission)
        return disposition

    class ReachedPolicy(Exception):
        pass

    def policy(*args):
        raise ReachedPolicy

    monkeypatch.setattr(materials, "scoped_doc", scoped)
    monkeypatch.setattr(materials, "_policy", policy)
    with pytest.raises(ReachedPolicy):
        materials.approve_stock_disposition("LOSS-1")


def _file_module(adapter, monkeypatch):
    adapter.frappe.db.table_exists = lambda doctype: True
    monkeypatch.delitem(sys.modules, "uranos_project_os.file_security", raising=False)
    return importlib.import_module("uranos_project_os.file_security")


def test_revoked_project_grant_denies_the_original_file_owner(adapter, monkeypatch):
    files = _file_module(adapter, monkeypatch)
    file = FakeDocument({"doctype": "File", "name": "FILE-A", "owner": adapter.frappe.session.user,
                         "file_url": "/private/files/evidence.jpg", "is_private": 1})
    monkeypatch.setattr(files, "project_references", lambda doc: {("URANOS Field Progress Entry", "PROGRESS-A")})
    adapter.frappe.db.get_value = lambda *args, **kwargs: "P-A"
    # No current project grant, even though the same user originally uploaded it.
    with pytest.raises(adapter.frappe.PermissionError):
        files.require_file_scope(file)


def test_duplicate_private_url_cannot_hide_foreign_project_attachment(adapter, monkeypatch):
    files = _file_module(adapter, monkeypatch)
    alias = FakeDocument({"doctype": "File", "name": "NEW-ALIAS", "owner": adapter.frappe.session.user,
                          "file_url": "/private/files/foreign.jpg", "is_private": 1})
    foreign = Row(name="FILE-B", attached_to_doctype="URANOS Field Progress Entry", attached_to_name="PROGRESS-B")
    adapter.frappe.get_all = lambda doctype, **kwargs: [foreign] if doctype == "File" else []
    adapter.frappe.db.get_value = lambda *args, **kwargs: "P-B"
    with pytest.raises(adapter.frappe.PermissionError):
        files.guard_write(alias)


def test_referenced_private_file_cannot_be_made_public(adapter, monkeypatch):
    files = _file_module(adapter, monkeypatch)
    old = FakeDocument({"doctype": "File", "name": "FILE-A", "file_url": "/private/files/evidence.jpg", "is_private": 1})
    changed = FakeDocument({**old, "is_private": 0}, previous=old)
    monkeypatch.setattr(files, "require_file_scope", lambda doc: {("URANOS Field Progress Entry", "PROGRESS-A")})
    with pytest.raises((adapter.frappe.PermissionError, adapter.frappe.ValidationError)):
        files.guard_write(changed)


def test_file_listing_has_project_scope_hook(adapter, monkeypatch):
    """Presence-only gate; SQL and REST isolation still require a real site test."""
    monkeypatch.delitem(sys.modules, "uranos_project_os.hooks", raising=False)
    hooks = importlib.import_module("uranos_project_os.hooks")
    assert "File" in hooks.permission_query_conditions, "Native File listing scopes by readable type, not parent project"


def test_shared_blob_alias_cannot_become_project_evidence(adapter, monkeypatch):
    files = _file_module(adapter, monkeypatch)
    file = FakeDocument({"doctype": "File", "name": "FILE-B", "file_url": "/private/files/shared.jpg", "is_private": 1})
    monkeypatch.setattr(files, "require_file_scope", lambda doc: {("URANOS Field Progress Entry", "PROGRESS-A")})
    adapter.frappe.get_all = lambda doctype, **kwargs: (["FILE-A", "FILE-B"] if kwargs.get("pluck") else
        [Row(name="FILE-A"), Row(name="FILE-B")]) if doctype == "File" else []
    adapter.frappe.db.exists = lambda doctype, filters: doctype == "DocShare" and "FILE-A" in str(filters)
    with pytest.raises((adapter.frappe.PermissionError, adapter.frappe.ValidationError)):
        files.guard_write(file)


def test_kit_consumption_rejects_module_vs_table_units(adapter, monkeypatch):
    materials = importlib.import_module("uranos_project_os.services.materials")
    issue = FakeDocument({"project": "P-A", "name": "KIT-1", "kit_template": "TEMPLATE-1", "work_package": "WP-1"})
    monkeypatch.setattr(materials, "scoped_doc", lambda doctype, name: FakeDocument(
        {"output_uom": "Table"} if doctype == "URANOS Material Kit Template" else {"uom": "Module"}))
    with pytest.raises((adapter.frappe.PermissionError, adapter.frappe.ValidationError)):
        materials._kit_installed(issue, None)


def test_historical_material_actor_does_not_reauthorize_a_departed_user(adapter, monkeypatch):
    materials = importlib.import_module("uranos_project_os.services.materials")
    # The helper is private: only persisted immutable Verified/Posted records
    # may feed it. This test checks separation, not provenance persistence.
    adapter.frappe.get_roles = lambda user: []
    historical = materials._historical_actor("P-A", "departed@example.invalid", "progress_verify")
    assert historical.user == "departed@example.invalid"
    with pytest.raises(adapter.frappe.PermissionError):
        materials._actor("P-A", "departed@example.invalid", "progress_verify")
