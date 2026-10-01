"""URANOS Project OS — 3D Holographic Vision Controller (www/uranos_vision.py).

Provides live operational statistics, project telemetry, and blocker risk metrics
to the WebGL 3D executive presentation landing page.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List

import frappe

no_cache = 1


def get_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch live operational database metrics for the 3D Vision portal."""
    context.no_cache = 1
    context.title = "URANOS Vision · Jumeau Numérique 3D & Pilotage de Crise"
    context.meta_description = (
        "Plateforme 3D temps-réel de supervision des centrales solaires photovoltaïques, "
        "résolution d'obstacles opérationnels et gouvernance stricte sous architecture hexagonale."
    )

    try:
        csrf_token = frappe.sessions.get_csrf_token()
    except Exception:
        csrf_token = ""
    context.csrf_token = csrf_token

    # 1. High-Level KPI Aggregations (Strict DB Queries, zero-preserving)
    try:
        total_projects = frappe.db.count("Project")
        total_blockers = frappe.db.count("URANOS Blocker")
        active_blockers = frappe.db.count("URANOS Blocker", {"status": ["!=", "Closed"]})
        resolved_blockers = frappe.db.count("URANOS Blocker", {"status": "Closed"})
        critical_active = frappe.db.count(
            "URANOS Blocker", {"severity": "Critical", "status": ["!=", "Closed"]}
        )
        high_active = frappe.db.count(
            "URANOS Blocker", {"severity": "High", "status": ["!=", "Closed"]}
        )

        # Calculate total lost hours from database
        lost_hours_query = frappe.db.sql(
            "SELECT COALESCE(SUM(lost_hours), 0) FROM `tabURANOS Blocker`"
        )
        total_lost_hours = float(lost_hours_query[0][0]) if (lost_hours_query and lost_hours_query[0][0] is not None) else 0.0

        # Calculate total capacity from URANOS Project Profile
        cap_query = frappe.db.sql(
            "SELECT COALESCE(SUM(capacity_ac_mw), 0) FROM `tabURANOS Project Profile`"
        )
        total_capacity_mw = float(cap_query[0][0]) if (cap_query and cap_query[0][0] is not None) else (total_projects * 1.0)
    except Exception as e:
        frappe.log_error(title="URANOS Vision Telemetry Error", message=str(e))
        total_projects = 0
        total_blockers = 0
        active_blockers = 0
        resolved_blockers = 0
        critical_active = 0
        high_active = 0
        total_lost_hours = 0.0
        total_capacity_mw = 0.0

    context.total_projects = total_projects
    context.total_blockers = total_blockers
    context.active_blockers = active_blockers
    context.resolved_blockers = resolved_blockers
    context.critical_active = critical_active
    context.high_active = high_active
    context.total_lost_hours = round(total_lost_hours, 1)
    context.total_capacity_mw = round(total_capacity_mw, 1)

    # 2. Status Breakdown
    statuses = ["Open", "In Progress", "Pending Verification", "Closed"]
    status_counts: Dict[str, int] = {}
    for st in statuses:
        try:
            status_counts[st] = frappe.db.count("URANOS Blocker", {"status": st})
        except Exception:
            status_counts[st] = 0
    context.status_counts = status_counts

    # 3. Severity Breakdown
    severities = ["Critical", "High", "Medium", "Low"]
    severity_counts: Dict[str, int] = {}
    for sev in severities:
        try:
            severity_counts[sev] = frappe.db.count("URANOS Blocker", {"severity": sev})
        except Exception:
            severity_counts[sev] = 0
    context.severity_counts = severity_counts

    # 4. Category Breakdown
    categories = [
        "Material", "Quality", "Equipment", "Document", "Safety",
        "Weather", "Crew", "Access", "Logistics", "Administration"
    ]
    category_counts: Dict[str, int] = {}
    for cat in categories:
        try:
            category_counts[cat] = frappe.db.count("URANOS Blocker", {"category": cat})
        except Exception:
            category_counts[cat] = 0
    context.category_counts = category_counts

    # 5. Recent Active Issues for HUD Table
    try:
        recent_blockers = frappe.get_all(
            "URANOS Blocker",
            fields=["name", "project", "title", "severity", "status", "category", "lost_hours", "responsible"],
            order_by="modified desc",
            limit=8,
        )
    except Exception as e:
        frappe.log_error(title="URANOS Vision Recent Blockers Query Failed", message=str(e))
        recent_blockers = []
    context.recent_blockers = recent_blockers

    # 6. Projects Telemetry for 3D Node Placement
    try:
        project_docs = frappe.get_all("Project", fields=["name", "project_name"], order_by="name asc", limit=200)
        # Fetch capacity per project if available
        profiles = {
            p.project: p.capacity_ac_mw
            for p in frappe.get_all("URANOS Project Profile", fields=["project", "capacity_ac_mw"], limit=200)
        }
        telemetry = []
        for p in project_docs:
            p_name = p.name
            blk_count = frappe.db.count("URANOS Blocker", {"project": p_name, "status": ["!=", "Closed"]})
            crit_count = frappe.db.count("URANOS Blocker", {"project": p_name, "severity": "Critical", "status": ["!=", "Closed"]})
            cap = profiles.get(p_name, 1.0)
            telemetry.append({
                "id": p_name,
                "name": p.project_name or p_name,
                "capacity_mw": float(cap) if cap else 1.0,
                "active_blockers": blk_count,
                "critical_blockers": crit_count,
                "status": "Alert" if crit_count > 0 else ("Warning" if blk_count > 0 else "Nominal"),
            })
    except Exception as e:
        frappe.log_error(title="URANOS Vision Telemetry Failed", message=str(e))
        telemetry = []
    context.projects_telemetry = telemetry

    # Pass user session info
    context.current_user = frappe.session.user if hasattr(frappe, "session") else "Guest"
    context.is_authenticated = context.current_user != "Guest"

    return context
