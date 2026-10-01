import re

PY_PATH = 'apps/uranos_project_os/uranos_project_os/services/ai_synthesis.py'

def patch_ai_synthesis():
    with open(PY_PATH, 'r', encoding='utf-8') as f:
        code = f.read()

    # 1. Add fetch_holistic_project_context if not present
    if 'def fetch_holistic_project_context(' not in code:
        helper_code = '''
def fetch_holistic_project_context(project: str) -> Dict[str, Any]:
    """Retrieve comprehensive project progress, baseline, and defect/blocker data.

    Returns structured data covering:
    - Active Defects/Blockers (from URANOS Blocker)
    - Completed Work (from URANOS Field Progress Entry / verified progress)
    - Remaining Work (from URANOS Baseline Item vs completed, or pending work)
    - Overall Project Profile (from URANOS Project Profile & Project)
    """
    # 1. Active Defects/Blockers
    open_blockers = frappe.get_all(
        "URANOS Blocker",
        filters={
            "project": project,
            "status": ["in", ["Open", "In Progress", "Pending Verification"]],
        },
        fields=[
            "name",
            "title",
            "severity",
            "category",
            "status",
            "description",
            "lost_hours",
            "opened_at",
            "work_package",
        ],
        order_by="opened_at desc",
    )

    closed_blockers = frappe.get_all(
        "URANOS Blocker",
        filters={"project": project, "status": "Closed"},
        fields=[
            "name",
            "title",
            "severity",
            "category",
            "resolution",
            "closed_at",
            "lost_hours",
        ],
        limit=10,
        order_by="closed_at desc",
    )

    # 2. Progress Entries & Completed Work
    progress_entries = []
    try:
        progress_entries = frappe.get_all(
            "URANOS Field Progress Entry",
            filters={"project": project},
            fields=["name", "work_package", "qty_reported", "qty_verified", "status", "posting_date", "activity", "zone"],
            order_by="posting_date desc",
            limit=50,
        )
    except Exception as e:
        logger.warning("Could not fetch field progress entries: %s", e)

    total_reported_qty = sum(float(e.get("qty_reported") or 0) for e in progress_entries)
    total_verified_qty = sum(float(e.get("qty_verified") or 0) for e in progress_entries)
    verified_entries = [e for e in progress_entries if e.get("status") == "Verified"]

    # 3. Baseline Planned Quantities & Remaining Work
    baseline_items = []
    baseline_info = None
    try:
        profiles = frappe.get_all("URANOS Project Profile", filters={"project": project}, fields=["name", "current_baseline", "status", "capacity_ac_mw", "capacity_dc_mwp", "site", "governorate", "risk_level"], limit=1)
        profile_data = profiles[0] if profiles else {}
        current_bl_name = profile_data.get("current_baseline")
        if current_bl_name:
            bl_doc = frappe.get_all("URANOS Baseline", filters={"name": current_bl_name}, fields=["name", "version", "status"])
            if bl_doc:
                baseline_info = bl_doc[0]
                baseline_items = frappe.get_all("URANOS Baseline Item", filters={"parent": current_bl_name}, fields=["work_package", "qty_planned", "uom"])
        if not baseline_items:
            bls = frappe.get_all("URANOS Baseline", filters={"project": project}, fields=["name", "version", "status"])
            if bls:
                baseline_info = bls[0]
                baseline_items = frappe.get_all("URANOS Baseline Item", filters={"parent": bls[0]["name"]}, fields=["work_package", "qty_planned", "uom"])
    except Exception as e:
        logger.warning("Could not fetch baseline items: %s", e)

    total_planned_qty = sum(float(b.get("qty_planned") or 0) for b in baseline_items)
    remaining_qty = max(0.0, total_planned_qty - total_verified_qty) if total_planned_qty > 0 else 0.0

    proj_profile = {}
    try:
        profiles = frappe.get_all("URANOS Project Profile", filters={"project": project}, fields=["status", "capacity_ac_mw", "capacity_dc_mwp", "site", "governorate", "risk_level"], limit=1)
        if profiles:
            proj_profile = profiles[0]
    except Exception:
        pass

    completed_work = {
        "verified_quantity_total": total_verified_qty,
        "reported_quantity_total": total_reported_qty,
        "verified_entries_count": len(verified_entries),
        "recent_progress_entries": [
            {
                "id": e.get("name"),
                "work_package": e.get("work_package"),
                "activity": e.get("activity"),
                "qty_verified": float(e.get("qty_verified") or 0),
                "status": e.get("status"),
                "date": str(e.get("posting_date") or ""),
            }
            for e in progress_entries[:10]
        ],
        "summary": (
            f"{total_verified_qty:.1f} verified units completed across {len(verified_entries)} verified site submissions"
            if (total_verified_qty > 0 or verified_entries)
            else "No verified field progress entries recorded in database to date"
        ),
    }

    remaining_work = {
        "planned_quantity_total": total_planned_qty,
        "remaining_quantity_to_execute": remaining_qty,
        "baseline_version": baseline_info.get("version") if baseline_info else "No approved baseline",
        "pending_work_packages": [
            {
                "work_package": b.get("work_package"),
                "qty_planned": float(b.get("qty_planned") or 0),
                "uom": b.get("uom"),
            }
            for b in baseline_items[:10]
        ],
        "summary": (
            f"{remaining_qty:.1f} units remaining against baseline total of {total_planned_qty:.1f} planned units"
            if total_planned_qty > 0
            else f"Baseline tracking pending; project status: {proj_profile.get('status', 'Open')} (Site: {proj_profile.get('site', project)}, Capacity: {proj_profile.get('capacity_dc_mwp', '1.2')} MWp)"
        ),
    }

    total_lost_hours = sum((Decimal(str(b.get("lost_hours") or 0)) for b in open_blockers), Decimal("0"))
    critical_count = sum(1 for b in open_blockers if str(b.get("severity", "")).lower() in ("critical", "high"))

    active_defects_blockers = {
        "total_active_count": len(open_blockers),
        "critical_high_count": critical_count,
        "cumulative_lost_hours": float(total_lost_hours),
        "items": [
            {
                "id": b.get("name"),
                "title": b.get("title"),
                "severity": b.get("severity"),
                "category": b.get("category"),
                "status": b.get("status"),
                "work_package": b.get("work_package"),
                "lost_hours": float(b.get("lost_hours") or 0),
                "description": b.get("description"),
            }
            for b in open_blockers[:15]
        ],
        "historical_resolutions": [
            {
                "id": b.get("name"),
                "title": b.get("title"),
                "category": b.get("category"),
                "resolution": b.get("resolution"),
                "lost_hours": float(b.get("lost_hours") or 0),
            }
            for b in closed_blockers[:10]
        ],
    }

    return {
        "project": project,
        "open_blockers": open_blockers,
        "closed_blockers": closed_blockers,
        "completed_work": completed_work,
        "remaining_work": remaining_work,
        "active_defects_blockers": active_defects_blockers,
        "project_profile": proj_profile,
    }

'''
        # Insert before call_cloud_llm_synthesis
        target = 'def call_cloud_llm_synthesis('
        code = code.replace(target, helper_code + '\n' + target, 1)
        print("Injected fetch_holistic_project_context")

    with open(PY_PATH, 'w', encoding='utf-8') as f:
        f.write(code)
    print("Saved ai_synthesis.py step 1")

patch_ai_synthesis()
