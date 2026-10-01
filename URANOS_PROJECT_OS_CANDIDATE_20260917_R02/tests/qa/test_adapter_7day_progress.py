"""Executable boundary tests for 7-Day Verified Progress Reader adapter."""
from datetime import date
from decimal import Decimal
import pytest
from conftest import FakeDocument, Row


def test_progress_api_requires_authenticated_user(adapter):
    adapter.frappe.session.user = "Guest"
    from uranos_project_os.services.progress import get_verified_progress_7days
    with pytest.raises(adapter.frappe.PermissionError):
        get_verified_progress_7days("PV-01")


def test_progress_api_requires_authorized_business_role(adapter):
    adapter.frappe.session.user = "unauthorized@example.invalid"
    adapter.frappe.get_roles = lambda user: ["Customer"]
    from uranos_project_os.services.progress import get_verified_progress_7days
    with pytest.raises(adapter.frappe.PermissionError):
        get_verified_progress_7days("PV-01")


def test_progress_api_rejects_unauthorized_project(adapter, monkeypatch):
    adapter.frappe.session.user = "engineer@example.invalid"
    adapter.frappe.get_roles = lambda user: ["URANOS Site Controller"]
    monkeypatch.setattr(adapter.security, "allowed_projects", lambda user: frozenset({"PV-01"}))

    from uranos_project_os.services.progress import get_verified_progress_7days
    with pytest.raises(adapter.frappe.PermissionError):
        get_verified_progress_7days("PV-99-FORBIDDEN")


def test_progress_api_returns_verified_window(adapter, monkeypatch):
    adapter.frappe.session.user = "engineer@example.invalid"
    adapter.frappe.get_roles = lambda user: ["URANOS Site Controller"]
    monkeypatch.setattr(adapter.security, "allowed_projects", lambda user: frozenset({"PV-01"}))

    # Mock baseline and profile
    pkg1 = FakeDocument({"work_package": "PV-01-WP030", "code": "WP-030", "title": "Battage", "uom": "pieux", "qty_planned": Decimal("1000"), "weight": Decimal("50")})
    pkg2 = FakeDocument({"work_package": "PV-01-WP050", "code": "WP-050", "title": "Modules", "uom": "modules", "qty_planned": Decimal("2000"), "weight": Decimal("50")})

    baseline_doc = FakeDocument({
        "name": "BASE-01",
        "project": "PV-01",
        "version": "B1",
        "status": "Approved",
        "packages": [pkg1, pkg2],
    })

    profile_doc = FakeDocument({"name": "PROF-01", "project": "PV-01", "current_baseline": "BASE-01"})

    entries = [
        {
            "name": "E-01",
            "project": "PV-01",
            "work_package": "PV-01-WP030",
            "baseline_version": "B1",
            "posting_date": "2026-09-12",
            "qty_reported": "100",
            "qty_verified": "100",
            "reported_by": "engineer@uranos.local",
            "verifier": "controller@uranos.local",
            "status": "Verified",
            "evidence": ["/private/files/test.jpg"],
        }
    ]

    monkeypatch.setattr(adapter.common, "project_rows", lambda dt, proj, fields, **kw: [profile_doc] if dt == "URANOS Project Profile" else [])
    monkeypatch.setattr(adapter.common, "scoped_doc", lambda dt, name, **kw: baseline_doc if dt == "URANOS Baseline" else None)
    monkeypatch.setattr(adapter.api, "_all_rows", lambda dt, proj, fields: entries if dt == "URANOS Field Progress Entry" else [])

    from uranos_project_os.services.progress import get_verified_progress_7days
    result = get_verified_progress_7days("PV-01", start_date="2026-09-10", end_date="2026-09-16")

    assert result["project"] == "PV-01"
    assert result["baseline_version"] == "B1"
    assert result["period"]["calendar_days"] == 7
    wp030 = next(r for r in result["work_packages"] if r["code"] == "WP-030")
    assert wp030["qty_verified"] == 100.0  # JSON converted float
    assert wp030["is_measured"] is True
    wp050 = next(r for r in result["work_packages"] if r["code"] == "WP-050")
    assert wp050["qty_verified"] is None  # Unknown
    assert wp050["is_measured"] is False
