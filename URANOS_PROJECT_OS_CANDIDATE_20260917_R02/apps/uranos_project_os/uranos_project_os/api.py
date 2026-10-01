"""Public whitelisted Desk APIs for URANOS Project OS."""
from __future__ import annotations

import frappe
from uranos_project_os.services.api import (
    FIELD_ROLES,
    get_dashboard_kpis,
    get_dashboard_telemetry,
    generate_executive_pdf,
    generate_daily_report,
    get_accessible_projects,
    get_engineer_users,
    get_site_team_users,
    get_users_by_role,
)

__all__ = [
    "FIELD_ROLES",
    "get_dashboard_kpis",
    "get_dashboard_telemetry",
    "generate_executive_pdf",
    "generate_daily_report",
    "get_accessible_projects",
    "get_engineer_users",
    "get_site_team_users",
    "get_users_by_role",
]

