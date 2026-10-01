"""Stock availability cannot be manufactured by reclassifying a warehouse."""
import pytest

from conftest import FakeDocument


@pytest.mark.parametrize("field,new", [("uranos_stock_state", "Available"), ("company", "OTHER"),
                                      ("is_group", 1), ("parent_warehouse", "OTHER")])
@pytest.mark.parametrize("trusted", [False, True])
def test_stock_service_capability_does_not_authorize_warehouse_reclassification(adapter, monkeypatch, field, new, trusted):
    old = FakeDocument({"doctype": "Warehouse", "uranos_project": "P-A", "uranos_stock_state": "Quarantine",
                        "company": "CO", "is_group": 0, "parent_warehouse": "P-A-GROUP"})
    doc = FakeDocument({**old, field: new}, previous=old)
    monkeypatch.setattr(adapter.security, "validate_project_links", lambda doc: None)
    if trusted:
        with adapter.controllers.authorized_transition(), pytest.raises(adapter.frappe.ValidationError):
            adapter.security.validate_standard_transaction(doc)
    else:
        with pytest.raises(adapter.frappe.ValidationError):
            adapter.security.validate_standard_transaction(doc)


def test_new_classified_warehouse_and_unchanged_metadata_remain_valid(adapter, monkeypatch):
    monkeypatch.setattr(adapter.security, "validate_project_links", lambda doc: None)
    old = FakeDocument({"doctype": "Warehouse", "uranos_project": "P-A", "uranos_stock_state": "Available",
                        "company": "CO", "is_group": 0, "parent_warehouse": "P-A-GROUP"})
    adapter.security.validate_standard_transaction(old)
    current = FakeDocument({**old, "warehouse_name": "Readable label"}, previous=old)
    adapter.security.validate_standard_transaction(current)
