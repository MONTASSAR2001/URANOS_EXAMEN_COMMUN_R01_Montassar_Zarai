"""Actual mixin guards with dependency fakes; disk/HTTP gates still need bench."""
import importlib
import sys

import pytest
from conftest import FakeDocument, Row


@pytest.fixture
def files(adapter, monkeypatch):
    sys.modules.pop("uranos_project_os.file_security", None)
    module = importlib.import_module("uranos_project_os.file_security")
    monkeypatch.setattr(module, "require_file_scope", lambda file, user=None: {("URANOS NCR", "NCR-A")})
    yield module
    sys.modules.pop("uranos_project_os.file_security", None)


@pytest.mark.parametrize("changes", [{"is_private": 0}, {"file_url": "/files/exposed.pdf"},
    {"attached_to_name": "NCR-B"}, {"attached_to_doctype": None, "attached_to_name": None},
    {"content_hash": "changed"}, {"content": b"replacement"}, {"owner": "other@example.invalid"}])
def test_project_evidence_mutations_fail_before_disk_write(adapter, files, changes):
    old = FakeDocument({"name": "FILE-A", "is_private": 1, "file_url": "/private/files/a.pdf",
        "content_hash": "unchanged", "attached_to_doctype": "URANOS NCR", "attached_to_name": "NCR-A",
        "owner": "field@example.invalid"})
    with pytest.raises((adapter.frappe.ValidationError, adapter.frappe.PermissionError)):
        files.guard_write(FakeDocument({**old, **changes}, previous=old))


def test_initial_private_upload_can_be_attached_once(adapter, files):
    old = FakeDocument({"name": "FILE-A", "is_private": 1, "file_url": "/private/files/a.pdf", "content_hash": "abc"})
    files.guard_write(FakeDocument({**old, "attached_to_doctype": "URANOS NCR", "attached_to_name": "NCR-A"}, previous=old))


def test_project_evidence_deletion_stops_before_base_method(adapter, files, monkeypatch):
    monkeypatch.setattr(files, "project_references", lambda file: {("URANOS NCR", "NCR-A")})
    doc = files.ProjectEvidenceFileMixin({"name": "FILE-A"})
    with pytest.raises(adapter.frappe.ValidationError):
        doc.on_trash()


def test_owner_download_denied_when_project_membership_removed(adapter, files, monkeypatch):
    def revoked(*args):
        adapter.frappe.throw("revoked", adapter.frappe.PermissionError)
    monkeypatch.setattr(files, "require_file_scope", revoked)
    doc = files.ProjectEvidenceFileMixin({"name": "FILE-A", "owner": adapter.frappe.session.user})
    assert doc.is_downloadable() is False
    with pytest.raises(adapter.frappe.PermissionError):
        doc.get_content()


def test_old_shared_alias_cannot_become_new_private_proof(adapter, files):
    adapter.frappe.get_all = lambda *args, **kwargs: [Row(name="OLD-SHARED"), Row(name="NEW-PROOF")]
    adapter.frappe.db.exists = lambda doctype, filters: doctype == "DocShare" and "OLD-SHARED" in filters["share_name"][1]
    with pytest.raises(adapter.frappe.PermissionError):
        files.require_unshared_blob(Row(name="NEW-PROOF", file_url="/private/files/shared.pdf"))
