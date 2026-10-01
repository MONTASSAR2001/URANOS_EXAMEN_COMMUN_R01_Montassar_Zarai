import frappe
from frappe.utils import now_datetime, today
from uranos_project_os.controllers import authorized_transition

def seed():
    frappe.init(site="uranos.localhost")
    frappe.connect()

    print("=== SEEDING OPERATIONAL DAILY DATA (2026-10-01) ===")
    
    # Grant ingenieur_01@uranos.local the Site Controller role and User Permissions
    user_doc = frappe.get_doc("User", "ingenieur_01@uranos.local")
    roles = [r.role for r in user_doc.roles]
    if "URANOS Site Controller" not in roles:
        user_doc.add_roles("URANOS Site Controller")
        print("Added URANOS Site Controller to ingenieur_01")

    for proj in ["PV-0004", "PV-0005", "PV-0017"]:
        if not frappe.db.exists("User Permission", {"user": "ingenieur_01@uranos.local", "allow": "Project", "for_value": proj}):
            up = frappe.get_doc({
                "doctype": "User Permission",
                "user": "ingenieur_01@uranos.local",
                "allow": "Project",
                "for_value": proj,
                "apply_to_all_doctypes": 1
            })
            up.insert(ignore_permissions=True)
            print(f"Granted Project {proj} to ingenieur_01")

    # 1. Update Blockers with realistic site reporters and engineer responsibles
    blocker_updates = {
        "B-00001": {
            "reported_by": "chantier_01@uranos.local",
            "responsible": "ingenieur_01@uranos.local",
            "opened_at": "2026-10-01 07:30:00",
            "severity": "Critical",
            "status": "In Progress",
            "description": "Validation raccordement poste haute tension STEG 225kV en cours avec la direction de distribution STEG Kairouan."
        },
        "B-00002": {
            "reported_by": "chantier_01@uranos.local",
            "responsible": "ingenieur_01@uranos.local",
            "opened_at": "2026-10-01 08:15:00",
            "severity": "High",
            "status": "In Progress",
            "description": "Contrôle aléatoire révélant un couple de serrage insuffisant sur 15% des axes trackers solaires."
        },
        "B-00003": {
            "reported_by": "chantier_01@uranos.local",
            "responsible": "ingenieur_01@uranos.local",
            "opened_at": "2026-10-01 09:00:00",
            "severity": "High",
            "status": "Open",
            "description": "Blocage douanier temporaire au port de Radès sur les conteneurs d'onduleurs centraux Sungrow."
        }
    }
    for b_id, vals in blocker_updates.items():
        if frappe.db.exists("URANOS Blocker", b_id):
            frappe.db.set_value("URANOS Blocker", b_id, vals, update_modified=False)
            print(f"Updated blocker {b_id}")

    # 2. Seed URANOS Work Packages
    work_packages = [
        {
            "code": "WP-0004-CIVIL",
            "project": "PV-0004",
            "title": "Génie Civil & Plateformes Onduleurs",
            "discipline": "Civil",
            "uom": "Nos",
            "qty_planned": 100.0,
            "weight": 25.0,
            "baseline_version": "BL-001",
            "status": "Completed"
        },
        {
            "code": "WP-0004-STRUC",
            "project": "PV-0004",
            "title": "Montage Structures Trackers 1P",
            "discipline": "Mechanical",
            "uom": "Nos",
            "qty_planned": 120.0,
            "weight": 35.0,
            "baseline_version": "BL-001",
            "status": "Completed"
        },
        {
            "code": "WP-0004-ELEC",
            "project": "PV-0004",
            "title": "Raccordement Poste Évacuation HT 225kV",
            "discipline": "Electrical",
            "uom": "Nos",
            "qty_planned": 50.0,
            "weight": 40.0,
            "baseline_version": "BL-001",
            "status": "Blocked"
        },
        {
            "code": "WP-0005-TRACK",
            "project": "PV-0005",
            "title": "Calibration & Serrage Trackers Solaires",
            "discipline": "Mechanical",
            "uom": "Nos",
            "qty_planned": 60.0,
            "weight": 30.0,
            "baseline_version": "BL-001",
            "status": "In Progress"
        },
        {
            "code": "WP-0017-VRD",
            "project": "PV-0017",
            "title": "Réception VRD et Caniveaux Câbles DC",
            "discipline": "Civil",
            "uom": "Nos",
            "qty_planned": 80.0,
            "weight": 20.0,
            "baseline_version": "BL-001",
            "status": "Completed"
        }
    ]

    wp_map = {}
    with authorized_transition():
        for wp_data in work_packages:
            code = wp_data["code"]
            existing = frappe.db.get_value("URANOS Work Package", {"code": code}, "name")
            if not existing:
                doc = frappe.get_doc({
                    "doctype": "URANOS Work Package",
                    **wp_data
                })
                doc.flags.ignore_mandatory = True
                doc.insert(ignore_permissions=True)
                wp_map[code] = doc.name
                print(f"Created Work Package: {code} -> {doc.name}")
            else:
                frappe.db.set_value("URANOS Work Package", existing, wp_data)
                wp_map[code] = existing
                print(f"Updated Work Package: {code} -> {existing}")

        # 3. Seed URANOS Field Progress Entries (Today 2026-10-01)
        progress_entries = [
            {
                "project": "PV-0004",
                "wp_code": "WP-0004-CIVIL",
                "activity": "Coulage massifs béton & plateformes onduleurs",
                "zone": "Zone A - Nord",
                "crew": "Équipe Génie Civil 01",
                "posting_date": "2026-10-01",
                "qty_reported": 100.0,
                "qty_verified": 100.0,
                "baseline_version": "BL-001",
                "reported_by": "chantier_01@uranos.local",
                "verifier": "ingenieur_01@uranos.local",
                "verified_at": "2026-10-01 11:00:00",
                "status": "Verified",
                "notes": "Validation complète des résistances d'éprouvettes à 28 jours."
            },
            {
                "project": "PV-0004",
                "wp_code": "WP-0004-STRUC",
                "activity": "Pose modules bifaciaux et vérification inclinaison",
                "zone": "Zone B - Est",
                "crew": "Équipe Montage Trackers 02",
                "posting_date": "2026-10-01",
                "qty_reported": 120.0,
                "qty_verified": 120.0,
                "baseline_version": "BL-001",
                "reported_by": "chantier_01@uranos.local",
                "verifier": "ingenieur_01@uranos.local",
                "verified_at": "2026-10-01 14:30:00",
                "status": "Verified",
                "notes": "Contrôle de planéité et serrage au couple étalonné conforme."
            },
            {
                "project": "PV-0017",
                "wp_code": "WP-0017-VRD",
                "activity": "Contrôle remblaiement tranchées et caniveaux VRD",
                "zone": "Zone Postes MT",
                "crew": "Équipe VRD Menzel Bourguiba",
                "posting_date": "2026-10-01",
                "qty_reported": 80.0,
                "qty_verified": 80.0,
                "baseline_version": "BL-001",
                "reported_by": "chantier_01@uranos.local",
                "verifier": "ingenieur_01@uranos.local",
                "verified_at": "2026-10-01 16:00:00",
                "status": "Verified",
                "notes": "Plan de récolement et compactage validés sans réserve."
            }
        ]

        for fpe_data in progress_entries:
            wp_code = fpe_data.pop("wp_code")
            wp_doc_name = wp_map.get(wp_code)
            if not wp_doc_name:
                continue

            existing_fpe = frappe.db.get_value(
                "URANOS Field Progress Entry",
                {"project": fpe_data["project"], "activity": fpe_data["activity"], "posting_date": fpe_data["posting_date"]},
                "name"
            )

            entry_dict = {
                "doctype": "URANOS Field Progress Entry",
                "work_package": wp_doc_name,
                **fpe_data
            }

            if not existing_fpe:
                doc = frappe.get_doc(entry_dict)
                doc.flags.ignore_mandatory = True
                doc.insert(ignore_permissions=True)
                print(f"Created Field Progress Entry for {wp_code}: {doc.name}")
            else:
                frappe.db.set_value("URANOS Field Progress Entry", existing_fpe, entry_dict)
                print(f"Updated Field Progress Entry for {wp_code}: {existing_fpe}")

    frappe.db.commit()
    print("=== SEEDING COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    seed()
