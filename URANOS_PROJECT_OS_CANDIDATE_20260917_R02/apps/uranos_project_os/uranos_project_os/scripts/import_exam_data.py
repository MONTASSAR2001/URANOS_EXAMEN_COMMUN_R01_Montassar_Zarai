#!/usr/bin/env python3
"""URANOS Project OS — Exam Mock Data Importer & Seeder.

Imports official exam mock data from DONNEES_FICTIVES.json:
- 20 Solar PV Projects (PV-01 to PV-20) + URANOS Project Profiles
- 4 Demo Users with explicit Project User Permissions and URANOS business roles
- 5 Sample Issues (B-001 to B-005) matching exact statuses and severities
- 18 Additional rich solar PV blocker scenarios across projects, using the
  official service layer APIs (assign_blocker, submit_resolution, close_blocker)
  to generate complete audit history, satisfying the Golden Rule.

Usage:
    bench --site <site> execute uranos_project_os.scripts.import_exam_data.execute
    OR
    python3 apps/uranos_project_os/uranos_project_os/scripts/import_exam_data.py --site uranos.local
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import frappe
    from uranos_project_os.controllers import authorized_transition
    from uranos_project_os.services.blockers import (
        assign_blocker,
        close_blocker,
        submit_resolution,
    )
except ImportError:
    frappe = None  # Handled for standalone / dry-run execution


CATEGORY_MAP = {
    "studies": "Document",
    "document": "Document",
    "supply": "Material",
    "material": "Material",
    "logistics": "Logistics",
    "civil": "Access",
    "access": "Access",
    "electrical": "Equipment",
    "equipment": "Equipment",
    "assembly": "Quality",
    "quality": "Quality",
    "safety": "Safety",
    "weather": "Weather",
    "crew": "Crew",
    "administration": "Administration",
    "client": "Client Decision",
}

SEVERITY_MAP = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
}

ROLE_MAP = {
    "site_team": ["URANOS Site Controller", "URANOS Team Lead"],
    "engineer": ["URANOS Engineering Director", "URANOS Project Manager"],
    "management": ["URANOS Executive", "URANOS Project Manager", "Accounts User", "Accounts Manager", "Support Team"],
}

DEMO_PASSWORD = "Password123!"


def locate_data_file(explicit_path: Optional[str] = None) -> Path:
    """Find DONNEES_FICTIVES.json across potential workspace / exam directory locations."""
    if explicit_path and os.path.exists(explicit_path):
        return Path(explicit_path).resolve()

    candidates = [
        Path.cwd() / "DONNEES_FICTIVES.json",
        Path(__file__).resolve().parents[4] / "DONNEES_FICTIVES.json",
        Path(__file__).resolve().parents[5] / "DONNEES_FICTIVES.json",
        Path("/home/montassar/Desktop/llm/URANOS_EXAMEN_COMMUN_R01_Montassar_Zarai/DONNEES_FICTIVES.json"),
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    # Search upwards from current file
    cur = Path(__file__).resolve().parent
    for _ in range(6):
        target = cur / "DONNEES_FICTIVES.json"
        if target.is_file():
            return target
        cur = cur.parent

    raise FileNotFoundError(
        "DONNEES_FICTIVES.json not found. Please provide path via --file <path>."
    )


def load_data(file_path: Path) -> Dict[str, Any]:
    """Parse and validate DONNEES_FICTIVES.json."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded exam data from: {file_path}")
    print(f"  - Projects in file: {len(data.get('projects', []))}")
    print(f"  - Demo users in file: {len(data.get('demo_users', []))}")
    print(f"  - Sample issues in file: {len(data.get('sample_issues', []))}")
    return data


def ensure_roles():
    """Ensure standard URANOS business roles exist in Frappe."""
    from uranos_project_os.setup import ROLES
    for name in ROLES:
        role_name = "URANOS " + name
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }).insert(ignore_permissions=True)


def seed_projects(projects_data: List[Dict[str, Any]]) -> List[str]:
    """Insert or update the 20 official exam projects (PV-01 to PV-20)."""
    print("\n--- Seeding 20 Projects (PV-01 to PV-20) ---")
    created_projects = []

    # Ensure in_import is active so custom project IDs like PV-01 are preserved
    if hasattr(frappe, "flags"):
        frappe.flags.in_import = True

    # Get default company if available
    default_company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not default_company:
        companies = frappe.get_all("Company", limit=1)
        default_company = companies[0].name if companies else None

    governorates = [
        "Tataouine", "Tozeur", "Kebili", "Medenine", "Gafsa",
        "Sidi Bouzid", "Kasserine", "Kairouan", "Zaghouan", "Sfax",
    ]

    for idx, p in enumerate(projects_data):
        pid = p["id"]
        capacity_mw = p.get("capacity_mw", 1)
        gov = governorates[idx % len(governorates)]

        # 1. Project DocType
        actual_project_id = pid
        if not frappe.db.exists("Project", pid):
            existing_by_name = frappe.db.get_value("Project", {"project_name": pid}, "name")
            if existing_by_name:
                actual_project_id = existing_by_name
                print(f"  [.] Existing Project: {actual_project_id} (found by project_name '{pid}')")
            else:
                proj_data = {
                    "doctype": "Project",
                    "project_name": pid,
                    "status": "Open",
                    "is_active": "Yes",
                }
                if default_company:
                    proj_data["company"] = default_company

                proj = frappe.get_doc(proj_data)
                proj.name = pid
                proj.flags.ignore_permissions = True
                proj.flags.ignore_mandatory = True
                proj.insert(ignore_permissions=True)
                actual_project_id = proj.name
                print(f"  [+] Created Project: {actual_project_id} ({capacity_mw} MW)")
        else:
            actual_project_id = pid
            print(f"  [.] Existing Project: {pid}")

        # 2. URANOS Project Profile
        profile_exists = frappe.db.exists("URANOS Project Profile", {"project": actual_project_id})
        if not profile_exists:
            profile = frappe.get_doc({
                "doctype": "URANOS Project Profile",
                "project": actual_project_id,
                "short_code": pid,
                "site": f"Centrale Solaire {pid}",
                "governorate": gov,
                "capacity_ac_mw": capacity_mw,
                "capacity_dc_mwp": float(Decimal(str(capacity_mw)) * Decimal("1.20")),
                "status": "In Progress",
                "risk_level": "Medium",
            })
            profile.flags.ignore_permissions = True
            profile.flags.ignore_mandatory = True
            with authorized_transition():
                profile.insert(ignore_permissions=True)
            print(f"      - Created URANOS Project Profile for {actual_project_id} ({gov})")

        created_projects.append(actual_project_id)

    return created_projects


def grant_project_permission(email: str, project_ref: str):
    """Ensure user has project access for service transition execution."""
    if not email or email == "Administrator":
        return
    proj_name = (
        frappe.db.get_value("Project", project_ref, "name")
        or frappe.db.get_value("Project", {"project_name": project_ref}, "name")
        or project_ref
    )
    if not frappe.db.exists("User Permission", {"user": email, "allow": "Project", "for_value": proj_name}):
        perm = frappe.get_doc({
            "doctype": "User Permission",
            "user": email,
            "allow": "Project",
            "for_value": proj_name,
            "apply_to_all_doctypes": 1,
        })
        perm.flags.ignore_permissions = True
        perm.insert(ignore_permissions=True)


def seed_users(users_data: List[Dict[str, Any]], all_project_ids: List[str]) -> Dict[str, str]:
    """Insert the demo users and configure project permissions & roles."""
    print("\n--- Seeding Demo Users & Project Grants ---")
    user_email_map: Dict[str, str] = {}

    # Supplement with ingenieur_03 referenced by sample issue B-005
    all_users = list(users_data)
    if not any(u["id"] == "ingenieur_03" for u in all_users):
        all_users.append({
            "id": "ingenieur_03",
            "role": "engineer",
            "projects": ["PV-03"],
        })

    for u in all_users:
        uid = u["id"]
        role_type = u["role"]
        roles_to_assign = ROLE_MAP.get(role_type, ["URANOS Site Controller"])
        email = f"{uid}@uranos.local"
        user_email_map[uid] = email

        first_name = "Manager" if "direction" in uid.lower() else uid.replace("_", " ").title()
        if not frappe.db.exists("User", email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "username": uid,
                "send_welcome_email": 0,
                "enabled": 1,
                "roles": [{"role": r} for r in roles_to_assign],
            })
            user.flags.ignore_permissions = True
            user.insert(ignore_permissions=True)

            try:
                from frappe.utils.password import update_password
                update_password(email, DEMO_PASSWORD)
            except Exception:
                pass

            print(f"  [+] Created User: {email} (Roles: {', '.join(roles_to_assign)})")
        else:
            user = frappe.get_doc("User", email)
            existing_roles = {r.role for r in user.roles}
            changed = False
            if "direction" in email.lower() and (user.first_name != "Manager" or user.full_name != "Manager"):
                user.first_name = "Manager"
                user.last_name = ""
                user.full_name = "Manager"
                changed = True
            for r in roles_to_assign:
                if r not in existing_roles:
                    user.append("roles", {"role": r})
                    changed = True
            if changed:
                user.save(ignore_permissions=True)
            print(f"  [.] Existing User: {email}")

        # Explicit Project User Permissions (fail-closed isolation)
        assigned_projects = u.get("projects")
        target_projects = all_project_ids if assigned_projects == "all" else (assigned_projects or [])

        for pid in target_projects:
            grant_project_permission(email, pid)
        print(f"      - Granted {len(target_projects)} project(s) access to {email}")

    return user_email_map


def seed_sample_issues(sample_issues: List[Dict[str, Any]], user_email_map: Dict[str, str]):
    """Insert the 5 exact sample issues from DONNEES_FICTIVES.json."""
    print("\n--- Seeding 5 Official Sample Issues (B-001 to B-005) ---")

    for item in sample_issues:
        iid = item["id"]
        project_ref = item["project"]
        project = (
            frappe.db.get_value("Project", project_ref, "name")
            or frappe.db.get_value("Project", {"project_name": project_ref}, "name")
            or project_ref
        )
        title = item["title"]
        category = CATEGORY_MAP.get(item.get("category", "supply"), "Material")
        severity = SEVERITY_MAP.get(item.get("severity", "low"), "Low")
        due_date = item.get("due_date")
        target_status = item.get("status", "Open")
        resp_id = item.get("responsible")
        responsible = user_email_map.get(resp_id) if resp_id else None

        if frappe.db.exists("URANOS Blocker", iid):
            print(f"  [.] Blocker {iid} already exists. Skipping.")
            continue

        # Initial Document Creation (always starts as Open)
        frappe.set_user("Administrator")
        doc_data = {
            "doctype": "URANOS Blocker",
            "name": iid,
            "project": project,
            "title": f"[{iid}] {title}",
            "category": category,
            "severity": severity,
            "status": "Open",
            "opened_at": frappe.utils.now(),
            "reported_by": "Administrator",
            "lost_hours": 0.0,
            "description": f"Enregistrement officiel de l'examen URANOS ({iid}).",
        }
        if due_date:
            doc_data["target_resolution"] = f"{due_date} 18:00:00"

        doc = frappe.get_doc(doc_data)
        doc.flags.ignore_permissions = True
        doc.flags.ignore_mandatory = True
        with authorized_transition():
            doc.insert(ignore_permissions=True)

        print(f"  [+] Created Blocker: {iid} in {project} [{category} / {severity}]")

        # Execute Service Layer Transitions to reach target_status
        if target_status == "In Progress":
            if not responsible:
                responsible = user_email_map.get("ingenieur_01", "Administrator")
            grant_project_permission(responsible, project)
            assign_blocker(
                name=iid,
                responsible=responsible,
                justification=f"Affectation officielle de résolution de l'obstacle {iid}.",
            )
            print(f"      -> Assigned to {responsible} (Status: In Progress)")

        elif target_status == "Pending Verification":
            resp = responsible or user_email_map.get("chantier_02", "Administrator")
            grant_project_permission(resp, project)
            assign_blocker(
                name=iid,
                responsible=resp,
                justification=f"Affectation pour correction immédiate {iid}.",
            )
            frappe.set_user(resp)
            submit_resolution(
                name=iid,
                corrective_action="Correction technique appliquée sur site et contrôlée contradictoirement.",
            )
            frappe.set_user("Administrator")
            print(f"      -> Resolved by {resp} (Status: Pending Verification)")

        elif target_status == "Closed":
            resp = responsible or user_email_map.get("ingenieur_03", "Administrator")
            closer = user_email_map.get("direction_01", "Administrator")
            if closer == resp:
                closer = user_email_map.get("chantier_01", "Administrator")

            grant_project_permission(resp, project)
            grant_project_permission(closer, project)
            assign_blocker(
                name=iid,
                responsible=resp,
                justification=f"Affectation pour clôture d'action fictive {iid}.",
            )
            frappe.set_user(resp)
            submit_resolution(
                name=iid,
                corrective_action="Action corrective finalisée avec succès selon le plan de contrôle.",
            )
            frappe.set_user(closer)
            close_blocker(
                name=iid,
                review_reason="Vérification indépendante effectuée. Clôture validée selon la Règle d'Or.",
            )
            frappe.set_user("Administrator")
            print(f"      -> Closed by {closer} (Golden Rule verified, Status: Closed)")


def seed_extra_blockers(all_project_ids: List[str], user_email_map: Dict[str, str]):
    """Generate 18 rich solar PV blocker scenarios across projects.

    Populates complete audit history and demonstrates the full 4-stage lifecycle:
    Open, In Progress, Pending Verification, Closed.
    """
    print("\n--- Seeding 18 Additional Realistic Scenarios (B-006 to B-023) ---")

    extra_scenarios = [
        # In Progress scenarios
        {
            "id": "B-006", "project": "PV-04",
            "title": "Retard livraison onduleurs centraux 1500V",
            "category": "Material", "severity": "Critical", "lost_hours": 14.5,
            "target": "In Progress", "assignee": "ingenieur_01",
            "justification": "Coordination logistique urgente auprès du transitaire portuaire.",
        },
        {
            "id": "B-008", "project": "PV-06",
            "title": "Infiltration d'eau dans caniveaux techniques DC",
            "category": "Weather", "severity": "Medium", "lost_hours": 4.0,
            "target": "Open", "assignee": None, "justification": "",
        },
        {
            "id": "B-009", "project": "PV-07",
            "title": "Indisponibilité nacelle élévatrice certifiée",
            "category": "Equipment", "severity": "Medium", "lost_hours": 6.0,
            "target": "In Progress", "assignee": "chantier_01",
            "justification": "Contrat de location express passé avec loueur local.",
        },
        {
            "id": "B-010", "project": "PV-08",
            "title": "Attente validation plan de raccordement STEG",
            "category": "Document", "severity": "Critical", "lost_hours": 24.0,
            "target": "In Progress", "assignee": "direction_01",
            "justification": "Relance formelle en commission mixte d'interconnexion réseau.",
        },
        {
            "id": "B-013", "project": "PV-11",
            "title": "Manque d'électriciens habilités B2V / BR sur site",
            "category": "Crew", "severity": "High", "lost_hours": 16.0,
            "target": "In Progress", "assignee": "chantier_02",
            "justification": "Dépêchement d'une brigade mobile de sous-traitance qualifiée.",
        },
        {
            "id": "B-015", "project": "PV-13",
            "title": "Défaut d'isolement sur boîte de jonction SMB-03",
            "category": "Equipment", "severity": "Critical", "lost_hours": 18.0,
            "target": "In Progress", "assignee": "ingenieur_01",
            "justification": "Campagne de mesure réflectométrique et caméra thermique engagée.",
        },
        {
            "id": "B-017", "project": "PV-15",
            "title": "Blocage douanier conteneurs de structures trackers",
            "category": "Logistics", "severity": "Critical", "lost_hours": 32.0,
            "target": "In Progress", "assignee": "direction_01",
            "justification": "Fourniture du certificat d'origine visé par la chambre de commerce.",
        },
        {
            "id": "B-020", "project": "PV-18",
            "title": "Piste d'accès dégradée après passage engins lourds",
            "category": "Access", "severity": "Low", "lost_hours": 2.0,
            "target": "Open", "assignee": None, "justification": "",
        },
        {
            "id": "B-022", "project": "PV-20",
            "title": "Certificat d'étalonnage soudeuse optique manquant",
            "category": "Administration", "severity": "Low", "lost_hours": 1.5,
            "target": "In Progress", "assignee": "chantier_02",
            "justification": "Récupération du certificat auprès du laboratoire métrologique.",
        },
        # Pending Verification scenarios
        {
            "id": "B-012", "project": "PV-10",
            "title": "Rupture de stock connecteurs solaires MC4 6mm²",
            "category": "Material", "severity": "High", "lost_hours": 9.5,
            "target": "Pending Verification", "assignee": "chantier_01",
            "justification": "Commande express de 500 paires de connecteurs auprès du stock tampon.",
            "action": "500 connecteurs réceptionnés au magasin chantier et certifiés conformes.",
        },
        {
            "id": "B-018", "project": "PV-16",
            "title": "Remarque bureau de contrôle sur note de calcul vent",
            "category": "Document", "severity": "High", "lost_hours": 10.0,
            "target": "Pending Verification", "assignee": "ingenieur_01",
            "justification": "Reprise de la simulation éléments finis sur logiciel de calcul.",
            "action": "Note R2 émise intégrant les surpressions aérodynamiques locales.",
        },
        {
            "id": "B-023", "project": "PV-01",
            "title": "Microfissures constatées sur 4 modules au déchargement",
            "category": "Quality", "severity": "High", "lost_hours": 8.0,
            "target": "Pending Verification", "assignee": "chantier_01",
            "justification": "Inspection visuelle et électroluminescence sur lot arrivant.",
            "action": "Mise en quarantaine des 4 panneaux et remplacement par stock de réserve.",
        },
        # Closed scenarios (Strictly enforcing Golden Rule: closer != resolver)
        {
            "id": "B-007", "project": "PV-05",
            "title": "Nivellement plateforme hors tolérances (+/- 5cm)",
            "category": "Quality", "severity": "High", "lost_hours": 8.0,
            "target": "Closed", "assignee": "chantier_01", "closer": "direction_01",
            "justification": "Affectation au topographe pour recalage au laser.",
            "action": "Reprise du régalage à la niveleuse guidée GPS et compactage validé.",
            "review": "Contrôle contradictoire topographique n°14 effectué sans réserve.",
        },
        {
            "id": "B-011", "project": "PV-09",
            "title": "Absence de balisage de sécurité zone poste HT",
            "category": "Safety", "severity": "Critical", "lost_hours": 12.0,
            "target": "Closed", "assignee": "chantier_02", "closer": "ingenieur_01",
            "justification": "Mise en sécurité immédiate du périmètre haute tension.",
            "action": "Pose d'une clôture rigide 2m avec panneaux danger de mort et cadenas consigne.",
            "review": "Audit HSE validé le jour même. Accès strictement consigné.",
        },
        {
            "id": "B-014", "project": "PV-12",
            "title": "Accès piste Nord bloqué par travaux tiers",
            "category": "Access", "severity": "High", "lost_hours": 5.5,
            "target": "Closed", "assignee": "ingenieur_01", "closer": "direction_01",
            "justification": "Médiation avec les autorités régionales et le chef de chantier tiers.",
            "action": "Création d'une déviation stabilisée et dégagement de la voie principale.",
            "review": "Constat d'huissier levé et circulation des convois rétablie.",
        },
        {
            "id": "B-016", "project": "PV-14",
            "title": "Couple de serrage non conforme sur pieux battus",
            "category": "Quality", "severity": "Medium", "lost_hours": 7.0,
            "target": "Closed", "assignee": "chantier_02", "closer": "chantier_01",
            "justification": "Contrôle qualité systématique à la clé dynamométrique étalonnée.",
            "action": "Resserrage des 120 boulons d'ancrage au couple nominal de 180 N.m.",
            "review": "Fiche d'autocontrôle QA n°52 contresignée par le contrôleur qualité.",
        },
        {
            "id": "B-019", "project": "PV-17",
            "title": "Alerte canicule (> 45°C) : suspension travaux après-midi",
            "category": "Weather", "severity": "Low", "lost_hours": 3.5,
            "target": "Closed", "assignee": "chantier_01", "closer": "direction_01",
            "justification": "Application de la directive sécurité spéciale météo extrême.",
            "action": "Horaires décalés de 05h00 à 11h00 avec distribution d'eau réfrigérée.",
            "review": "Aucun incident thermique à déplorer. Reprise en cadence nominale.",
        },
        {
            "id": "B-021", "project": "PV-19",
            "title": "Inversion de polarité repérée sur string PV n°14",
            "category": "Equipment", "severity": "Medium", "lost_hours": 4.5,
            "target": "Closed", "assignee": "chantier_02", "closer": "ingenieur_01",
            "justification": "Recherche par voltmètre sur l'armoire de regroupement.",
            "action": "Rebranchement des connecteurs polarisés et vérification Voc = 920V.",
            "review": "Mesure électrique confirmée conforme avant raccordement onduleur.",
        },
    ]

    for item in extra_scenarios:
        iid = item["id"]
        project_ref = item["project"]
        project = (
            frappe.db.get_value("Project", project_ref, "name")
            or frappe.db.get_value("Project", {"project_name": project_ref}, "name")
            or project_ref
        )
        title = item["title"]
        category = item["category"]
        severity = item["severity"]
        lost_hours = float(item["lost_hours"])
        target_status = item["target"]

        if frappe.db.exists("URANOS Blocker", iid):
            print(f"  [.] Blocker {iid} already exists. Skipping.")
            continue

        frappe.set_user("Administrator")
        doc_data = {
            "doctype": "URANOS Blocker",
            "name": iid,
            "project": project,
            "title": f"[{iid}] {title}",
            "category": category,
            "severity": severity,
            "status": "Open",
            "opened_at": frappe.utils.now(),
            "reported_by": "Administrator",
            "lost_hours": lost_hours,
            "target_resolution": frappe.utils.add_days(frappe.utils.now(), 5),
            "description": f"Incident opérationnel photovoltaïque documenté pour la centrale {project}.",
        }

        doc = frappe.get_doc(doc_data)
        doc.flags.ignore_permissions = True
        doc.flags.ignore_mandatory = True
        with authorized_transition():
            doc.insert(ignore_permissions=True)

        print(f"  [+] Created Blocker {iid} [{severity}] in {project}")

        assignee_key = item.get("assignee")
        assignee_email = user_email_map.get(assignee_key) if assignee_key else None

        if target_status == "In Progress" and assignee_email:
            grant_project_permission(assignee_email, project)
            assign_blocker(
                name=iid,
                responsible=assignee_email,
                justification=item.get("justification", "Affectation pour résolution."),
            )
            print(f"      -> Assigned to {assignee_email}")

        elif target_status == "Pending Verification" and assignee_email:
            grant_project_permission(assignee_email, project)
            assign_blocker(
                name=iid,
                responsible=assignee_email,
                justification=item.get("justification", "Affectation pour résolution."),
            )
            frappe.set_user(assignee_email)
            submit_resolution(
                name=iid,
                corrective_action=item.get("action", "Action corrective complétée."),
            )
            frappe.set_user("Administrator")
            print(f"      -> Resolved by {assignee_email} (Pending Verification)")

        elif target_status == "Closed" and assignee_email:
            closer_key = item.get("closer", "direction_01")
            closer_email = user_email_map.get(closer_key, "direction_01@uranos.local")

            # Enforce Golden Rule
            if closer_email == assignee_email:
                closer_email = "direction_01@uranos.local" if assignee_email != "direction_01@uranos.local" else "ingenieur_01@uranos.local"

            grant_project_permission(assignee_email, project)
            grant_project_permission(closer_email, project)

            assign_blocker(
                name=iid,
                responsible=assignee_email,
                justification=item.get("justification", "Affectation pour résolution."),
            )
            frappe.set_user(assignee_email)
            submit_resolution(
                name=iid,
                corrective_action=item.get("action", "Action corrective exécutée."),
            )
            frappe.set_user(closer_email)
            close_blocker(
                name=iid,
                review_reason=item.get("review", "Vérification indépendante validée selon la Règle d'Or."),
            )
            frappe.set_user("Administrator")
            print(f"      -> Closed by {closer_email} (Golden Rule verified)")


def execute(file_path: Optional[str] = None):
    """Main execution entry point for bench execute."""
    if frappe is None:
        raise RuntimeError("Frappe framework must be loaded in the python environment.")

    frappe.set_user("Administrator")
    frappe.flags.in_import = True
    print("=" * 70)
    print("URANOS PROJECT OS — EXAM DATA IMPORTER & SEEDER")
    print("=" * 70)

    # 1. Locate and read DONNEES_FICTIVES.json
    data_file = locate_data_file(file_path)
    data = load_data(data_file)

    # 2. Ensure roles exist
    ensure_roles()

    # 3. Seed 20 Projects
    project_ids = seed_projects(data.get("projects", []))

    # 4. Seed Demo Users & Grants
    user_map = seed_users(data.get("demo_users", []), project_ids)

    # 5. Seed 5 Sample Issues
    seed_sample_issues(data.get("sample_issues", []), user_map)

    # 6. Seed 18 Extra Rich Scenarios
    seed_extra_blockers(project_ids, user_map)

    # Commit transaction
    frappe.db.commit()

    # Display final metrics
    total_proj = frappe.db.count("Project")
    total_blockers = frappe.db.count("URANOS Blocker")
    active_blockers = frappe.db.count("URANOS Blocker", {"status": ["!=", "Closed"]})
    closed_blockers = frappe.db.count("URANOS Blocker", {"status": "Closed"})

    print("\n" + "=" * 70)
    print("IMPORT COMPLETE & COMMITTED SUCCESSFULLY")
    print(f"  - Total Projects:        {total_proj}")
    print(f"  - Total URANOS Blockers: {total_blockers}")
    print(f"  - Active Blockers:       {active_blockers} (Open, In Progress, Pending)")
    print(f"  - Closed Blockers:       {closed_blockers} (Verified under Golden Rule)")
    print("=" * 70)


def main():
    """CLI handler with site and file argument support."""
    parser = argparse.ArgumentParser(description="URANOS Exam Data Importer & Seeder")
    parser.add_argument("--site", help="Frappe site name to connect to", default=None)
    parser.add_argument("--file", help="Path to DONNEES_FICTIVES.json", default=None)
    args = parser.parse_args()

    if frappe and args.site:
        frappe.init(site=args.site)
        frappe.connect()

    execute(file_path=args.file)

    if frappe and args.site:
        frappe.destroy()


if __name__ == "__main__":
    main()
