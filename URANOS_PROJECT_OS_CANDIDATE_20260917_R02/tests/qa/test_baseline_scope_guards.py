"""IR-F03 raw-write boundary regressions, not Frappe integration evidence."""
import pytest
from conftest import FakeDocument


@pytest.mark.parametrize("old_value,new_value", [(None, '{"version":1,"baselines":[]}'),
    ('{"version":1,"baselines":[]}', '{"version":1,"baselines":[{"name":"B3"}]}')])
def test_raw_change_cannot_forge_or_rewrite_server_scope_snapshot(adapter, old_value, new_value):
    old = FakeDocument({"doctype": "URANOS Change Request", "status": "Impact Analysis", "scope_snapshot": old_value})
    doc = adapter.controllers.UranosDocument({**old, "scope_snapshot": new_value}, previous=old)
    with pytest.raises(adapter.frappe.PermissionError, match="scope_snapshot"):
        doc._guard_server_state()


def test_raw_insert_cannot_seed_legacy_approval_snapshot(adapter):
    doc = adapter.controllers.UranosDocument({"doctype": "URANOS Change Request", "status": "Proposed",
        "scope_snapshot": '{"version":1,"baselines":[]}'})
    with pytest.raises(adapter.frappe.PermissionError, match="scope_snapshot"):
        doc._guard_server_state()


@pytest.mark.parametrize("field", ["title", "site", "criticality"])
def test_applied_signed_scope_metadata_cannot_be_edited_raw(adapter, field):
    old = FakeDocument({"doctype": "URANOS Work Package", "status": "Planned", "baseline_approved": 1,
        "title": "Approved subject", "site": "SITE-A", "criticality": "Normal"})
    current = adapter.controllers.UranosDocument({**old, field: "Changed"}, previous=old)
    with pytest.raises(adapter.frappe.ValidationError):
        current._guard_server_state()
