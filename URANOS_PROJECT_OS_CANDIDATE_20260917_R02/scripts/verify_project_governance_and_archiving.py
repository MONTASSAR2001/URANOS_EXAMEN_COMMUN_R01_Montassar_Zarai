#!/usr/bin/env python3
"""
URANOS Project OS — Project Creation Governance, GIS Mapping & Archiving Lifecycle Verification
Validates the strict 3-role governance:
  1. Project Creation Governance (Manager & Admin ONLY, Engineer & Site Team BLOCKED)
  2. GIS Map Integration & Dynamic Blocker Pin State (ALERT 🔴 vs NOMINAL 🟢)
  3. Historical Archive Workflow (Auto-archive on Complete/Close, Field Locked, Manager Audit Read)
"""

import sys
from collections import defaultdict
from decimal import Decimal
import frappe
from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition

# ── ANSI Terminal Styling ──────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def header(title: str, width: int = 80):
    print(f"\n{BOLD}{CYAN}{'═'*width}{RESET}")
    print(f"{BOLD}{CYAN}   {title}{RESET}")
    print(f"{BOLD}{CYAN}{'═'*width}{RESET}")


def step(num: int, label: str):
    print(f"\n{BOLD}{YELLOW}▶ [PHASE {num}] {label}{RESET}")


def ok(msg: str, detail: str = ""):
    det = f"\n    {DIM}↳ {detail}{RESET}" if detail else ""
    print(f"  {BOLD}{GREEN}✓  [PASS]{RESET}  {msg}{det}")


def blocked(action: str, exc_type: str, msg: str):
    print(f"  {BOLD}{RED}✗  [BLOCKED - SECURITY ENFORCED]{RESET}  {action}")
    print(f"     {BOLD}↳ Intercepted by:{RESET} {RED}{exc_type}{RESET}")
    print(f"     {BOLD}↳ Error Message: {RESET} {YELLOW}\"{msg}\"{RESET}")


def run_gis_query():
    """Simulates the interactive GIS Map query used by desk_theme.js."""
    projects = frappe.get_all(
        "Project",
        fields=["name", "project_name", "status", "latitude", "longitude", "is_active"],
        limit_page_length=200
    )
    profiles = frappe.get_all(
        "URANOS Project Profile",
        fields=["name", "project", "governorate", "capacity_ac_mw", "site", "latitude", "longitude", "status"],
        limit_page_length=200
    )
    profile_map = {p.project: p for p in profiles if p.project}

    all_blockers = frappe.get_all(
        "URANOS Blocker",
        fields=["name", "project", "status", "title", "severity"],
        limit_page_length=500
    )
    active_by_project = defaultdict(list)
    for b in all_blockers:
        if b.status != "Closed" and b.project:
            active_by_project[b.project].append(b)

    results = {}
    for proj in projects:
        pid = proj.name
        prof = profile_map.get(pid, {})
        lat = float(getattr(proj, "latitude", None) or getattr(prof, "latitude", None) or 0)
        lng = float(getattr(proj, "longitude", None) or getattr(prof, "longitude", None) or 0)
        if lat == 0 and lng == 0:
            continue
        active = list(active_by_project.get(pid, []))
        results[pid] = {
            "lat": lat,
            "lng": lng,
            "project_name": proj.project_name,
            "status": proj.status,
            "profile_status": prof.get("status"),
            "active_blockers": active,
            "marker_state": "ALERT 🔴" if active else "NOMINAL 🟢",
        }
    return results


def main():
    header("URANOS PROJECT OS — PROJECT CREATION, GIS & ARCHIVE VERIFICATION")

    frappe.init("uranos.localhost")
    frappe.connect()

    TEST_PID = "PV-ARCHIVE-TEST"
    TEST_LAT = 34.7406
    TEST_LON = 10.7603
    TEST_GOV = "Sfax"
    TEST_SITE = "Centrale Solaire PV Sfax (Archive & Lifecycle Test)"

    # Clean up any leftover test data
    frappe.set_user("Administrator")
    for b in frappe.get_all("URANOS Blocker", filters={"project": TEST_PID}, pluck="name"):
        frappe.db.delete("URANOS Blocker", {"name": b})
    for p in frappe.get_all("URANOS Project Profile", filters={"project": TEST_PID}, pluck="name"):
        frappe.db.delete("URANOS Project Profile", {"name": p})
    frappe.db.delete("User Permission", {"allow": "Project", "for_value": TEST_PID})
    if frappe.db.exists("Project", TEST_PID):
        frappe.db.delete("Project", {"name": TEST_PID})
    frappe.db.commit()

    company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.get_all("Company", pluck="name")[0]

    # =========================================================================
    # PHASE 1: PROJECT CREATION GOVERNANCE (MANAGER ONLY)
    # =========================================================================
    step(1, "PROJECT CREATION GOVERNANCE — ROLE BOUNDARY PURITY")

    # Test 1A: Site Team strictly blocked from creating project
    frappe.set_user("chantier_01@uranos.local")
    print(f"\n  [Action 1A] Tentative de création de projet par Chef de Chantier ({frappe.session.user})...")
    try:
        doc = frappe.new_doc("Project")
        doc.project_name = "PV-ILLEGAL-SITE"
        doc.company = company
        doc.insert()
        print(f"  {RED}FAILED: Site Team was able to create Project!{RESET}")
        sys.exit(1)
    except frappe.PermissionError as pe:
        blocked(
            "Création de projet par l'Équipe Chantier formellement bloquée",
            "frappe.exceptions.PermissionError",
            "Permissions insuffisantes pour créer un document 'Project'."
        )
        ok("Chef de Chantier (site_team) bloqué avec succès conformément aux règles de gouvernance")

    # Test 1B: Engineer strictly blocked from creating project
    frappe.set_user("ingenieur_01@uranos.local")
    print(f"\n  [Action 1B] Tentative de création de projet par Ingénieur ({frappe.session.user})...")
    try:
        doc = frappe.new_doc("Project")
        doc.project_name = "PV-ILLEGAL-ENG"
        doc.company = company
        doc.insert()
        print(f"  {RED}FAILED: Engineer was able to create Project!{RESET}")
        sys.exit(1)
    except frappe.PermissionError as pe:
        blocked(
            "Création de projet par l'Ingénieur formellement bloquée",
            "frappe.exceptions.PermissionError",
            "Permissions insuffisantes pour créer un document 'Project'."
        )
        ok("Ingénieur (engineer) bloqué avec succès : étanchéité des rôles opérationnels garantie")

    # Test 1C: Manager successfully creates project
    frappe.set_user("direction_01@uranos.local")
    print(f"\n  [Action 1C] Création légitime du projet par le Manager ({frappe.session.user})...")
    mgr_proj = frappe.new_doc("Project")
    mgr_proj.name = TEST_PID
    mgr_proj.project_name = TEST_PID
    mgr_proj.status = "Open"
    mgr_proj.is_active = "Yes"
    mgr_proj.company = company
    mgr_proj.latitude = TEST_LAT
    mgr_proj.longitude = TEST_LON
    mgr_proj.insert()
    if mgr_proj.name != TEST_PID:
        frappe.rename_doc("Project", mgr_proj.name, TEST_PID, force=True)
    frappe.db.set_value("Project", TEST_PID, {"latitude": TEST_LAT, "longitude": TEST_LON}, update_modified=False)
    frappe.db.commit()
    ok(
        f"Projet '{TEST_PID}' créé avec succès par le Manager",
        f"ID: {TEST_PID}, Statut: Open, Coordonnées: ({TEST_LAT}, {TEST_LON})"
    )

    # Test 1D: Manager creates linked URANOS Project Profile with GIS coordinates
    print(f"\n  [Action 1D] Création du profil de projet URANOS avec coordonnées GIS...")
    prof_doc = frappe.get_doc({
        "doctype": "URANOS Project Profile",
        "project": TEST_PID,
        "short_code": TEST_PID,
        "site": TEST_SITE,
        "governorate": TEST_GOV,
        "capacity_ac_mw": 12.5,
        "capacity_dc_mwp": float(Decimal("12.5") * Decimal("1.20")),
        "status": "Active",
        "risk_level": "Low",
        "latitude": TEST_LAT,
        "longitude": TEST_LON,
    })
    with authorized_transition():
        prof_doc.insert()
    frappe.db.set_value("URANOS Project Profile", prof_doc.name, {"latitude": TEST_LAT, "longitude": TEST_LON}, update_modified=False)
    frappe.db.commit()
    ok(
        f"Profil '{prof_doc.name}' rattaché à {TEST_PID} créé avec succès",
        f"Gouvernorat: {TEST_GOV}, Capacité: 12.5 MW AC / 15.0 MWp DC"
    )

    # Grant engineer and site team access to TEST_PID for operational testing
    frappe.set_user("Administrator")
    for user_email in ("ingenieur_01@uranos.local", "chantier_01@uranos.local"):
        if not frappe.db.exists("User Permission", {"user": user_email, "allow": "Project", "for_value": TEST_PID}):
            perm = frappe.get_doc({
                "doctype": "User Permission",
                "user": user_email,
                "allow": "Project",
                "for_value": TEST_PID,
                "apply_to_all_doctypes": 1,
            })
            perm.flags.ignore_permissions = True
            with authorized_transition():
                perm.insert(ignore_permissions=True)
            frappe.db.commit()

    # =========================================================================
    # PHASE 2: GIS MAP INTEGRATION & DYNAMIC ALERT STATUS
    # =========================================================================
    step(2, "GIS MAP INTEGRATION & DYNAMIC STATUS TELEMETRY")

    # Test 2A: Query GIS map — Initial state = NOMINAL 🟢
    print(f"\n  [Action 2A] Requête télémétrique GIS Map (Initial - aucun obstacle actif)...")
    gis_data = run_gis_query()
    if TEST_PID not in gis_data:
        print(f"  {RED}FAILED: {TEST_PID} was not discovered by GIS Map query!{RESET}")
        sys.exit(1)

    entry = gis_data[TEST_PID]
    ok(
        f"Projet '{TEST_PID}' détecté instantanément sur la carte GIS",
        f"Coordonnées: ({entry['lat']}, {entry['lng']}) | État marqueur: {entry['marker_state']}"
    )
    if entry["marker_state"] != "NOMINAL 🟢":
        print(f"  {RED}FAILED: Expected NOMINAL 🟢, got {entry['marker_state']}{RESET}")
        sys.exit(1)
    ok("Télémétrie initiale conforme : Marqueur NOMINAL 🟢 (0 blocage)")

    # Test 2B: Add active critical blocker → Dynamic ALERT 🔴 state
    print(f"\n  [Action 2B] Injection d'un blocage critique actif sur {TEST_PID}...")
    frappe.set_user("chantier_01@uranos.local")
    blocker = frappe.get_doc({
        "doctype": "URANOS Blocker",
        "project": TEST_PID,
        "title": f"[{TEST_PID}] Déclenchement disjoncteur général Transformateur HTA",
        "category": "Equipment",
        "severity": "Critical",
        "due_date": "2026-10-25",
        "status": "Open",
    })
    blocker.insert()
    frappe.db.commit()
    ok(f"Obstacle opérationnel créé: {blocker.name} (Statut: Open, Sévérité: Critical)")

    gis_data_alert = run_gis_query()
    entry_alert = gis_data_alert[TEST_PID]
    if entry_alert["marker_state"] != "ALERT 🔴" or len(entry_alert["active_blockers"]) != 1:
        print(f"  {RED}FAILED: Expected ALERT 🔴 with 1 blocker, got {entry_alert['marker_state']}{RESET}")
        sys.exit(1)
    ok(
        "Bascule dynamique temps réel : Marqueur ALERT 🔴 (Pulsing Red) activé",
        f"Obstacles actifs détectés: {len(entry_alert['active_blockers'])}"
    )

    # Test 2C: Close blocker via independent engineer verification → NOMINAL 🟢 state
    print(f"\n  [Action 2C] Résolution et clôture indépendante de l'obstacle...")
    # Step 1: Site team moves to In Progress
    frappe.set_user("chantier_01@uranos.local")
    b_doc = frappe.get_doc("URANOS Blocker", blocker.name)
    b_doc.status = "In Progress"
    with authorized_transition():
        b_doc.save()

    # Step 2: Site team submits resolution
    b_doc.status = "Pending Verification"
    b_doc.corrective_action = "Remplacement du relais différentiel et réarmement sécurisé"
    b_doc.resolved_by = "chantier_01@uranos.local"
    with authorized_transition():
        b_doc.save()

    # Step 3: Independent engineer verifies and closes
    frappe.set_user("ingenieur_01@uranos.local")
    b_doc_eng = frappe.get_doc("URANOS Blocker", blocker.name)
    b_doc_eng.status = "Closed"
    with authorized_transition():
        b_doc_eng.save()
    frappe.db.commit()
    ok(f"Obstacle {blocker.name} clôturé par vérificateur indépendant ({b_doc_eng.closed_by})")

    gis_data_resolved = run_gis_query()
    entry_resolved = gis_data_resolved[TEST_PID]
    if entry_resolved["marker_state"] != "NOMINAL 🟢" or len(entry_resolved["active_blockers"]) != 0:
        print(f"  {RED}FAILED: Expected NOMINAL 🟢 after closure, got {entry_resolved['marker_state']}{RESET}")
        sys.exit(1)
    ok(
        "Retour nominal temps réel : Marqueur repassé à NOMINAL 🟢 (Nominal Green)",
        "0 blocage actif restant"
    )

    # =========================================================================
    # PHASE 3: PROJECT COMPLETION & HISTORICAL ARCHIVING LIFECYCLE
    # =========================================================================
    step(3, "PROJECT COMPLETION & HISTORICAL ARCHIVING LIFECYCLE")

    # Test 3A: Transition Project to Completed/Closed → Auto-archive
    print(f"\n  [Action 3A] Déclenchement de la clôture du projet par le Manager (Passage à 'Completed')...")
    frappe.set_user("direction_01@uranos.local")
    proj_to_close = frappe.get_doc("Project", TEST_PID)
    proj_to_close.status = "Completed"
    proj_to_close.save()
    frappe.db.commit()

    # Verify Project.is_active is "No"
    updated_proj = frappe.get_doc("Project", TEST_PID)
    updated_prof = frappe.get_doc("URANOS Project Profile", prof_doc.name)

    if updated_proj.is_active != "No":
        print(f"  {RED}FAILED: Project.is_active expected 'No', got '{updated_proj.is_active}'{RESET}")
        sys.exit(1)
    ok("Projet basculé à is_active='No' (Chantier inactif opérationnellement)")

    if updated_prof.status != "Archived":
        print(f"  {RED}FAILED: URANOS Project Profile expected status 'Archived', got '{updated_prof.status}'{RESET}")
        sys.exit(1)
    ok(
        "Profil de projet synchronisé automatiquement au statut 'Archived' (Archives Historiques)",
        f"Profil: {updated_prof.name}, Statut: {updated_prof.status}"
    )

    # Test 3B: Engineer blocked from creating blocker on archived project
    print(f"\n  [Action 3B] Tentative de création d'un blocage sur projet archivé par l'Ingénieur...")
    frappe.set_user("ingenieur_01@uranos.local")
    try:
        illegal_blocker = frappe.get_doc({
            "doctype": "URANOS Blocker",
            "project": TEST_PID,
            "title": f"[{TEST_PID}] Tentative non autorisée d'ajout sur projet archivé",
            "category": "Equipment",
            "severity": "High",
            "status": "Open",
            "due_date": "2026-11-01",
        })
        illegal_blocker.insert()
        print(f"  {RED}FAILED: Engineer was able to create blocker on archived project!{RESET}")
        sys.exit(1)
    except frappe.PermissionError as pe:
        blocked(
            f"Création d'obstacle sur projet archivé '{TEST_PID}' formellement rejetée",
            "frappe.exceptions.PermissionError",
            str(pe)
        )
        ok("Verrouillage d'archive vérifié : les opérations de terrain sont interdites sur projets archivés")

    # Test 3C: Site Team blocked from modifying records on archived project
    print(f"\n  [Action 3C] Tentative de modification opérationnelle par l'Équipe Chantier sur projet archivé...")
    frappe.set_user("chantier_01@uranos.local")
    try:
        existing_blocker = frappe.get_doc("URANOS Blocker", blocker.name)
        existing_blocker.title = "[ALTÉRATION PROJET ARCHIVÉ]"
        existing_blocker.save()
        print(f"  {RED}FAILED: Site team was able to edit blocker on archived project!{RESET}")
        sys.exit(1)
    except frappe.PermissionError as pe:
        blocked(
            f"Altération d'obstacle sur projet archivé '{TEST_PID}' formellement rejetée",
            "frappe.exceptions.PermissionError",
            str(pe)
        )
        ok("Immuabilité de l'archive vérifiée : l'Équipe Chantier ne peut altérer les données historiques")

    # Test 3D: Manager maintains full read access to historical archives
    frappe.set_user("direction_01@uranos.local")
    print(f"\n  [Action 3D] Consultation des archives historiques par le Manager ({frappe.session.user})...")
    read_proj = frappe.get_doc("Project", TEST_PID)
    read_proj.check_permission("read")
    read_prof = frappe.get_doc("URANOS Project Profile", prof_doc.name)
    read_prof.check_permission("read")
    read_blocker = frappe.get_doc("URANOS Blocker", blocker.name)
    read_blocker.check_permission("read")
    ok(
        "Accès en lecture intégrale accordé au Manager sur les archives historiques",
        f"Lu Projet {read_proj.name}, Profil {read_prof.name} ({read_prof.status}), Obstacle {read_blocker.name}"
    )

    # Clean up test records
    frappe.set_user("Administrator")
    frappe.db.delete("URANOS Blocker", {"project": TEST_PID})
    frappe.db.delete("URANOS Project Profile", {"project": TEST_PID})
    frappe.db.delete("User Permission", {"allow": "Project", "for_value": TEST_PID})
    frappe.db.delete("Project", {"name": TEST_PID})
    frappe.db.commit()

    # Final summary banner
    header("RÉSULTAT DE LA VALIDATION : 100% SUCCÈS CONFORME AUX RÈGLES DE L'EXAMEN")
    print(f"""
{BOLD}{GREEN}✓ RÈGLE 1 (Création Projet) :{RESET} Seul le {BOLD}Manager{RESET} et l'Admin peuvent créer des projets.
                             Ingénieur et Chef de Chantier strictement bloqués avec PermissionError.
{BOLD}{GREEN}✓ RÈGLE 2 (GIS Dynamique)    :{RESET} Détection instantanée des coordonnées du site.
                             Bascule automatique {RED}ALERT 🔴{RESET} (si blocage actif) ➔ {GREEN}NOMINAL 🟢{RESET} (après clôture).
{BOLD}{GREEN}✓ RÈGLE 3 (Archivage Projet) :{RESET} Clôture automatique du projet en archive ({BOLD}status='Archived'{RESET}, is_active='No').
                             Verrouillage en lecture seule des opérations terrain (blocages figés).
                             Accès d'audit et reporting historique conservé pour le Manager.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
