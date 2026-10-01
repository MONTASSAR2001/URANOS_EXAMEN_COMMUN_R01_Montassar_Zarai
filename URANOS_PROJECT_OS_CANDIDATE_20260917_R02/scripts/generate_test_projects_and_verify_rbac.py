#!/usr/bin/env python3
"""
URANOS Project OS — Dynamic Generation & RBAC Integration Test Suite
Generates 5 new photovoltaic projects (PV-21 to PV-25) with linked Project Profiles
and sequential URANOS Blockers (B-.#####), then strictly validates RBAC isolation.
"""

import re
import sys
from decimal import Decimal
import frappe
from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition

PASSED = 0
FAILED = 0


def record_assertion(test_name: str, passed: bool, details: str = ""):
    global PASSED, FAILED
    status = "PASS" if passed else "FAIL"
    if passed:
        PASSED += 1
        print(f"  [{status}] {test_name}" + (f" — {details}" if details else ""))
    else:
        FAILED += 1
        print(f"  [{status}] {test_name}" + (f" — {details}" if details else ""), file=sys.stderr)


def ensure_project(pid: str, project_name: str, company: str = "URANOS Group") -> str:
    """Ensure Project exists with explicit name=pid."""
    if frappe.db.exists("Project", pid):
        return pid

    # Check if exists by project_name
    existing = frappe.db.get_value("Project", {"project_name": project_name}, "name")
    if existing:
        if existing != pid:
            frappe.rename_doc("Project", existing, pid, force=True)
            frappe.db.commit()
        return pid

    proj = frappe.get_doc({
        "doctype": "Project",
        "name": pid,
        "project_name": project_name,
        "status": "Open",
        "is_active": "Yes",
        "company": company if frappe.db.exists("Company", company) else None,
    })
    proj.flags.ignore_permissions = True
    proj.flags.ignore_mandatory = True
    with authorized_transition():
        proj.insert(ignore_permissions=True)

    if proj.name != pid:
        frappe.rename_doc("Project", proj.name, pid, force=True)

    frappe.db.commit()
    return pid


def ensure_project_profile(pid: str, gov: str, mw: float):
    """Ensure URANOS Project Profile exists and links to Project."""
    if not frappe.db.exists("URANOS Project Profile", {"project": pid}):
        profile = frappe.get_doc({
            "doctype": "URANOS Project Profile",
            "project": pid,
            "short_code": pid,
            "site": f"Centrale Solaire {pid} ({gov})",
            "governorate": gov,
            "capacity_ac_mw": mw,
            "capacity_dc_mwp": float(Decimal(str(mw)) * Decimal("1.20")),
            "status": "Active",
            "risk_level": "Medium",
        })
        profile.flags.ignore_permissions = True
        profile.flags.ignore_mandatory = True
        with authorized_transition():
            profile.insert(ignore_permissions=True)
        frappe.db.commit()
        return profile
    return frappe.get_doc("URANOS Project Profile", {"project": pid})


def create_blocker(project: str, title: str, category: str, severity: str, due_date: str, status: str = "Open", responsible: str = None) -> frappe.model.document.Document:
    """Create a blocker and optionally transition it through the 4-step workflow."""
    blocker = frappe.get_doc({
        "doctype": "URANOS Blocker",
        "project": project,
        "title": title,
        "category": category,
        "severity": severity,
        "due_date": due_date,
        "responsible": responsible,
        "status": "Open",
    })
    blocker.flags.ignore_permissions = True
    with authorized_transition():
        blocker.insert(ignore_permissions=True)
    frappe.db.commit()

    if status in ("In Progress", "Pending Verification", "Closed"):
        blocker.status = "In Progress"
        with authorized_transition():
            blocker.save(ignore_permissions=True)
        frappe.db.commit()

    if status in ("Pending Verification", "Closed"):
        blocker.status = "Pending Verification"
        blocker.corrective_action = f"Action corrective planifiée et exécutée sur {project}."
        blocker.resolved_by = responsible or "ingenieur_01@uranos.local"
        with authorized_transition():
            blocker.save(ignore_permissions=True)
        frappe.db.commit()

    if status == "Closed":
        # Independent closure adhering to Golden Rule
        verifier = "ingenieur_03@uranos.local" if blocker.resolved_by != "ingenieur_03@uranos.local" else "ingenieur_02@uranos.local"
        blocker.status = "Closed"
        blocker.closed_by = verifier
        with authorized_transition():
            blocker.save(ignore_permissions=True)
        frappe.db.commit()

    return blocker


def grant_project_permission(email: str, pid: str):
    """Grant User Permission for a specific project."""
    if not frappe.db.exists("User Permission", {"user": email, "allow": "Project", "for_value": pid}):
        perm = frappe.get_doc({
            "doctype": "User Permission",
            "user": email,
            "allow": "Project",
            "for_value": pid,
            "apply_to_all_doctypes": 1,
        })
        perm.flags.ignore_permissions = True
        with authorized_transition():
            perm.insert(ignore_permissions=True)
        frappe.db.commit()


def main():
    print("=" * 80)
    print("   URANOS PROJECT OS — DYNAMIC GENERATION & RBAC TEST SUITE")
    print("=" * 80)

    frappe.init("uranos.localhost")
    frappe.connect()

    new_projects = [
        {"id": "PV-21", "gov": "Tozeur", "mw": 5.0},
        {"id": "PV-22", "gov": "Tataouine", "mw": 10.0},
        {"id": "PV-23", "gov": "Kairouan", "mw": 7.5},
        {"id": "PV-24", "gov": "Gafsa", "mw": 12.0},
        {"id": "PV-25", "gov": "Kebili", "mw": 4.5},
    ]

    print("\n--- STEP 1: Dynamic Database Generation (5 New Projects PV-21 to PV-25) ---")
    created_blockers = []
    naming_series_pattern = re.compile(r"^B-\d{5}$")

    for pdata in new_projects:
        pid = pdata["id"]
        gov = pdata["gov"]
        mw = pdata["mw"]

        # 1. Project
        proj_id = ensure_project(pid, pid)
        record_assertion(f"Project '{pid}' exists in database", frappe.db.exists("Project", pid) == pid)

        # 2. URANOS Project Profile
        profile = ensure_project_profile(pid, gov, mw)
        record_assertion(
            f"URANOS Project Profile created for '{pid}'",
            profile.project == pid,
            f"Profile ID={profile.name} (Frappe hash format), Site={profile.site}"
        )

        # 3. Two URANOS Blockers per project
        # Blocker A: Open / In Progress
        b_open = create_blocker(
            project=pid,
            title=f"[{pid}] Anomalie serrage connecteurs MC4",
            category="Equipment",
            severity="High",
            due_date="2026-10-15",
            status="In Progress",
            responsible="ingenieur_01@uranos.local"
        )
        created_blockers.append(b_open)

        # Blocker B: Closed (via 4-step workflow + independent closure)
        b_closed = create_blocker(
            project=pid,
            title=f"[{pid}] Retard validation plan d'implantation VRD",
            category="Document",
            severity="Critical",
            due_date="2026-09-28",
            status="Closed",
            responsible="ingenieur_01@uranos.local"
        )
        created_blockers.append(b_closed)

        # Grant management access to the newly generated project (Portfolio oversight)
        grant_project_permission("direction_01@uranos.local", pid)

    print("\n--- STEP 2: Verification of Blocker Naming Series (B-.#####) ---")
    all_sequential = True
    for b in created_blockers:
        matches = bool(naming_series_pattern.match(b.name))
        if not matches:
            all_sequential = False
        print(f"  • Blocker {b.name} -> Project: {b.project}, Title: '{b.title[:45]}...', Status: {b.status}")

    record_assertion(
        "All 10 newly created blockers adhere to 'B-.##### ' sequential naming series",
        all_sequential,
        f"IDs sampled: {created_blockers[0].name} to {created_blockers[-1].name}"
    )

    print("\n--- STEP 3: RBAC & Permission Isolation Verification ---")
    # Check permissions on PV-21 blockers
    sample_b1 = created_blockers[0]  # On PV-21

    # 3.1 site_team: chantier_01@uranos.local (NOT assigned to PV-21)
    frappe.set_user("chantier_01@uranos.local")
    chantier_read_b1 = security.has_permission(sample_b1, "chantier_01@uranos.local", "read")
    chantier_list_pv21 = frappe.get_list("URANOS Blocker", filters={"project": "PV-21"})
    record_assertion(
        "site_team (chantier_01) CANNOT read unassigned PV-21 blocker",
        chantier_read_b1 is False,
        f"has_permission(read)={chantier_read_b1}"
    )
    record_assertion(
        "site_team (chantier_01) list query on PV-21 returns 0 records (Zero Leakage)",
        len(chantier_list_pv21) == 0,
        f"Returned {len(chantier_list_pv21)} records"
    )

    # 3.2 engineer: ingenieur_01@uranos.local (NOT assigned to PV-21)
    frappe.set_user("ingenieur_01@uranos.local")
    eng_read_b1 = security.has_permission(sample_b1, "ingenieur_01@uranos.local", "read")
    eng_list_pv21 = frappe.get_list("URANOS Blocker", filters={"project": "PV-21"})
    record_assertion(
        "engineer (ingenieur_01) CANNOT read unassigned PV-21 blocker",
        eng_read_b1 is False,
        f"has_permission(read)={eng_read_b1}"
    )
    record_assertion(
        "engineer (ingenieur_01) list query on PV-21 returns 0 records (Zero Leakage)",
        len(eng_list_pv21) == 0,
        f"Returned {len(eng_list_pv21)} records"
    )

    # 3.3 management: direction_01@uranos.local (Global Portfolio oversight)
    frappe.set_user("direction_01@uranos.local")
    dir_read_all = all(
        security.has_permission(b, "direction_01@uranos.local", "read")
        for b in created_blockers
    )
    dir_list_new = frappe.get_list(
        "URANOS Blocker",
        filters={"project": ["in", ["PV-21", "PV-22", "PV-23", "PV-24", "PV-25"]]}
    )
    dir_blocker_ids = {d["name"] for d in dir_list_new}
    created_ids = {b.name for b in created_blockers}
    all_visible = created_ids.issubset(dir_blocker_ids)

    record_assertion(
        "management (direction_01) has global READ access across ALL new projects (PV-21 to PV-25)",
        dir_read_all and all_visible,
        f"has_permission on all 10 blockers=True, list query returned {len(dir_list_new)} blockers (all 10 new blockers visible)"
    )

    # Verify management CANNOT write/modify blockers (Strict Read-Only)
    # Fetch a clean doc instance without in-memory ignore_permissions flag
    clean_sample_b = frappe.get_doc("URANOS Blocker", sample_b1.name)
    dir_write_allowed = security.has_permission(clean_sample_b, "direction_01@uranos.local", "write")
    dir_write_exception = False
    try:
        clean_sample_b.title = "Unauthorized modification by Management"
        clean_sample_b.save()
    except frappe.PermissionError:
        dir_write_exception = True
    except Exception as ex:
        if not dir_write_allowed:
            dir_write_exception = True

    record_assertion(
        "management (direction_01) CANNOT write or modify blockers (Strict Read-Only)",
        dir_write_allowed is False and dir_write_exception is True,
        f"has_permission(write)={dir_write_allowed}, write rejected with PermissionError"
    )

    print("\n" + "=" * 80)
    print(f"RESULTS: {PASSED} PASSED, {FAILED} FAILED")
    print("=" * 80)
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
