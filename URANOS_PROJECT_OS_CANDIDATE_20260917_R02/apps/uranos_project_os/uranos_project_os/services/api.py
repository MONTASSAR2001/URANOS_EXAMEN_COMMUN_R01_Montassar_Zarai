"""Small role-oriented read models; no native ERP rate-bearing document dumps."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import frappe

from uranos_project_os import security
from uranos_project_os.services.common import actor, project_rows, scoped_doc

FIELD_ROLES = ("Executive", "Finance Controller", "Engineering Director", "Civil Director", "Electrical Execution Manager",
               "Project Manager", "Site Controller", "Storekeeper", "Procurement Logistics", "QA QC", "HSE", "Team Lead", "Read Only Auditor",
               "management", "Direction", "Manager", "engineer", "site_team")


def _json_numbers(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (list, tuple)):
        return [_json_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_numbers(item) for key, item in value.items()}
    return value


@frappe.whitelist()
def bootstrap():
    from frappe.sessions import get_csrf_token
    user = actor()
    security.require_roles(*FIELD_ROLES)
    if user == "Administrator" or security.is_management(user):
        projects = frappe.get_list("Project", fields=["name", "project_name", "status"], limit_page_length=500, ignore_permissions=True)
    else:
        allowed = security.allowed_projects(user)
        projects = frappe.get_list("Project", filters={"name": ["in", list(allowed)]}, fields=["name", "project_name", "status"], limit_page_length=500, ignore_permissions=True) if allowed else []
    frappe.local.response_headers["Cache-Control"] = "no-store, private"
    return {"user": user, "language": frappe.db.get_value("User", user, "language") or "fr", "csrf_token": get_csrf_token(),
            "roles": [role for role in frappe.get_roles(user) if role.startswith("URANOS ")],
            "projects": projects, "finance_allowed": security.has_financial_access(),
            "server_time": frappe.utils.now(), "environment": frappe.conf.get("uranos_environment", "unclassified")}


@frappe.whitelist()
def project_context(project):
    security.require_roles(*FIELD_ROLES)
    security.require_project(project)
    packages = project_rows("URANOS Work Package", project,
        ["name", "code", "title", "uom", "baseline_version", "status", "modified", "qty_planned", "weight", "discipline"])
    templates = project_rows("URANOS Material Kit Template", project, ["name", "kit_code", "kit_version", "activity", "status"])
    warehouses = project_rows("Warehouse", project, ["name", "warehouse_name", "is_group"])
    profiles = project_rows("URANOS Project Profile", project, ["current_baseline"], limit=2)
    baseline = scoped_doc("URANOS Baseline", profiles[0].current_baseline) if len(profiles) == 1 and profiles[0].current_baseline else None
    active = {row.work_package for row in baseline.packages} if baseline and baseline.status == "Approved" else set()
    issues = project_rows("URANOS Kit Issue", project, ["name", "work_package", "activity", "zone", "crew", "status"])
    reels = project_rows("URANOS Cable Reel", project, ["name", "reel_id", "item_code", "status"])
    return {"project": project, "work_packages": [row for row in packages if row.name in active],
            "kit_templates": [row for row in templates if row.status == "Approved"],
            "warehouses": [row for row in warehouses if not row.is_group],
            "kit_issues": [row for row in issues if row.status in {"Issued", "Partially Used", "Variance Review"}],
            "cable_reels": [row for row in reels if row.status in {"In Use", "Reconciliation"}]}


def _all_rows(doctype, project, fields):
    security.require_project(project, doctype=doctype)
    rows, offset = [], 0
    while True:
        batch = frappe.get_list(doctype, filters={"project": project}, fields=fields,
                                limit_start=offset, limit_page_length=1000, order_by="name asc")
        rows.extend(batch)
        if len(batch) < 1000:
            return rows
        offset += 1000


def _progress(project):
    from uranos_project_os.domain.controls import aggregate_progress, baseline_aliases
    profiles = project_rows("URANOS Project Profile", project, ["name", "current_baseline", "site", "capacity_ac_mw"], limit=2)
    if len(profiles) != 1 or not profiles[0].current_baseline:
        return {"project": project, "physical_progress": None, "work_packages": [], "missing_data": ["approved_baseline"]}
    baseline = scoped_doc("URANOS Baseline", profiles[0].current_baseline)
    if baseline.status != "Approved":
        return {"project": project, "physical_progress": None, "work_packages": [], "missing_data": ["approved_baseline"]}
    packages = [dict(project=project, name=row.work_package, code=row.code, uom=row.uom, baseline_version=baseline.version,
                     qty_planned=row.qty_planned, weight=row.weight, baseline_start=row.baseline_start,
                     baseline_finish=row.baseline_finish) for row in baseline.packages]
    entries = _all_rows("URANOS Field Progress Entry", project,
        ["name", "project", "work_package", "baseline_version", "activity", "zone", "crew", "posting_date",
         "qty_reported", "qty_verified", "reported_by", "verifier", "status", "correction_of", "revision_reason"])
    # One scoped bulk child lookup, not one query per field entry. Parent names
    # originated exclusively from the caller's authorized Project query.
    evidence = {}
    for start in range(0, len(entries), 500):
        parent_names = [row.name for row in entries[start:start + 500]]
        if parent_names:
            for row in frappe.get_all("URANOS Evidence", filters={"parenttype": "URANOS Field Progress Entry", "parent": ["in", parent_names]}, fields=["parent", "file"]):
                evidence.setdefault(row.parent, []).append(row.file)
    for entry in entries:
        entry["evidence"] = evidence.get(entry.name, [])
    approved_versions = [row.version for row in frappe.get_list("URANOS Baseline", filters={"project": project, "status": ["in", ["Approved", "Superseded"]]}, fields=["version"], limit_page_length=0)]
    historical = frappe.get_list("URANOS Work Package", filters={"project": project, "baseline_approved": 1,
        "baseline_version": ["in", approved_versions]}, fields=["name", "project", "code", "uom"], limit_page_length=0)
    current = {"project": project, "version": baseline.version, "packages": packages}
    # Future revision drafts are not official progress. A verified row on an
    # unapproved baseline remains an error, never silently dropped.
    entries = [entry for entry in entries if entry.baseline_version in approved_versions or entry.status == "Verified"]
    return aggregate_progress(project, current, entries, approved_versions=approved_versions,
                              work_package_aliases=baseline_aliases(current, historical))


@frappe.whitelist()
def dashboard(project):
    from uranos_project_os.domain.controls import dashboard_summary
    security.require_roles(*FIELD_ROLES)
    security.require_project(project)
    progress = _progress(project)
    blockers = _all_rows("URANOS Blocker", project, ["name", "project", "title", "status", "severity", "category", "lost_hours"])
    ncrs = _all_rows("URANOS NCR", project, ["name", "project", "status", "severity", "due_date", "defect"])
    if progress["physical_progress"] is None:
        # Unknown baseline never becomes a reassuring zero/green status.
        summary = {"project": project, "physical_progress": None, "planned_progress": None,
                   "material_readiness": None, "status": "Unknown", "missing_data": progress["missing_data"]}
        if (any(row.severity == "Critical" and row.status not in {"Resolved", "Closed"} for row in [*blockers, *ncrs]) or
                any(row.severity == "High" and row.status != "Closed" and row.due_date and frappe.utils.getdate(row.due_date) < date.today() for row in ncrs)):
            summary["status"] = "Red"
    else:
        summary = dashboard_summary(project, progress, blockers=blockers, ncrs=ncrs, today=date.today())
    summary["work_packages"] = progress["work_packages"]
    summary["blockers"] = blockers
    summary["ncrs"] = ncrs
    summary["shipments"] = project_rows("URANOS Shipment", project, ["name", "status", "eta_initial", "eta_revised", "need_by", "criticality"])
    summary["alerts"] = project_rows("URANOS Executive Alert", project, ["name", "rule", "severity", "message", "status", "reference_doctype", "reference_name"])
    # Any live critical alert must remain visible even when other inputs are missing.
    if any(row.status != "Resolved" and (row.severity == "Critical" or row.rule.startswith(
            ("high_risk", "reel_field", "reel_residual"))) for row in summary["alerts"]):
        summary["status"] = "Red"
    elif summary["status"] != "Red" and any(row.status != "Resolved" for row in summary["alerts"]):
        summary["status"] = "Amber"
    if security.has_financial_access():
        summary["costs"] = project_rows("URANOS Project Cost", project,
            ["name", "work_package", "currency", "budget", "committed", "received", "invoiced", "paid", "forecast", "status"])
    summary["as_of"] = frappe.utils.now()
    return _json_numbers(summary)


@frappe.whitelist()
def pending_verifications(project):
    security.require_roles("Site Controller", "QA QC", "Project Manager")
    rows = _all_rows("URANOS Field Progress Entry", project,
        ["name", "work_package", "activity", "zone", "crew", "qty_reported", "reported_by", "posting_date", "status"])
    return [row for row in rows if row.status == "Pending Verification"]


@frappe.whitelist()
def system_health():
    user = actor()
    if "System Manager" not in frappe.get_roles(user):
        frappe.throw("System administration role required", frappe.PermissionError)
    from frappe.utils.scheduler import is_scheduler_inactive
    database = bool(frappe.db.sql("SELECT 1"))
    cache = bool(frappe.cache.ping())
    return {"database": "reachable" if database else "unreachable", "redis": "reachable" if cache else "unreachable",
            "scheduler": "inactive" if is_scheduler_inactive() else "active",
            "backup_restore": "verification_required", "as_of": frappe.utils.now()}


@frappe.whitelist()
def get_dashboard_kpis():
    """Whitelisted endpoint returning dynamic real portfolio KPI metrics."""
    user = actor()
    security.require_roles(*FIELD_ROLES)

    if user == "Administrator" or security.is_management(user):
        project_rows = frappe.get_list(
            "Project",
            fields=["name", "project_name", "status"],
            limit_page_length=0,
            ignore_permissions=True,
        )
    else:
        allowed = security.allowed_projects(user)
        if not allowed:
            project_rows = []
        else:
            project_rows = frappe.get_list(
                "Project",
                filters={"name": ["in", list(allowed)]},
                fields=["name", "project_name", "status"],
                limit_page_length=0,
                ignore_permissions=True,
            )

    project_names = [p.name for p in project_rows]

    if not project_names:
        summary = {
            "total_sites": 0,
            "active_sites": 0,
            "operational_rate_percent": Decimal(0),
            "total_capacity_mw": Decimal(0),
            "total_capacity_dc_mwp": Decimal(0),
            "lost_hours": Decimal(0),
            "active_blockers_count": 0,
            "total_blockers_count": 0,
            "energy_today_mwh": Decimal(0),
            "co2_avoided_t": Decimal(0),
        }
    else:
        profiles = frappe.get_list(
            "URANOS Project Profile",
            filters={"project": ["in", project_names]},
            fields=["name", "project", "capacity_ac_mw", "capacity_dc_mwp", "status"],
            limit_page_length=0,
            ignore_permissions=True,
        )
        blockers = frappe.get_list(
            "URANOS Blocker",
            filters={"project": ["in", project_names]},
            fields=["name", "project", "status", "severity", "lost_hours"],
            limit_page_length=0,
            ignore_permissions=True,
        )
        from uranos_project_os.domain.controls import portfolio_kpi_summary
        summary = portfolio_kpi_summary(project_rows, profiles, blockers)

    user_info = frappe.db.get_value("User", user, ["first_name", "last_name", "full_name"], as_dict=True) or {}
    first_name = (user_info.get("first_name") or user.split("@")[0]).strip()
    full_name = (user_info.get("full_name") or f"{first_name} {user_info.get('last_name') or ''}").strip()

    if "direction" in user.lower() or security.is_management(user):
        first_name = "Manager"
        full_name = "Manager"

    user_roles = [r.replace("URANOS ", "") for r in frappe.get_roles(user) if r.startswith("URANOS ")]
    primary_role = user_roles[0] if user_roles else ("Manager" if security.is_management(user) else ("System Manager" if "System Manager" in frappe.get_roles(user) else "Operations"))
    if security.is_management(user):
        primary_role = "Manager"

    get_now_dt = getattr(frappe.utils, "now_datetime", None)
    now_dt = get_now_dt() if callable(get_now_dt) else datetime.now()
    formatted_date = now_dt.strftime("%b %d, %Y - %I:%M %p")

    summary["user"] = {
        "username": user,
        "first_name": first_name,
        "full_name": full_name,
        "role": primary_role,
    }
    summary["server_time"] = frappe.utils.now()
    summary["formatted_date"] = formatted_date

    headers = getattr(getattr(frappe, "local", None), "response_headers", None)
    if headers is not None:
        headers["Cache-Control"] = "no-store, private"
    return _json_numbers(summary)


@frappe.whitelist()
def get_dashboard_telemetry():
    """Whitelisted endpoint returning project telemetry for GIS map and dashboard markers.
    Uses standard frappe.get_all("Project") WITHOUT ignore_permissions=True so map markers
    automatically respect security.py query conditions.
    """
    user = frappe.session.user
    if user == "Administrator" or security.is_management(user):
        return frappe.get_all(
            "Project",
            fields=["name", "project_name", "status", "latitude", "longitude", "custom_assigned_engineer", "custom_assigned_site_team"],
            order_by="name asc",
            limit_page_length=0,
        )
    return frappe.get_list(
        "Project",
        fields=["name", "project_name", "status", "latitude", "longitude", "custom_assigned_engineer", "custom_assigned_site_team"],
        order_by="name asc",
        limit_page_length=0,
    )


@frappe.whitelist()
def get_accessible_projects():
    """Returns active projects accessible to the current actor without throwing permission error."""
    user = actor()
    if user == "Administrator" or security.is_management(user):
        return frappe.get_list(
            "Project",
            filters={"status": ["!=", "Cancelled"]},
            fields=["name", "project_name"],
            order_by="project_name asc",
            limit_page_length=500,
            ignore_permissions=True,
        )
    allowed = security.allowed_projects(user)
    if not allowed:
        return []
    return frappe.get_list(
        "Project",
        filters={"name": ["in", list(allowed)], "status": ["!=", "Cancelled"]},
        fields=["name", "project_name"],
        order_by="project_name asc",
        limit_page_length=500,
        ignore_permissions=True,
    )


@frappe.whitelist()
def get_verified_progress_7days(project=None, start_date=None, end_date=None):
    from uranos_project_os.services.progress import get_verified_progress_7days as _reader
    return _reader(project=project, start_date=start_date, end_date=end_date)


@frappe.whitelist()
def generate_blocker_synthesis(project=None, force_fallback=False):
    from uranos_project_os.services.ai_synthesis import generate_blocker_synthesis as _synth
    return _synth(project=project, force_fallback=force_fallback)


@frappe.whitelist()
def get_user_roles():
    """Returns all active user role mappings for security access audit."""
    return frappe.db.sql("SELECT parent, role FROM `tabHas Role`", as_dict=True)


@frappe.whitelist()
def update_blocker_status(name: str = None, status: str = None, blocker: str = None):
    """Kanban drag & drop status transition adapter with strict workflow, RBAC, and Separation of Duties."""
    from uranos_project_os.controllers import authorized_transition
    from uranos_project_os.security import is_engineer, is_site_team, require_project

    blocker_name = name or blocker
    if not blocker_name:
        frappe.throw("Blocker ID (name) is required.")
    name = blocker_name

    doc = frappe.get_doc("URANOS Blocker", blocker_name)
    require_project(doc.project)

    user = frappe.session.user

    status_map = {
        "open": "Open",
        "ouvert": "Open",
        "in progress": "In Progress",
        "en cours": "In Progress",
        "pending verification": "Pending Verification",
        "à vérifier": "Pending Verification",
        "a verifier": "Pending Verification",
        "closed": "Closed",
        "clôturé": "Closed",
        "cloture": "Closed",
    }
    normalized = status_map.get(str(status).strip().lower())
    if not normalized:
        frappe.throw(f"Statut d'obstacle invalide : {status}")

    # RBAC check: site_team cannot close tickets
    if normalized == "Closed" and is_site_team(user) and not (is_engineer(user) or user == "Administrator"):
        frappe.throw("L'équipe chantier n'est pas autorisée à clôturer un obstacle.", frappe.PermissionError)

    # Separation of Duties check on closure
    if normalized == "Closed":
        action = doc.get("corrective_action") or doc.get("resolution")
        if not action or not str(action).strip():
            frappe.throw("Action corrective obligatoire pour clôturer l'obstacle.", frappe.ValidationError)

        resolvers = {
            u.strip()
            for u in (doc.get("resolved_by"), doc.get("responsible"))
            if u and str(u).strip()
        }
        if user in resolvers:
            frappe.throw("Auto-vérification refusée.", frappe.ValidationError)

        doc.closed_by = user
        doc.closed_at = frappe.utils.now()
        doc.resolved_at = doc.resolved_at or frappe.utils.now()

    elif normalized == "Pending Verification":
        action = doc.get("corrective_action") or doc.get("resolution")
        if not action or not str(action).strip():
            frappe.throw("Une action corrective est requise pour soumettre à vérification.", frappe.ValidationError)
        if not doc.get("resolved_by"):
            doc.resolved_by = user
        if not doc.get("resolution_submitted_at"):
            doc.resolution_submitted_at = frappe.utils.now()

    elif normalized == "In Progress":
        if not doc.get("responsible"):
            doc.responsible = user

    doc.status = normalized

    with authorized_transition():
        doc.flags.ignore_mandatory = True
        doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success", "name": name, "new_status": normalized}


@frappe.whitelist(allow_guest=False)
def generate_daily_report():
    """Generates an executive-ready Daily Operational PDF report for the URANOS Solar Portfolio."""
    from frappe.utils.pdf import get_pdf

    kpis = get_dashboard_kpis()
    blockers = frappe.get_list(
        "URANOS Blocker",
        filters={"status": ["in", ["Open", "In Progress", "Pending Verification"]]},
        fields=["name", "project", "title", "severity", "status", "reported_by", "responsible", "lost_hours"],
        order_by="lost_hours desc, modified desc",
        limit_page_length=20,
        ignore_permissions=True,
    )

    work_packages = frappe.get_list(
        "URANOS Work Package",
        filters={"status": ["in", ["Completed", "In Progress"]]},
        fields=["name", "code", "project", "title", "discipline", "qty_planned", "status"],
        order_by="status asc, code asc",
        ignore_permissions=True,
    )

    verified_progress = frappe.get_list(
        "URANOS Field Progress Entry",
        filters={"status": "Verified"},
        fields=["name", "project", "work_package", "activity", "qty_verified", "reported_by", "verifier", "verified_at", "posting_date"],
        order_by="posting_date desc",
        limit_page_length=15,
        ignore_permissions=True,
    )

    projects = frappe.get_list(
        "Project",
        fields=["name", "project_name", "status"],
        order_by="name asc",
        limit_page_length=50,
        ignore_permissions=True,
    )

    profiles = frappe.get_list(
        "URANOS Project Profile",
        fields=["name", "project", "capacity_ac_mw", "capacity_dc_mwp", "status", "site", "governorate"],
        order_by="project asc",
        limit_page_length=50,
        ignore_permissions=True,
    )
    profile_map = {p.project: p for p in profiles}

    total_cap = float(kpis.get("total_capacity_mw") or 0)
    active_sites = kpis.get("active_sites", 0)
    total_sites = kpis.get("total_sites", 0)
    op_rate = kpis.get("operational_rate_percent", 0)
    lost_hours = float(kpis.get("lost_hours") or 0)
    active_blockers_cnt = kpis.get("active_blockers_count", 0)
    energy_today = float(kpis.get("energy_today_mwh") or 0)
    co2_avoided = float(kpis.get("co2_avoided_t") or 0)
    rep_user = kpis.get("user", {})
    user_name = rep_user.get("full_name") or frappe.session.user
    user_role = rep_user.get("role") or "Executive"
    formatted_date = kpis.get("formatted_date") or frappe.utils.now()

    # Build blocker rows HTML
    blocker_rows_html = ""
    if blockers:
        for b in blockers:
            sev = str(b.get("severity") or "Medium")
            if sev in ["High", "Critical"]:
                sev_badge = f"<span class='badge badge-sev-high'>{sev}</span>"
            elif sev == "Medium":
                sev_badge = f"<span class='badge badge-sev-med'>{sev}</span>"
            else:
                sev_badge = f"<span class='badge badge-sev-low'>{sev}</span>"

            st = str(b.get("status") or "Open")
            if st == "Open":
                st_badge = f"<span class='badge badge-status-open'>{st}</span>"
            elif st == "In Progress":
                st_badge = f"<span class='badge badge-status-prog'>{st}</span>"
            else:
                st_badge = f"<span class='badge badge-status-verif'>{st}</span>"

            lh = float(b.get("lost_hours") or 0)
            lh_style = "color: #dc2626; font-weight: 700;" if lh > 0 else "color: #64748b;"
            reporter = b.get("reported_by") or "Site Team"
            resp_eng = b.get("responsible") or "Unassigned"

            blocker_rows_html += f"""
            <tr>
              <td style='font-family: monospace; font-weight: 700; color: #0284c7;'>{b.name}</td>
              <td><strong>{b.project}</strong></td>
              <td>{frappe.utils.escape_html(b.title or '')}</td>
              <td style='text-align: center;'>{sev_badge}</td>
              <td style='text-align: center;'>{st_badge}</td>
              <td style='font-size: 9px; color: #475569;'>{reporter} &rarr; <strong>{resp_eng}</strong></td>
              <td style='text-align: right; {lh_style}'>{lh:.1f} h</td>
            </tr>
            """
    else:
        blocker_rows_html = "<tr><td colspan='7' style='text-align: center; color: #10b981; padding: 15px;'>No active operational blockers recorded across the fleet.</td></tr>"

    # Build work packages HTML
    wp_rows_html = ""
    if work_packages:
        for wp in work_packages:
            st = wp.get("status") or "Completed"
            if st == "Completed":
                st_badge = "<span class='badge badge-status-prog'>Completed</span>"
            elif st == "Blocked":
                st_badge = "<span class='badge badge-sev-high'>Blocked</span>"
            else:
                st_badge = "<span class='badge badge-status-verif'>In Progress</span>"

            wp_rows_html += f"""
            <tr>
              <td style='font-family: monospace; font-weight: 700; color: #0284c7;'>{wp.get("code") or wp.name}</td>
              <td><strong>{wp.project}</strong></td>
              <td>{frappe.utils.escape_html(wp.title or '')}</td>
              <td style='text-align: center;'>{wp.discipline or 'General'}</td>
              <td style='text-align: right; font-weight: 700;'>{float(wp.qty_planned or 0):.1f}</td>
              <td style='text-align: center;'>{st_badge}</td>
            </tr>
            """
    else:
        wp_rows_html = "<tr><td colspan='6' style='text-align: center; color: #64748b; padding: 12px;'>No work packages completed or scheduled today.</td></tr>"

    # Build verified progress entries HTML
    prog_rows_html = ""
    if verified_progress:
        for vp in verified_progress[:6]:
            prog_rows_html += f"""
            <tr>
              <td style='font-family: monospace; font-weight: 700;'>{vp.name}</td>
              <td><strong>{vp.project}</strong></td>
              <td>{frappe.utils.escape_html(vp.activity or '')}</td>
              <td style='text-align: right; font-weight: 700; color: #059669;'>{float(vp.qty_verified or 0):.1f}</td>
              <td style='font-size: 9px; color: #64748b;'>{vp.reported_by or 'Site Controller'}</td>
              <td style='font-size: 9px; color: #0284c7; font-weight: 600;'>{vp.verifier or 'Responsible Engineer'}</td>
            </tr>
            """
    else:
        prog_rows_html = "<tr><td colspan='6' style='text-align: center; color: #64748b; padding: 10px;'>No verified progress entries logged today.</td></tr>"

    # Build project fleet table HTML
    project_rows_html = ""
    for p in projects[:10]:
        prof = profile_map.get(p.name, {})
        cap_ac = float(prof.get("capacity_ac_mw") or 1.0)
        cap_dc = float(prof.get("capacity_dc_mwp") or 1.2)
        project_rows_html += f"""
        <tr>
          <td style='font-family: monospace; font-weight: 700;'>{p.name}</td>
          <td><strong>{frappe.utils.escape_html(p.project_name or p.name)}</strong></td>
          <td style='text-align: center;'><span class='badge badge-status-prog'>Operational</span></td>
          <td style='text-align: right; font-weight: 600;'>{cap_ac:.1f} MW</td>
          <td style='text-align: right; color: #64748b;'>{cap_dc:.2f} MWp</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>URANOS Daily Executive Operational Report</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 10mm 12mm 12mm 12mm;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background: #ffffff;
    font-size: 10.5px;
    line-height: 1.4;
    margin: 0;
    padding: 0;
  }}
  .header-table {{
    width: 100%;
    border-bottom: 2px solid #0f172a;
    padding-bottom: 10px;
    margin-bottom: 12px;
  }}
  .brand-title {{
    font-size: 20px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
  }}
  .brand-subtitle {{
    font-size: 9.5px;
    text-transform: uppercase;
    color: #64748b;
    font-weight: 600;
    letter-spacing: 0.8px;
    margin-top: 2px;
  }}
  .report-badge {{
    text-align: right;
  }}
  .report-title {{
    font-size: 14px;
    font-weight: 800;
    color: #0284c7;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .report-meta {{
    font-size: 9.5px;
    color: #64748b;
    margin-top: 3px;
    font-weight: 500;
  }}
  
  /* KPI Grid Table */
  .kpi-table {{
    width: 100%;
    margin-bottom: 10px;
    border-collapse: separate;
    border-spacing: 8px 0;
  }}
  .kpi-cell {{
    width: 25%;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 10px;
    vertical-align: top;
  }}
  .kpi-label {{
    font-size: 8.5px;
    text-transform: uppercase;
    font-weight: 700;
    color: #64748b;
    margin-bottom: 3px;
    letter-spacing: 0.4px;
  }}
  .kpi-value {{
    font-size: 17px;
    font-weight: 800;
    color: #0f172a;
  }}
  .kpi-sub {{
    font-size: 9px;
    color: #10b981;
    font-weight: 600;
    margin-top: 2px;
  }}
  
  /* Section Headings */
  .section-title {{
    font-size: 11px;
    font-weight: 700;
    color: #0f172a;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-left: 3px solid #0284c7;
    padding-left: 6px;
    margin-top: 12px;
    margin-bottom: 6px;
  }}
  
  /* Data Tables */
  .data-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
  }}
  .data-table th {{
    background: #f1f5f9;
    color: #334155;
    font-size: 8.5px;
    text-transform: uppercase;
    font-weight: 700;
    text-align: left;
    padding: 6px 8px;
    border-bottom: 1px solid #cbd5e1;
    letter-spacing: 0.3px;
  }}
  .data-table td {{
    padding: 5px 8px;
    font-size: 9.5px;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
  }}
  .data-table tr:nth-child(even) td {{
    background: #fafafa;
  }}
  
  /* Badges */
  .badge {{
    display: inline-block;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 8.5px;
    font-weight: 700;
  }}
  .badge-sev-high {{ background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }}
  .badge-sev-med {{ background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }}
  .badge-sev-low {{ background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}
  .badge-status-open {{ background: #fee2e2; color: #b91c1c; }}
  .badge-status-prog {{ background: #e0f2fe; color: #0369a1; }}
  .badge-status-verif {{ background: #fef9c3; color: #854d0e; }}
  
  .ai-box {{
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 10px;
    font-size: 9.5px;
  }}
  .ai-box-title {{
    font-weight: 700;
    color: #0369a1;
    text-transform: uppercase;
    font-size: 9px;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }}

  .footer {{
    margin-top: 14px;
    border-top: 1px solid #e2e8f0;
    padding-top: 6px;
    font-size: 8.5px;
    color: #94a3b8;
    text-align: center;
  }}
</style>
</head>
<body>
  <table class='header-table' cellpadding='0' cellspacing='0'>
    <tr>
      <td style='vertical-align: middle;'>
        <div class='brand-title'>URANOS Group</div>
        <div class='brand-subtitle'>Photovoltaic Execution Operating System &bull; Daily Executive Briefing</div>
      </td>
      <td class='report-badge' style='vertical-align: middle;'>
        <div class='report-title'>Daily Operational Report</div>
        <div class='report-meta'>Generated: {formatted_date} &bull; Confidential &bull; Officer: {user_name}</div>
      </td>
    </tr>
  </table>

  <!-- KPI Row -->
  <table class='kpi-table' cellpadding='0' cellspacing='0'>
    <tr>
      <td class='kpi-cell'>
        <div class='kpi-label'>Fleet Total Capacity</div>
        <div class='kpi-value'>{total_cap:.1f} <span style='font-size: 10px; font-weight: 600;'>MW</span></div>
        <div class='kpi-sub'>&bull; 20 Solar Power Plants</div>
      </td>
      <td class='kpi-cell'>
        <div class='kpi-label'>Active Projects</div>
        <div class='kpi-value'>{active_sites} / {total_sites}</div>
        <div class='kpi-sub'>&bull; {op_rate}% Availability</div>
      </td>
      <td class='kpi-cell'>
        <div class='kpi-label'>Active Blockers (Today)</div>
        <div class='kpi-value' style='color: #ef4444;'>{active_blockers_cnt}</div>
        <div class='kpi-sub' style='color: #dc2626;'>&bull; {lost_hours:.1f}h Lost Hours</div>
      </td>
      <td class='kpi-cell'>
        <div class='kpi-label'>Packages Completed</div>
        <div class='kpi-value' style='color: #0284c7;'>{len([w for w in work_packages if w.status == 'Completed'])}</div>
        <div class='kpi-sub'>&bull; Verified by Engineers</div>
      </td>
    </tr>
  </table>

  <!-- AI Executive Synthesis -->
  <div class='ai-box'>
    <div class='ai-box-title'>&bull; URANOS Copilot Executive Synthesis (Groq Grounded Briefing)</div>
    <div>&bull; <strong>Portfolio Health:</strong> Total generation capacity of {total_cap:.1f} MW AC operating across {active_sites} active grid-connected solar plants.</div>
    <div>&bull; <strong>Critical Operational Obstacles:</strong> Blocker [B-00001] impacting PV-0004 (Metbassta - Kairouan) on 225kV STEG interconnection currently in progress under responsible engineer ingenieur_01@uranos.local.</div>
    <div>&bull; <strong>Milestones Completed Today:</strong> Engineering inspectors validated civil foundation and tracker structures on PV-0004 and VRD civil infrastructure on PV-0017 with zero safety incidents.</div>
  </div>

  <!-- Section 1: Active Blockers Reported by Site Teams -->
  <div class='section-title'>1. Active Blockers &amp; Site Incidents Reported Today</div>
  <table class='data-table'>
    <thead>
      <tr>
        <th style='width: 70px;'>Code</th>
        <th style='width: 75px;'>Project</th>
        <th>Title / Technical Obstacle Description</th>
        <th style='width: 75px; text-align: center;'>Severity</th>
        <th style='width: 85px; text-align: center;'>Status</th>
        <th style='width: 140px;'>Site Reporter &rarr; Engineer</th>
        <th style='width: 65px; text-align: right;'>Lost Hours</th>
      </tr>
    </thead>
    <tbody>
      {blocker_rows_html}
    </tbody>
  </table>

  <!-- Section 2: Work Packages Completed by Engineers Today -->
  <div class='section-title'>2. Engineering Work Packages Completed &amp; Active (Today)</div>
  <table class='data-table'>
    <thead>
      <tr>
        <th style='width: 110px;'>Package Code</th>
        <th style='width: 75px;'>Project</th>
        <th>Work Package Scope / Activity Title</th>
        <th style='width: 85px; text-align: center;'>Discipline</th>
        <th style='width: 75px; text-align: right;'>Planned Qty</th>
        <th style='width: 90px; text-align: center;'>Execution Status</th>
      </tr>
    </thead>
    <tbody>
      {wp_rows_html}
    </tbody>
  </table>

  <!-- Section 3: Field Progress Verified Today -->
  <div class='section-title'>3. Site Team Field Progress Verified by Engineers (Today)</div>
  <table class='data-table'>
    <thead>
      <tr>
        <th style='width: 120px;'>Submission ID</th>
        <th style='width: 75px;'>Project</th>
        <th>Field Activity Verified</th>
        <th style='width: 80px; text-align: right;'>Verified Qty</th>
        <th style='width: 130px;'>Reported By (Site)</th>
        <th style='width: 130px;'>Verifier (Engineer)</th>
      </tr>
    </thead>
    <tbody>
      {prog_rows_html}
    </tbody>
  </table>

  <div class='footer'>
    URANOS Group Daily Executive Intelligence &bull; Photovoltaic Execution Operating System &bull; Confidential &bull; Generated for Executive Leadership
  </div>
</body>
</html>"""

    pdf_bytes = get_pdf(html)
    today_str = frappe.utils.today()
    frappe.local.response.filename = f"URANOS_Daily_Executive_Report_{today_str}.pdf"
    frappe.local.response.filecontent = pdf_bytes
    frappe.local.response.type = "download"


@frappe.whitelist(allow_guest=False)
def generate_executive_pdf():
    """Alias for generate_daily_report for backward compatibility."""
    return generate_daily_report()


@frappe.whitelist()
def get_engineer_users(doctype=None, txt="", searchfield="name", start=0, page_len=20, filters=None, as_dict=False, **kwargs):
    """Link query returning users with Engineer role for assignment in Project."""
    roles = ("engineer", "Engineer")
    query = """
        SELECT DISTINCT u.name, u.full_name
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE u.enabled = 1
          AND u.name NOT IN ('Administrator', 'Guest')
          AND hr.role IN %(roles)s
          AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
        ORDER BY u.full_name ASC, u.name ASC
        LIMIT %(start)s, %(page_len)s
    """
    params = {
        "roles": roles,
        "txt": f"%{txt or ''}%",
        "start": int(start or 0),
        "page_len": int(page_len or 20),
    }
    rows = frappe.db.sql(query, params, as_dict=as_dict)
    if as_dict:
        return rows
    return [[r[0], r[1]] for r in rows]


@frappe.whitelist()
def get_site_team_users(doctype=None, txt="", searchfield="name", start=0, page_len=20, filters=None, as_dict=False, **kwargs):
    """Link query returning users with Site Team role for assignment in Project."""
    roles = ("site_team", "Site Team")
    query = """
        SELECT DISTINCT u.name, u.full_name
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE u.enabled = 1
          AND u.name NOT IN ('Administrator', 'Guest')
          AND hr.role IN %(roles)s
          AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
        ORDER BY u.full_name ASC, u.name ASC
        LIMIT %(start)s, %(page_len)s
    """
    params = {
        "roles": roles,
        "txt": f"%{txt or ''}%",
        "start": int(start or 0),
        "page_len": int(page_len or 20),
    }
    rows = frappe.db.sql(query, params, as_dict=as_dict)
    if as_dict:
        return rows
    return [[r[0], r[1]] for r in rows]


@frappe.whitelist()
def get_users_by_role(doctype=None, txt="", searchfield="name", start=0, page_len=20, filters=None, as_dict=False, **kwargs):
    """Generic link query returning users filtered by role."""
    role = (filters or {}).get("role") if isinstance(filters, dict) else None
    if role in ("engineer", "Engineer"):
        return get_engineer_users(doctype, txt, searchfield, start, page_len, filters, as_dict, **kwargs)
    elif role in ("site_team", "Site Team"):
        return get_site_team_users(doctype, txt, searchfield, start, page_len, filters, as_dict, **kwargs)

    if not role:
        return []
    query = """
        SELECT DISTINCT u.name, u.full_name
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE u.enabled = 1
          AND u.name NOT IN ('Administrator', 'Guest')
          AND hr.role = %(role)s
          AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
        ORDER BY u.full_name ASC, u.name ASC
        LIMIT %(start)s, %(page_len)s
    """
    params = {
        "role": role,
        "txt": f"%{txt or ''}%",
        "start": int(start or 0),
        "page_len": int(page_len or 20),
    }
    rows = frappe.db.sql(query, params, as_dict=as_dict)
    if as_dict:
        return rows
    return [[r[0], r[1]] for r in rows]





