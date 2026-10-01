"""Derived alert behavior with explicit dependency fakes, not scheduler proof."""
import importlib

from conftest import FakeDocument


def test_resolved_absent_risk_does_not_create_fake_alert(adapter):
    monitoring = importlib.import_module("uranos_project_os.services.monitoring")
    monitoring._maintain("P1", "URANOS NCR", "N1", "quality_blocker", "resolved", open_risk=False)


def test_repeated_alert_uses_stable_identity_and_no_stock_mutation(adapter):
    monitoring = importlib.import_module("uranos_project_os.services.monitoring")
    records = {}

    class Persisted(FakeDocument):
        def insert(self, **kwargs):
            records[self.name] = self
            return self
    adapter.frappe.get_doc = lambda *args: records[args[1]] if len(args) == 2 else Persisted(args[0])
    adapter.frappe.db.exists = lambda doctype, name: name in records
    for _ in range(3):
        monitoring._maintain("P1", "URANOS NCR", "N1", "quality_blocker", "needs review", severity="Critical")
    assert len(records) == 1
    record = next(iter(records.values()))
    assert record.doctype == "URANOS Executive Alert"
    assert record.status == "Open"
    monitoring._maintain("P1", "URANOS NCR", "N1", "quality_blocker", "closed", open_risk=False)
    assert record.status == "Resolved"
