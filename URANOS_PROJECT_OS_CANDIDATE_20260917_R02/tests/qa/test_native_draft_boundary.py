"""Draft preparation is not ledger posting; actual ORM remains a staging gate."""
import pytest

from conftest import FakeDocument


@pytest.mark.parametrize("purpose", ["Material Transfer", "Material Issue", "Material Receipt"])
@pytest.mark.parametrize("docstatus", [0, 1, 2])
def test_native_preparation_never_confers_posting_authority(adapter, monkeypatch, purpose, docstatus):
    adapter.frappe.get_roles = lambda user: ["URANOS Finance Controller"]
    monkeypatch.setattr(adapter.security, "validate_project_links", lambda doc: None)
    doc = FakeDocument({"doctype": "Stock Entry", "project": "P-A", "purpose": purpose, "docstatus": docstatus})
    if docstatus == 0:
        adapter.security.validate_standard_transaction(doc)
    else:
        with pytest.raises(adapter.frappe.PermissionError):
            adapter.security.validate_standard_transaction(doc)


def test_field_role_cannot_prepare_rate_bearing_native_entry(adapter, monkeypatch):
    adapter.frappe.get_roles = lambda user: ["URANOS Storekeeper"]
    monkeypatch.setattr(adapter.security, "validate_project_links", lambda doc: None)
    doc = FakeDocument({"doctype": "Stock Entry", "project": "P-A", "purpose": "Material Issue", "docstatus": 0})
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.security.validate_standard_transaction(doc)
