"""Native locking API contract; real transaction isolation remains NOT RUN."""
import pytest

from conftest import FakeDocument, Row


def test_locked_read_fetches_current_parent_children_and_rechecks_permission(adapter):
    first = FakeDocument({"doctype": "URANOS Baseline", "project": "P-A", "status": "Draft"})
    current = FakeDocument({"doctype": "URANOS Baseline", "project": "P-A", "status": "Approved"})
    calls = []

    def get_doc(doctype, name, **kwargs):
        calls.append((doctype, name, kwargs))
        return current if kwargs.get("for_update") else first

    adapter.frappe.get_doc = get_doc
    adapter.frappe.get_all = lambda *args, **kwargs: [Row(for_value="P-A", apply_to_all_doctypes=1)]
    result = adapter.common.scoped_doc("URANOS Baseline", "BASE", permission="write", lock=True)
    assert result is current
    assert calls[-1] == ("URANOS Baseline", "BASE", {"for_update": True})
    assert first.permission_checks == current.permission_checks == ["write"]


def test_scope_is_checked_again_on_the_current_locked_record(adapter):
    def get_doc(doctype, name, **kwargs):
        return FakeDocument({"doctype": doctype, "project": "P-B" if kwargs.get("for_update") else "P-A"})
    adapter.frappe.get_doc = get_doc
    adapter.frappe.get_all = lambda *args, **kwargs: [Row(for_value="P-A", apply_to_all_doctypes=1)]
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.common.scoped_doc("URANOS Baseline", "BASE", lock=True)
