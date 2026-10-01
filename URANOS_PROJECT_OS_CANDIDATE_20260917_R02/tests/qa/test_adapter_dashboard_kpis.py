"""Executable boundary tests for Portfolio Dashboard KPIs adapter."""
from datetime import datetime
import pytest
from conftest import FakeDocument, Row


def test_api_requires_authenticated_user(adapter):
    adapter.frappe.session.user = "Guest"
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.api.get_dashboard_kpis()


def test_api_requires_authorized_business_role(adapter):
    adapter.frappe.session.user = "unauthorized@example.invalid"
    adapter.frappe.get_roles = lambda user: ["Customer"]
    with pytest.raises(adapter.frappe.PermissionError):
        adapter.api.get_dashboard_kpis()


def test_api_scopes_metrics_to_allowed_projects(adapter, monkeypatch):
    adapter.frappe.session.user = "engineer@example.invalid"
    adapter.frappe.get_roles = lambda user: ["URANOS Site Controller"]
    monkeypatch.setattr(adapter.security, "allowed_projects", lambda user: frozenset({"PV-01"}))

    sample_projects = [
        FakeDocument({"name": "PV-01", "project_name": "Centrale 1", "status": "Open"}),
    ]
    sample_profiles = [
        FakeDocument({"name": "PROF-01", "project": "PV-01", "capacity_ac_mw": 1.0, "capacity_dc_mwp": 1.2, "status": "In Progress"}),
    ]
    sample_blockers = [
        FakeDocument({"name": "B-01", "project": "PV-01", "status": "In Progress", "severity": "High", "lost_hours": 8.0}),
    ]

    def mock_get_list(doctype, **kwargs):
        if doctype == "Project":
            return sample_projects
        elif doctype == "URANOS Project Profile":
            return sample_profiles
        elif doctype == "URANOS Blocker":
            return sample_blockers
        return []

    monkeypatch.setattr(adapter.frappe, "get_list", mock_get_list)
    adapter.frappe.db.get_value = lambda doctype, name, fields, **kw: {"first_name": "Engineer", "last_name": "Site", "full_name": "Engineer Site"}

    result = adapter.api.get_dashboard_kpis()
    assert result["total_sites"] == 1
    assert result["active_sites"] == 1
    assert result["total_capacity_mw"] == 1.0
    assert result["lost_hours"] == 8.0
    assert result["user"]["first_name"] == "Engineer"
    assert result["user"]["role"] == "Site Controller"
    assert "formatted_date" in result
    assert result["operational_rate_percent"] == 100.0


def test_api_returns_empty_when_no_projects_allowed(adapter, monkeypatch):
    adapter.frappe.session.user = "auditor@example.invalid"
    adapter.frappe.get_roles = lambda user: ["URANOS Read Only Auditor"]
    monkeypatch.setattr(adapter.security, "allowed_projects", lambda user: frozenset())
    adapter.frappe.db.get_value = lambda *args, **kw: {"first_name": "Auditor", "full_name": "Auditor User"}

    result = adapter.api.get_dashboard_kpis()
    assert result["total_sites"] == 0
    assert result["active_sites"] == 0
    assert result["total_capacity_mw"] == 0.0
    assert result["lost_hours"] == 0.0
