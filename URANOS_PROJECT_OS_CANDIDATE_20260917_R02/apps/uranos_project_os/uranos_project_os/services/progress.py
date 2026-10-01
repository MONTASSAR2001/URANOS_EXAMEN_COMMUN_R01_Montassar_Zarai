"""Service adapter layer for 7-Day Verified Progress Reader.

Strict Hexagonal Architecture:
Adapts Frappe database records (Project, Baseline, Field Progress Entry)
to the pure domain reader in domain.controls.read_verified_progress_window.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

import frappe
from uranos_project_os import security
from uranos_project_os.domain.controls import read_verified_progress_window
from uranos_project_os.services.api import _all_rows, _json_numbers
from uranos_project_os.services.common import actor, project_rows, scoped_doc

FIELD_ROLES = (
    "Executive",
    "Finance Controller",
    "Engineering Director",
    "Civil Director",
    "Electrical Execution Manager",
    "Project Manager",
    "Site Controller",
    "Storekeeper",
    "Procurement Logistics",
    "QA QC",
    "HSE",
    "Team Lead",
    "Read Only Auditor",
    "management",
    "Direction",
    "Manager",
    "engineer",
    "site_team",
)


@frappe.whitelist()
def get_verified_progress_7days(
    project: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Whitelisted endpoint returning 7-day verified progress by work package and unit.

    - Authenticates user and checks role grants.
    - Strictly enforces project isolation (security.allowed_projects).
    - If project is not provided, defaults to the user's primary assigned project.
    - Dates default to the preceding 7 calendar days if omitted.
    """
    user = actor()
    security.require_roles(*FIELD_ROLES)

    # Determine allowed projects
    if user == "Administrator":
        allowed = set(frappe.get_list("Project", pluck="name"))
    else:
        allowed = set(security.allowed_projects(user) or [])

    if not allowed:
        return {
            "project": project or "None",
            "status": "Unknown",
            "missing_data": ["authorized_project"],
            "work_packages": [],
            "units_summary": {},
        }

    if not project:
        # Default to first allowed project
        project = sorted(allowed)[0]
    elif project not in allowed:
        frappe.throw(
            f"Unauthorized access: user {user} lacks grant for project {project}",
            frappe.PermissionError,
        )

    # Resolve 7-day period window (defaults to latest 7 calendar days ending today)
    if not end_date:
        today = date.today()
        end_date_obj = today
        start_date_obj = today - timedelta(days=6)
    else:
        end_date_obj = date.fromisoformat(str(end_date)[:10])
        if not start_date:
            start_date_obj = end_date_obj - timedelta(days=6)
        else:
            start_date_obj = date.fromisoformat(str(start_date)[:10])

    # Fetch approved baseline
    profiles = project_rows(
        "URANOS Project Profile", project, ["current_baseline"], limit=2
    )
    if not profiles or not profiles[0].current_baseline:
        return {
            "project": project,
            "status": "Unknown",
            "missing_data": ["approved_baseline"],
            "period": {
                "start_date": start_date_obj.isoformat(),
                "end_date": end_date_obj.isoformat(),
                "calendar_days": 7,
            },
            "work_packages": [],
            "units_summary": {},
        }

    baseline_doc = scoped_doc("URANOS Baseline", profiles[0].current_baseline)
    if not baseline_doc or baseline_doc.status != "Approved":
        return {
            "project": project,
            "status": "Unknown",
            "missing_data": ["approved_baseline"],
            "period": {
                "start_date": start_date_obj.isoformat(),
                "end_date": end_date_obj.isoformat(),
                "calendar_days": 7,
            },
            "work_packages": [],
            "units_summary": {},
        }

    baseline_dict = {
        "project": project,
        "version": baseline_doc.version,
        "packages": [
            {
                "name": row.work_package,
                "project": getattr(row, "project", None) or project,
                "baseline_version": getattr(row, "baseline_version", None) or baseline_doc.version,
                "code": getattr(row, "code", None) or row.work_package,
                "title": getattr(row, "title", None) or getattr(row, "code", None) or row.work_package,
                "uom": getattr(row, "uom", None) or "units",
                "qty_planned": row.qty_planned,
                "weight": getattr(row, "weight", None) if getattr(row, "weight", None) is not None else 0,
            }
            for row in baseline_doc.packages
        ],
    }

    # Fetch progress entries
    entries = _all_rows(
        "URANOS Field Progress Entry",
        project,
        [
            "name",
            "project",
            "work_package",
            "baseline_version",
            "activity",
            "zone",
            "crew",
            "posting_date",
            "qty_reported",
            "qty_verified",
            "reported_by",
            "verifier",
            "status",
            "correction_of",
            "revision_reason",
        ],
    )

    result = read_verified_progress_window(
        project,
        baseline_dict,
        entries,
        start_date_obj,
        end_date_obj,
        permitted_projects=allowed,
    )

    headers = getattr(getattr(frappe, "local", None), "response_headers", None)
    if headers is not None:
        headers["Cache-Control"] = "no-store, private"

    return _json_numbers(result)
