#!/usr/bin/env python3
"""
URANOS Project OS — Production Environment Wipe & Tunisian Fleet Seeding
1. Complete wipe of fake/test Project and linked records.
2. Configuration of Project Naming Series to 'PV-.####'.
3. Explicit RBAC docperm configuration for engineer, site_team, and management.
4. Programmatic seeding of 20 realistic Tunisian Photovoltaic projects with exact coordinates.
5. Generation of realistic URANOS Blockers with 4-step workflow.
"""

import sys
from decimal import Decimal
import frappe
from uranos_project_os.controllers import authorized_transition

TUNISIAN_PROJECTS = [
    {
        "project_name": "Centrale Solaire Tozeur I (10 MW)",
        "governorate": "Tozeur",
        "latitude": 33.9197,
        "longitude": 8.1336,
        "capacity_mw": 10.0,
        "status": "Completed",
        "percent_complete": 100.0,
    },
    {
        "project_name": "Centrale Solaire Tozeur II (10 MW)",
        "governorate": "Tozeur",
        "latitude": 33.9250,
        "longitude": 8.1450,
        "capacity_mw": 10.0,
        "status": "Open",
        "percent_complete": 85.0,
    },
    {
        "project_name": "Parc Photovoltaïque Tataouine - Dharfa (10 MW)",
        "governorate": "Tataouine",
        "latitude": 32.9297,
        "longitude": 10.4518,
        "capacity_mw": 10.0,
        "status": "Completed",
        "percent_complete": 100.0,
    },
    {
        "project_name": "Centrale Solaire Metbassta - Kairouan (100 MW)",
        "governorate": "Kairouan",
        "latitude": 35.6781,
        "longitude": 10.0963,
        "capacity_mw": 100.0,
        "status": "Open",
        "percent_complete": 62.0,
    },
    {
        "project_name": "Centrale Solaire Gafsa - Segdoud (120 MW)",
        "governorate": "Gafsa",
        "latitude": 34.4250,
        "longitude": 8.7842,
        "capacity_mw": 120.0,
        "status": "Open",
        "percent_complete": 45.0,
    },
    {
        "project_name": "Centrale Solaire Sidi Bouzid - Scadd (50 MW)",
        "governorate": "Sidi Bouzid",
        "latitude": 35.0382,
        "longitude": 9.4858,
        "capacity_mw": 50.0,
        "status": "Open",
        "percent_complete": 78.0,
    },
    {
        "project_name": "Centrale Solaire Borj Bourguiba (200 MW)",
        "governorate": "Tataouine",
        "latitude": 32.2500,
        "longitude": 9.9800,
        "capacity_mw": 200.0,
        "status": "Open",
        "percent_complete": 30.0,
    },
    {
        "project_name": "Parc Solaire Medenine - Ben Guerdane (10 MW)",
        "governorate": "Médenine",
        "latitude": 33.1389,
        "longitude": 11.2167,
        "capacity_mw": 10.0,
        "status": "Open",
        "percent_complete": 90.0,
    },
    {
        "project_name": "Centrale PV Gabès - Ghannouch (15 MW)",
        "governorate": "Gabès",
        "latitude": 33.9333,
        "longitude": 10.0667,
        "capacity_mw": 15.0,
        "status": "Open",
        "percent_complete": 55.0,
    },
    {
        "project_name": "Centrale Solaire Kasserine - Feriana (10 MW)",
        "governorate": "Kasserine",
        "latitude": 34.9500,
        "longitude": 8.5667,
        "capacity_mw": 10.0,
        "status": "Open",
        "percent_complete": 40.0,
    },
    {
        "project_name": "Centrale Solaire Kebili - Douz (10 MW)",
        "governorate": "Kébili",
        "latitude": 33.4667,
        "longitude": 9.0167,
        "capacity_mw": 10.0,
        "status": "Completed",
        "percent_complete": 100.0,
    },
    {
        "project_name": "Parc Solaire Sfax - Thyna (12 MW)",
        "governorate": "Sfax",
        "latitude": 34.6500,
        "longitude": 10.6667,
        "capacity_mw": 12.0,
        "status": "Open",
        "percent_complete": 70.0,
    },
    {
        "project_name": "Centrale PV Mahdia - El Jem (10 MW)",
        "governorate": "Mahdia",
        "latitude": 35.3000,
        "longitude": 10.7167,
        "capacity_mw": 10.0,
        "status": "Open",
        "percent_complete": 65.0,
    },
    {
        "project_name": "Centrale Solaire Siliana - Gaâfour (10 MW)",
        "governorate": "Siliana",
        "latitude": 36.3200,
        "longitude": 9.3200,
        "capacity_mw": 10.0,
        "status": "Open",
        "percent_complete": 50.0,
    },
    {
        "project_name": "Centrale PV Béja - Medjez El Bab (10 MW)",
        "governorate": "Béja",
        "latitude": 36.6500,
        "longitude": 9.6167,
        "capacity_mw": 10.0,
        "status": "Open",
        "percent_complete": 80.0,
    },
    {
        "project_name": "Parc Solaire Jendouba - Oued Mliz (10 MW)",
        "governorate": "Jendouba",
        "latitude": 36.4667,
        "longitude": 8.5500,
        "capacity_mw": 10.0,
        "status": "Open",
        "percent_complete": 25.0,
    },
    {
        "project_name": "Centrale PV Bizerte - Menzel Bourguiba (15 MW)",
        "governorate": "Bizerte",
        "latitude": 37.1550,
        "longitude": 9.7926,
        "capacity_mw": 15.0,
        "status": "Open",
        "percent_complete": 95.0,
    },
    {
        "project_name": "Centrale Solaire Nabeul - Grombalia (10 MW)",
        "governorate": "Nabeul",
        "latitude": 36.6000,
        "longitude": 10.5000,
        "capacity_mw": 10.0,
        "status": "Completed",
        "percent_complete": 100.0,
    },
    {
        "project_name": "Centrale Solaire Zaghouan - Zriba (10 MW)",
        "governorate": "Zaghouan",
        "latitude": 36.3667,
        "longitude": 10.2500,
        "capacity_mw": 10.0,
        "status": "Open",
        "percent_complete": 75.0,
    },
    {
        "project_name": "Centrale PV Monastir - Sahline (10 MW)",
        "governorate": "Monastir",
        "latitude": 35.7500,
        "longitude": 10.7167,
        "capacity_mw": 10.0,
        "status": "Open",
        "percent_complete": 60.0,
    },
]


def wipe_data():
    print("--- 1. Purging Test / Fake Data ---")
    tables = [
        "tabURANOS Blocker",
        "tabURANOS Daily Site Report",
        "tabURANOS Field Progress Entry",
        "tabURANOS Work Package",
        "tabURANOS Baseline",
        "tabURANOS Project Profile",
        "tabProject",
    ]
    for tbl in tables:
        count = frappe.db.sql(f"SELECT COUNT(*) FROM `{tbl}`")[0][0]
        frappe.db.sql(f"DELETE FROM `{tbl}`")
        print(f"  • Cleared {tbl}: {count} records removed")

    # Clear orphaned project User Permissions
    up_cnt = frappe.db.sql("SELECT COUNT(*) FROM `tabUser Permission` WHERE allow='Project'")[0][0]
    frappe.db.sql("DELETE FROM `tabUser Permission` WHERE allow='Project'")
    print(f"  • Cleared tabUser Permission (allow='Project'): {up_cnt} records removed")

    # Clear User Settings for Project list view
    if frappe.db.table_exists("__UserSettings"):
        frappe.db.sql("DELETE FROM `__UserSettings` WHERE doctype='Project'")
        print("  • Cleared __UserSettings for 'Project'")

    # Reset series counters
    frappe.db.sql("DELETE FROM `tabSeries` WHERE name IN ('PV-', 'PROJ-', 'B-')")
    print("  • Reset tabSeries for 'PV-', 'PROJ-', and 'B-' to 0")
    frappe.db.commit()


def setup_naming_series():
    print("\n--- 2. Configuring Clean Naming Series 'PV-.####' for Project ---")
    # Update tabDocField
    frappe.db.sql("""
        UPDATE `tabDocField`
        SET options = 'PV-.####', `default` = 'PV-.####'
        WHERE parent = 'Project' AND fieldname = 'naming_series'
    """)

    # Ensure Property Setter exists
    ps_options_name = "Project-naming_series-options"
    if not frappe.db.exists("Property Setter", ps_options_name):
        ps_opt = frappe.get_doc({
            "doctype": "Property Setter",
            "name": ps_options_name,
            "doc_type": "Project",
            "doctype_or_field": "DocField",
            "field_name": "naming_series",
            "property": "options",
            "property_type": "Text",
            "value": "PV-.####",
        })
        ps_opt.insert(ignore_permissions=True)
    else:
        frappe.db.set_value("Property Setter", ps_options_name, "value", "PV-.####")

    ps_default_name = "Project-naming_series-default"
    if not frappe.db.exists("Property Setter", ps_default_name):
        ps_def = frappe.get_doc({
            "doctype": "Property Setter",
            "name": ps_default_name,
            "doc_type": "Project",
            "doctype_or_field": "DocField",
            "field_name": "naming_series",
            "property": "default_value",
            "property_type": "Text",
            "value": "PV-.####",
        })
        ps_def.insert(ignore_permissions=True)
    else:
        frappe.db.set_value("Property Setter", ps_default_name, "value", "PV-.####")

    frappe.db.commit()
    print("  ✓ Project naming_series set to 'PV-.####' (options & default)")


def configure_rbac_permissions():
    print("\n--- 3. Configuring RBAC Permissions for Project, Profile & Project Type Doctypes ---")
    roles_perms = [
        {"role": "management", "read": 1, "write": 1, "create": 1, "delete": 0},
        {"role": "URANOS Executive", "read": 1, "write": 1, "create": 1, "delete": 0},
        {"role": "Desk User", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"role": "engineer", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"role": "site_team", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"role": "All", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"role": "URANOS Engineering Director", "read": 1, "write": 1, "create": 0, "delete": 0},
        {"role": "URANOS Project Manager", "read": 1, "write": 1, "create": 0, "delete": 0},
        {"role": "URANOS Site Controller", "read": 1, "write": 0, "create": 0, "delete": 0},
    ]

    for doctype in ["Project", "URANOS Project Profile", "Project Type"]:
        for rp in roles_perms:
            role = rp["role"]
            existing = frappe.db.get_value("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}, "name")
            if existing:
                frappe.db.set_value("Custom DocPerm", existing, {
                    "read": rp["read"],
                    "write": rp["write"],
                    "create": rp["create"],
                    "delete": rp["delete"],
                })
                print(f"  • Updated Custom DocPerm for {doctype} - '{role}': read={rp['read']}, create={rp['create']}")
            else:
                docperm = frappe.get_doc({
                    "doctype": "Custom DocPerm",
                    "parent": doctype,
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": role,
                    "permlevel": 0,
                    "read": rp["read"],
                    "write": rp["write"],
                    "create": rp["create"],
                    "delete": rp["delete"],
                })
                docperm.insert(ignore_permissions=True)
                print(f"  • Inserted Custom DocPerm for {doctype} - '{role}': read={rp['read']}, create={rp['create']}")

    frappe.db.commit()


def ensure_custom_fields():
    print("\n--- 1b. Ensuring Custom Fields for Project ---")
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    custom_fields = {
        "Project": [
            {
                "fieldname": "latitude",
                "label": "Latitude",
                "fieldtype": "Float",
                "insert_after": "status",
                "read_only": 0,
                "in_list_view": 1,
            },
            {
                "fieldname": "longitude",
                "label": "Longitude",
                "fieldtype": "Float",
                "insert_after": "latitude",
                "read_only": 0,
                "in_list_view": 1,
            },
            {
                "fieldname": "custom_assigned_engineer",
                "label": "Assigned Engineer",
                "fieldtype": "Link",
                "options": "User",
                "insert_after": "longitude",
                "read_only": 0,
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "custom_assigned_site_team",
                "label": "Assigned Site Team",
                "fieldtype": "Link",
                "options": "User",
                "insert_after": "custom_assigned_engineer",
                "read_only": 0,
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
        ],
    }
    create_custom_fields(custom_fields, update=True)
    frappe.clear_cache(doctype="Project")
    print("  ✓ Custom Fields verified / created on Project.")


def seed_projects():
    print("\n--- 4. Programmatically Seeding 20 Realistic Tunisian Solar Projects ---")
    company = "URANOS Group" if frappe.db.exists("Company", "URANOS Group") else None
    created_projects = []

    for idx, pinfo in enumerate(TUNISIAN_PROJECTS, start=1):
        mw = pinfo["capacity_mw"]
        is_active = "No" if pinfo["status"] == "Completed" else "Yes"
        
        # Exact assignment requirements:
        # ingenieur_01@uranos.local -> exactly 3 projects (indices 4, 5, 17: PV-0004, PV-0005, PV-0017)
        # chantier_01@uranos.local  -> exactly 1 project  (index 4: PV-0004)
        assigned_engineer = None
        assigned_site_team = None
        if idx in (4, 5, 17):
            assigned_engineer = "ingenieur_01@uranos.local"
        if idx == 4:
            assigned_site_team = "chantier_01@uranos.local"

        proj = frappe.get_doc({
            "doctype": "Project",
            "naming_series": "PV-.####",
            "project_name": pinfo["project_name"],
            "status": pinfo["status"],
            "is_active": is_active,
            "percent_complete": pinfo["percent_complete"],
            "percent_complete_method": "Task Completion",
            "company": company,
            "latitude": pinfo["latitude"],
            "longitude": pinfo["longitude"],
            "custom_assigned_engineer": assigned_engineer,
            "custom_assigned_site_team": assigned_site_team,
        })
        proj.flags.ignore_permissions = True
        proj.flags.ignore_mandatory = True
        with authorized_transition():
            proj.insert(ignore_permissions=True)
        frappe.db.commit()

        # Create or update URANOS Project Profile
        prof_name = frappe.db.get_value("URANOS Project Profile", {"project": proj.name})
        if not prof_name:
            prof = frappe.get_doc({
                "doctype": "URANOS Project Profile",
                "project": proj.name,
                "short_code": proj.name,
                "site": pinfo["project_name"],
                "governorate": pinfo["governorate"],
                "capacity_ac_mw": mw,
                "capacity_dc_mwp": float(Decimal(str(mw)) * Decimal("1.20")),
                "status": "Archived" if pinfo["status"] == "Completed" else "Active",
                "latitude": pinfo["latitude"],
                "longitude": pinfo["longitude"],
                "risk_level": "Low" if pinfo["percent_complete"] > 70 else "Medium",
            })
            prof.flags.ignore_permissions = True
            with authorized_transition():
                prof.insert(ignore_permissions=True)
        else:
            frappe.db.set_value("URANOS Project Profile", prof_name, {
                "site": pinfo["project_name"],
                "governorate": pinfo["governorate"],
                "capacity_ac_mw": mw,
                "capacity_dc_mwp": float(Decimal(str(mw)) * Decimal("1.20")),
                "status": "Archived" if pinfo["status"] == "Completed" else "Active",
                "latitude": pinfo["latitude"],
                "longitude": pinfo["longitude"],
            })
        frappe.db.commit()

        created_projects.append(proj)
        print(f"  [{idx:02d}/20] Created {proj.name} — '{pinfo['project_name']}' ({pinfo['governorate']}) | {mw} MW | {pinfo['status']} ({pinfo['percent_complete']}%)")

    return created_projects


def seed_realistic_blockers(projects):
    print("\n--- 5. Seeding Realistic Operational Blockers for Fleet Map Telemetry ---")
    # Add a few blockers on active projects to populate the map markers and KPIs
    blocker_specs = [
        {
            "proj_idx": 3,  # Metbassta - Kairouan 100MW (PV-0004)
            "title": "Validation raccordement poste haute tension STEG 225kV",
            "category": "Administration",
            "severity": "Critical",
            "status": "Open",
            "due_date": "2026-10-20",
            "responsible": "ingenieur_01@uranos.local",
        },
        {
            "proj_idx": 4,  # Gafsa - Segdoud 120MW (PV-0005)
            "title": "Anomalie couple de serrage structures trackers solaires bifaciaux",
            "category": "Equipment",
            "severity": "High",
            "status": "In Progress",
            "due_date": "2026-10-15",
            "responsible": "ingenieur_01@uranos.local",
        },
        {
            "proj_idx": 5,  # Sidi Bouzid 50MW (PV-0006)
            "title": "Retard dédouanement onduleurs centraux 3.125 MVA au port de Radès",
            "category": "Logistics",
            "severity": "High",
            "status": "Open",
            "due_date": "2026-10-10",
            "responsible": "ingenieur_03@uranos.local",
        },
        {
            "proj_idx": 6,  # Borj Bourguiba 200MW (PV-0007)
            "title": "Attente rapport étude géotechnique complémentaire sol meuble",
            "category": "Equipment",
            "severity": "Medium",
            "status": "In Progress",
            "due_date": "2026-10-25",
            "responsible": "ingenieur_01@uranos.local",
        },
        {
            "proj_idx": 8,  # Gabès 15MW (PV-0009)
            "title": "Contrôle qualité thermographie et sertissage connecteurs MC4",
            "category": "Quality",
            "severity": "Medium",
            "status": "Pending Verification",
            "due_date": "2026-10-05",
            "responsible": "ingenieur_01@uranos.local",
        },
        {
            "proj_idx": 16,  # Bizerte 15MW (PV-0017)
            "title": "Validation plan de récolement et conformité VRD",
            "category": "Document",
            "severity": "Low",
            "status": "Closed",
            "due_date": "2026-09-28",
            "responsible": "ingenieur_01@uranos.local",
        },
    ]

    for bspec in blocker_specs:
        target_proj = projects[bspec["proj_idx"]]
        blocker = frappe.get_doc({
            "doctype": "URANOS Blocker",
            "project": target_proj.name,
            "title": f"[{target_proj.name}] {bspec['title']}",
            "category": bspec["category"],
            "severity": bspec["severity"],
            "due_date": bspec["due_date"],
            "responsible": bspec["responsible"],
            "status": "Open",
        })
        blocker.flags.ignore_permissions = True
        with authorized_transition():
            blocker.insert(ignore_permissions=True)
        frappe.db.commit()

        if bspec["status"] in ("In Progress", "Pending Verification", "Closed"):
            blocker.status = "In Progress"
            with authorized_transition():
                blocker.save(ignore_permissions=True)
            frappe.db.commit()

        if bspec["status"] in ("Pending Verification", "Closed"):
            blocker.status = "Pending Verification"
            blocker.corrective_action = f"Action corrective validée sur le site {target_proj.project_name}."
            blocker.resolved_by = bspec["responsible"]
            with authorized_transition():
                blocker.save(ignore_permissions=True)
            frappe.db.commit()

        if bspec["status"] == "Closed":
            blocker.status = "Closed"
            blocker.closed_by = "ingenieur_03@uranos.local"
            with authorized_transition():
                blocker.save(ignore_permissions=True)
            frappe.db.commit()

        print(f"  • Created Blocker {blocker.name} on {target_proj.name} ({target_proj.project_name}) -> Status: {blocker.status}")


def main():
    print("=" * 80)
    print("   URANOS PROJECT OS — PRODUCTION ENVIRONMENT WIPE & SEEDING")
    print("=" * 80)

    frappe.init("uranos.localhost")
    frappe.connect()

    wipe_data()
    ensure_custom_fields()
    setup_naming_series()
    configure_rbac_permissions()
    projects = seed_projects()
    seed_realistic_blockers(projects)

    print("\n" + "=" * 80)
    print(f"SUCCESS: 20 Tunisian Solar Projects seeded with sequential PV-0001..PV-0020 IDs!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
