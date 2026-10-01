"""Executable boundary tests; mocks do not demonstrate real Frappe enforcement."""
import pytest
from conftest import FakeDocument, Row


def test_mutation_rejects_get_request(adapter):
    adapter.frappe.local.request.method = "GET"
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.common.require_post()


def test_unauthenticated_user_is_rejected(adapter):
    adapter.frappe.session.user = "Guest"
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.security.current_user()


def test_empty_scope_denies_even_executive(adapter):
    adapter.frappe.get_roles = lambda user: ["URANOS Executive"]
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.security.require_project("P-A")


def test_doctype_restricted_grant_does_not_become_global(adapter):
    adapter.frappe.get_all = lambda *args, **kwargs: [Row(for_value="P-A", apply_to_all_doctypes=0,
        applicable_for="URANOS Daily Site Report")]
    assert adapter.security.allowed_projects() == frozenset()
    assert adapter.security.allowed_projects(doctype="URANOS Field Progress Entry") == frozenset()
    assert adapter.security.allowed_projects(doctype="URANOS Daily Site Report") == {"P-A"}


def test_administrator_is_not_business_approver(adapter):
    adapter.frappe.session.user = "Administrator"
    adapter.frappe.get_roles = lambda user: ["System Manager"]
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.security.require_roles("Site Controller")


def test_financial_record_denied_to_field_role(adapter):
    adapter.frappe.get_all = lambda *args, **kwargs: [Row(for_value="P-A", apply_to_all_doctypes=1)]
    assert not adapter.security.has_permission(FakeDocument({"doctype": "Purchase Order", "project": "P-A"}))


def test_sync_receipt_read_is_actor_bound(adapter):
    adapter.frappe.get_all = lambda *args, **kwargs: [Row(for_value="P-A", apply_to_all_doctypes=1)]
    doc = FakeDocument({"doctype": "URANOS Offline Sync Receipt", "project": "P-A", "sync_user": "other@example.invalid"})
    assert not adapter.security.has_permission(doc)
    assert "sync_user" in adapter.security.scoped_query(doc.doctype)


def test_docshare_cannot_add_alternate_project_access(adapter):
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.security.reject_project_sharing(Row(share_doctype="URANOS Daily Site Report"))


def test_client_document_flag_cannot_enable_transition(adapter):
    doc = adapter.controllers.UranosDocument({"doctype": "URANOS Daily Site Report", "status": "Approved"})
    doc.flags.uranos_authorized_transition = True
    with pytest.raises(adapter.frappe.PermissionError):
        doc._guard_server_state()


def test_private_transition_capability_unwinds_on_error(adapter):
    assert not adapter.controllers.transition_is_authorized()
    with pytest.raises(RuntimeError), adapter.controllers.authorized_transition():
        assert adapter.controllers.transition_is_authorized()
        raise RuntimeError("synthetic service failure")
    assert not adapter.controllers.transition_is_authorized()


def test_public_file_rejected_at_evidence_boundary(adapter):
    file = FakeDocument({"doctype": "File", "is_private": 0})
    adapter.frappe.get_doc = lambda *args: file
    doc = FakeDocument({"doctype": "URANOS Field Progress Entry", "project": "P-A"},
                       children=[Row(doctype="URANOS Evidence", file="FILE-A")])
    with pytest.raises(adapter.frappe.ValidationError):
        adapter.security.validate_evidence(doc)


def test_foreign_project_private_evidence_rejected(adapter):
    file = FakeDocument({"doctype": "File", "is_private": 1, "attached_to_doctype": "URANOS Daily Site Report",
                         "attached_to_name": "B-REPORT"})
    foreign = FakeDocument({"doctype": "URANOS Daily Site Report", "project": "P-B"})
    adapter.frappe.get_doc = lambda doctype, name: file if doctype == "File" else foreign
    doc = FakeDocument({"doctype": "URANOS Field Progress Entry", "project": "P-A"},
                       children=[Row(doctype="URANOS Evidence", file="FILE-B")])
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.security.validate_evidence(doc)


def test_foreign_owner_unattached_upload_rejected(adapter):
    file = FakeDocument({"doctype": "File", "is_private": 1, "owner": "other@example.invalid"})
    adapter.frappe.get_doc = lambda *args: file
    doc = FakeDocument({"doctype": "URANOS Field Progress Entry", "project": "P-A"},
                       children=[Row(doctype="URANOS Evidence", file="FILE-B")])
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.security.validate_evidence(doc)


def test_cross_project_doc_is_denied_before_return(adapter):
    adapter.frappe.get_doc = lambda *args: FakeDocument({"doctype": "URANOS Daily Site Report", "project": "P-B"})
    adapter.frappe.get_all = lambda *args, **kwargs: [Row(for_value="P-A", apply_to_all_doctypes=1)]
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.common.scoped_doc("URANOS Daily Site Report", "REPORT-B")


def test_original_actor_cannot_change_even_in_trusted_transition(adapter):
    old = FakeDocument({"doctype": "URANOS Field Progress Entry", "status": "Draft", "reported_by": "first@example.invalid"})
    doc = adapter.controllers.UranosDocument({**old, "reported_by": "other@example.invalid"}, previous=old)
    with adapter.controllers.authorized_transition(), pytest.raises(adapter.frappe.ValidationError):
        doc._guard_server_state()


def test_dashboard_does_not_fetch_finance_for_field_actor(adapter, monkeypatch):
    monkeypatch.setattr(adapter.security, "require_project", lambda *args, **kwargs: "P-A")
    monkeypatch.setattr(adapter.api, "_progress", lambda project: {"project": project, "physical_progress": None,
        "work_packages": [], "missing_data": ["approved_baseline"]})
    monkeypatch.setattr(adapter.api, "_all_rows", lambda *args, **kwargs: [])
    queries = []
    monkeypatch.setattr(adapter.api, "project_rows", lambda doctype, *args, **kwargs: queries.append(doctype) or [])
    result = adapter.api.dashboard("P-A")
    assert "costs" not in result
    assert "URANOS Project Cost" not in queries
    assert result["physical_progress"] is None
    assert result["status"] != "Green"


def test_authenticated_scope_declares_no_store_at_server_boundary(adapter):
    adapter.frappe.local.response_headers["Vary"] = "Accept-Encoding"
    adapter.security.current_user()
    adapter.security.current_user()
    assert adapter.frappe.local.response_headers["Cache-Control"] == "no-store, private"
    assert adapter.frappe.local.response_headers["Pragma"] == "no-cache"
    assert adapter.frappe.local.response_headers["Vary"] == "Accept-Encoding, Cookie"
