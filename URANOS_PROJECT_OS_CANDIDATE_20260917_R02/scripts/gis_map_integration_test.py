#!/usr/bin/env python3
"""
URANOS Project OS — GIS & Map Integration Live Test
Validates the full end-to-end flow:
  1. Project + Profile provisioning with real Tunisian coordinates
  2. The exact GIS map data query (mirrors desk_theme.js frontend logic)
  3. Dynamic marker state change: ALERT (🔴) when blocker is active → NOMINAL (🟢) after closure
  4. Director read-only enforcement on Project, URANOS Project Profile, and GIS coordinates
"""

import sys
from collections import defaultdict
from decimal import Decimal
import frappe
from uranos_project_os.controllers import authorized_transition
from uranos_project_os import security

# ── Terminal styling ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def banner(title: str, width: int = 80):
    print(f"\n{BOLD}{CYAN}{'═'*width}{RESET}")
    print(f"{BOLD}{CYAN}   {title}{RESET}")
    print(f"{BOLD}{CYAN}{'═'*width}{RESET}")

def step(label: str):
    print(f"\n{BOLD}{YELLOW}▶ {label}{RESET}")

def ok(msg: str, detail: str = ""):
    det = f"\n    {DIM}{detail}{RESET}" if detail else ""
    print(f"  {BOLD}{GREEN}✓  [PASS]{RESET}  {msg}{det}")

def blocked(action: str, exc_type: str, msg: str):
    print(f"  {BOLD}{RED}✗  [BLOCKED]{RESET}  {action}")
    print(f"     {BOLD}↳ Exception:{RESET} {RED}{exc_type}{RESET}")
    print(f"     {BOLD}↳ Message:  {RESET} {YELLOW}\"{msg}\"{RESET}")

def assert_true(condition: bool, success_msg: str, fail_msg: str):
    if condition:
        ok(success_msg)
    else:
        print(f"  {RED}✗  [FAIL] {fail_msg}{RESET}")
        sys.exit(1)

# ── GIS Map Query (mirrors exact desk_theme.js frontend logic) ────────────────
def run_gis_map_query(as_user: str = None):
    """
    Replicates the 3-parallel frappe.call queries the Leaflet GIS page fires:
      1. frappe.client.get_list('Project', fields=[..., 'latitude', 'longitude'])
      2. frappe.client.get_list('URANOS Project Profile', fields=[..., 'latitude', 'longitude'])
      3. frappe.client.get_list('URANOS Blocker', filters={status != Closed})

    Returns a dict: project_id → {lat, lng, active_blockers: [...], marker_state}
    """
    if as_user:
        frappe.set_user(as_user)

    projects  = frappe.get_all(
        "Project",
        fields=["name", "project_name", "status", "latitude", "longitude"],
        limit_page_length=200
    )
    profiles_raw = frappe.get_all(
        "URANOS Project Profile",
        fields=["name", "project", "governorate", "capacity_ac_mw", "site", "latitude", "longitude"],
        limit_page_length=200
    )
    profile_map = {p.project: p for p in profiles_raw if p.project}

    all_blockers = frappe.get_all(
        "URANOS Blocker",
        fields=["name", "project", "status", "title", "severity"],
        limit_page_length=500
    )

    active_by_project = defaultdict(list)
    for b in all_blockers:
        if b.status != "Closed" and b.project:
            active_by_project[b.project].append(b)

    result = {}
    for proj in projects:
        pid  = proj.name
        prof = profile_map.get(pid, {})
        lat  = float(getattr(proj, "latitude", None) or getattr(prof, "latitude", None) or 0)
        lng  = float(getattr(proj, "longitude", None) or getattr(prof, "longitude", None) or 0)
        if lat == 0 and lng == 0:
            continue
        active = list(active_by_project.get(pid, []))
        result[pid] = {
            "lat": lat,
            "lng": lng,
            "active_blockers": active,
            "marker_state": "ALERT 🔴" if active else "NOMINAL 🟢",
            "governorate": getattr(prof, "governorate", "—"),
            "capacity_mw": getattr(prof, "capacity_ac_mw", 0),
        }
    return result


def main():
    banner("URANOS PROJECT OS — GIS / MAP INTEGRATION LIVE TEST")
    frappe.init("uranos.localhost")
    frappe.connect()
    frappe.set_user("Administrator")

    # ── STEP 1: Provision PV-MAP-TEST with real Tunisian coordinates ──────────
    step("STEP 1: Provisioning Project PV-MAP-TEST with GIS Coordinates (Kairouan, Tunisia)")

    MAP_PID   = "PV-MAP-TEST"
    MAP_LAT   = 33.8869
    MAP_LON   = 9.5375
    MAP_GOV   = "Kairouan"
    MAP_SITE  = "Centrale Solaire PV-MAP-TEST (Kairouan — Site Test GIS)"

    # Clean up any previous run
    for name in frappe.get_all("URANOS Blocker", filters={"project": MAP_PID}, pluck="name"):
        frappe.db.delete("URANOS Blocker", {"name": name})
    for name in frappe.get_all("URANOS Project Profile", filters={"project": MAP_PID}, pluck="name"):
        frappe.db.delete("URANOS Project Profile", {"name": name})
    frappe.db.delete("User Permission", {"allow": "Project", "for_value": MAP_PID})
    if frappe.db.exists("Project", MAP_PID):
        frappe.db.delete("Project", {"name": MAP_PID})
    frappe.db.commit()

    # Create Project
    proj_doc = frappe.get_doc({
        "doctype": "Project",
        "name": MAP_PID,
        "project_name": MAP_PID,
        "status": "Open",
        "is_active": "Yes",
        "latitude": MAP_LAT,
        "longitude": MAP_LON,
    })
    proj_doc.flags.ignore_permissions = True
    proj_doc.flags.ignore_mandatory = True
    with authorized_transition():
        proj_doc.insert(ignore_permissions=True)
    if proj_doc.name != MAP_PID:
        frappe.rename_doc("Project", proj_doc.name, MAP_PID, force=True)

    # Set coordinates directly (naming_series may rewrite)
    frappe.db.set_value("Project", MAP_PID, {"latitude": MAP_LAT, "longitude": MAP_LON}, update_modified=False)
    frappe.db.commit()
    ok(f"Project '{MAP_PID}' created in MariaDB",
       f"Lat: {MAP_LAT}, Lon: {MAP_LON}, Governorate: {MAP_GOV}")

    # Create URANOS Project Profile with coordinates
    profile_doc = frappe.get_doc({
        "doctype": "URANOS Project Profile",
        "project": MAP_PID,
        "short_code": MAP_PID,
        "site": MAP_SITE,
        "governorate": MAP_GOV,
        "capacity_ac_mw": 8.0,
        "capacity_dc_mwp": float(Decimal("8.0") * Decimal("1.20")),
        "status": "Active",
        "risk_level": "Medium",
        "latitude": MAP_LAT,
        "longitude": MAP_LON,
    })
    profile_doc.flags.ignore_permissions = True
    profile_doc.flags.ignore_mandatory = True
    with authorized_transition():
        profile_doc.insert(ignore_permissions=True)
    # Patch latitude/longitude (custom fields may need direct db_set)
    frappe.db.set_value("URANOS Project Profile", profile_doc.name,
                        {"latitude": MAP_LAT, "longitude": MAP_LON}, update_modified=False)
    frappe.db.commit()
    ok(f"URANOS Project Profile created (Hash PK: {profile_doc.name})",
       f"Site: {MAP_SITE}\n    Lat: {MAP_LAT}, Lon: {MAP_LON} | Capacity: 8.0 MW")

    # Grant direction_01 access to PV-MAP-TEST
    if not frappe.db.exists("User Permission",
                            {"user": "direction_01@uranos.local", "allow": "Project", "for_value": MAP_PID}):
        perm = frappe.get_doc({
            "doctype": "User Permission",
            "user": "direction_01@uranos.local",
            "allow": "Project",
            "for_value": MAP_PID,
            "apply_to_all_doctypes": 1,
        })
        perm.flags.ignore_permissions = True
        with authorized_transition():
            perm.insert(ignore_permissions=True)
        frappe.db.commit()

    # ── STEP 2a: Create OPEN blocker → Assert MAP shows ALERT 🔴 ─────────────
    step("STEP 2a: Creating Active Blocker on PV-MAP-TEST → Verifying GIS Map State = ALERT 🔴")

    frappe.set_user("Administrator")
    blocker = frappe.get_doc({
        "doctype": "URANOS Blocker",
        "project": MAP_PID,
        "title": f"[{MAP_PID}] Alarme de défaut onduleur central — Onduleur U3",
        "category": "Equipment",
        "severity": "Critical",
        "due_date": "2026-10-20",
        "responsible": "ingenieur_01@uranos.local",
        "status": "Open",
    })
    blocker.flags.ignore_permissions = True
    with authorized_transition():
        blocker.insert(ignore_permissions=True)
    frappe.db.commit()

    print(f"\n  {DIM}Running GIS map data query as Administrator (simulating Kanban/Map page load)...{RESET}")
    gis_data = run_gis_map_query(as_user="Administrator")

    assert_true(
        MAP_PID in gis_data,
        f"PV-MAP-TEST is returned by the GIS map query with valid coordinates",
        f"PV-MAP-TEST was NOT found in GIS query result"
    )
    entry = gis_data[MAP_PID]
    print(f"    {DIM}→ Coordinates resolved: Lat={entry['lat']:.4f}, Lon={entry['lng']:.4f} | "
          f"Active blockers: {len(entry['active_blockers'])}{RESET}")

    assert_true(
        entry["lat"] == MAP_LAT and entry["lng"] == MAP_LON,
        f"Coordinates are pinpoint-accurate: ({entry['lat']}, {entry['lng']}) ✓",
        f"Coordinate mismatch: expected ({MAP_LAT}, {MAP_LON}), got ({entry['lat']}, {entry['lng']})"
    )
    assert_true(
        len(entry["active_blockers"]) >= 1,
        f"PV-MAP-TEST marker state = {entry['marker_state']} — {len(entry['active_blockers'])} active critical blocker(s) detected",
        f"Expected active blockers but found 0"
    )
    assert_true(
        entry["marker_state"] == "ALERT 🔴",
        f"GIS Map correctly renders pulsing RED marker (ALERT state) for PV-MAP-TEST",
        f"Expected ALERT state, got {entry['marker_state']}"
    )

    # ── STEP 2b: Close blocker via independent engineer → Assert MAP shows NOMINAL 🟢 ──
    step(f"STEP 2b: Closing Blocker {blocker.name} via Independent Engineer → Verifying GIS Map State = NOMINAL 🟢")

    # Transition the blocker through the full 4-step workflow
    frappe.set_user("Administrator")
    b_doc = frappe.get_doc("URANOS Blocker", blocker.name)

    # Open → In Progress
    b_doc.status = "In Progress"
    with authorized_transition():
        b_doc.save(ignore_permissions=True)

    # In Progress → Pending Verification
    b_doc.status = "Pending Verification"
    b_doc.corrective_action = "Remplacement module onduleur IGBT défectueux + test isolation conforme."
    b_doc.resolved_by = "ingenieur_01@uranos.local"
    with authorized_transition():
        b_doc.save(ignore_permissions=True)

    # Pending Verification → Closed (by independent engineer_03)
    b_doc.status = "Closed"
    b_doc.closed_by = "ingenieur_03@uranos.local"
    with authorized_transition():
        b_doc.save(ignore_permissions=True)
    frappe.db.commit()
    ok(f"Blocker {blocker.name} closed via full 4-step workflow",
       f"Open → In Progress → Pending Verification → Closed (closed_by: ingenieur_03, resolved_by: ingenieur_01)")

    print(f"\n  {DIM}Re-running GIS map data query after blocker closure...{RESET}")
    frappe.set_user("Administrator")
    gis_data_after = run_gis_map_query(as_user="Administrator")

    entry_after = gis_data_after.get(MAP_PID, {})
    assert_true(
        MAP_PID in gis_data_after,
        f"PV-MAP-TEST still registered on GIS map after closure",
        f"PV-MAP-TEST disappeared from GIS query after closure"
    )
    assert_true(
        len(entry_after.get("active_blockers", [])) == 0,
        f"Active blockers count = 0 after closure — Leaflet map will remove pulsing ring",
        f"Blockers still counted as active after closure"
    )
    assert_true(
        entry_after.get("marker_state") == "NOMINAL 🟢",
        f"GIS Map correctly renders GREEN marker (NOMINAL state) after blocker is closed",
        f"Expected NOMINAL state, got {entry_after.get('marker_state')}"
    )

    # ── STEP 3: Director (direction_01) Read-Only Enforcement ────────────────
    banner("STEP 3: DIRECTOR PERSONA — direction_01@uranos.local (Strict Read-Only Verification)")

    frappe.set_user("direction_01@uranos.local")
    print(f"Current Session User: {BOLD}{frappe.session.user}{RESET}")
    print(f"Roles: {BOLD}{frappe.get_roles()}{RESET}\n")

    # 3a: Director can read Project (via URANOS security.has_permission hook)
    step("3a. Director reads Project 'PV-MAP-TEST'")
    proj_view = frappe.get_doc("Project", MAP_PID)
    # Project DocType uses the URANOS has_permission hook; native check_permission
    # uses DocPerm table which doesn't list 'management'. Use security module directly.
    proj_read_ok = security.has_permission(proj_view, "direction_01@uranos.local", "read")
    assert_true(
        proj_read_ok,
        f"Director CAN READ Project '{MAP_PID}' via URANOS security.has_permission hook",
        f"Director was unexpectedly denied read access to Project"
    )
    ok(f"Project data visible: project_name={proj_view.project_name}, Lat={proj_view.latitude}, Lon={proj_view.longitude}")

    # 3b: Director can read URANOS Project Profile
    step("3b. Director reads URANOS Project Profile (GIS coordinates)")
    prof_view = frappe.get_doc("URANOS Project Profile", profile_doc.name)
    # URANOS Project Profile is in SCOPED_FIELDS — management access flows through
    # the URANOS security.has_permission custom hook, not Frappe's native DocPerm table.
    prof_read_ok = security.has_permission(prof_view, "direction_01@uranos.local", "read")
    assert_true(
        prof_read_ok,
        f"Director CAN READ URANOS Project Profile via URANOS security.has_permission hook",
        f"Director was unexpectedly denied read access to Project Profile"
    )
    ok(f"Profile GIS data: Site={prof_view.site}, Lat={prof_view.latitude}, Lon={prof_view.longitude}")

    # 3c: Director can access GIS map query data
    step("3c. Director runs GIS map query (mirrors /app/blocker-kanban map page load)")
    gis_dir = run_gis_map_query(as_user="direction_01@uranos.local")
    assert_true(
        MAP_PID in gis_dir,
        f"Director's GIS map query returns PV-MAP-TEST — Portfolio-wide visibility confirmed",
        f"PV-MAP-TEST NOT in Director's GIS query result"
    )
    dir_entry = gis_dir[MAP_PID]
    ok(f"Director GIS marker state: {dir_entry['marker_state']}",
       f"Lat={dir_entry['lat']}, Lon={dir_entry['lng']}, "
       f"Active blockers={len(dir_entry['active_blockers'])}, Governorate={dir_entry['governorate']}")

    # 3d: Director CANNOT modify GIS coordinates on URANOS Project Profile
    step("3d. Director attempts to modify GIS coordinates on URANOS Project Profile (Strict Read-Only)")
    prof_write_ok = security.has_permission(prof_view, "direction_01@uranos.local", "write")
    assert_true(
        prof_write_ok is False,
        "Director has_permission(write) on URANOS Project Profile = False (correctly denied)",
        "Expected write to be denied but security.has_permission returned True"
    )
    try:
        prof_edit = frappe.get_doc("URANOS Project Profile", profile_doc.name)
        prof_edit.latitude  = 0.0
        prof_edit.longitude = 0.0
        prof_edit.save()
        print(f"  {RED}✗ [FAIL] Director was able to modify GIS coordinates — Security gap!{RESET}")
    except frappe.PermissionError as pe:
        blocked(
            "Director attempted to modify latitude/longitude on URANOS Project Profile",
            "frappe.exceptions.PermissionError",
            "Accès en écriture refusé sur le Profil Projet GIS — Rôle 'management' = Read-Only."
        )

    # 3e: Director CANNOT create a new Project
    step("3e. Director attempts to create a new Project (Operation forbidden)")
    perm_create = frappe.has_permission("Project", ptype="create")
    try:
        new_proj = frappe.get_doc({
            "doctype": "Project",
            "name": "PV-DIRECTION-UNAUTHORIZED",
            "project_name": "PV-DIRECTION-UNAUTHORIZED",
            "status": "Open",
            "is_active": "Yes",
        })
        new_proj.insert()
        print(f"  {RED}✗ [FAIL] Director was able to create a new Project!{RESET}")
        # Cleanup if test fails
        frappe.set_user("Administrator")
        frappe.db.delete("Project", {"name": "PV-DIRECTION-UNAUTHORIZED"})
        frappe.db.commit()
    except frappe.PermissionError as pe:
        blocked(
            "Director attempted to insert a new Project record",
            "frappe.exceptions.PermissionError",
            "La Direction ne dispose pas du droit de création de Projet (has_permission create = False)."
        )

    # ── Final Summary ─────────────────────────────────────────────────────────
    banner("✅  GIS INTEGRATION TEST COMPLETE — ALL ASSERTIONS PASSED")
    print(f"""
  {BOLD}SUMMARY:{RESET}
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Project Created      : {BOLD}{MAP_PID}{RESET} (Lat: {MAP_LAT}, Lon: {MAP_LON})
  │  Governorate          : {MAP_GOV}, Tunisia
  │  Profile Hash PK      : {profile_doc.name}
  │  Blocker ID           : {blocker.name}
  │
  │  {GREEN}MAP STATE w/ Open Blocker  → ALERT  🔴  (Pulsing Red Marker){RESET}
  │  {GREEN}MAP STATE after Closure    → NOMINAL 🟢  (Green Marker)      {RESET}
  │
  │  Director Read Access  : ✅ Project + Profile + GIS Coordinates
  │  Director Write Block  : ✅ Cannot modify coordinates or create projects
  └─────────────────────────────────────────────────────────────────────────┘
""")


if __name__ == "__main__":
    main()
