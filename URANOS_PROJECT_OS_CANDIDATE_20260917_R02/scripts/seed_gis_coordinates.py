#!/usr/bin/env python3
"""
seed_gis_coordinates.py — Seed realistic Tunisian coordinates for all 20 URANOS solar projects.
Creates Custom Fields `latitude` and `longitude` on Project and URANOS Project Profile if they do not exist.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

PROJECT_COORDINATES = {
    "PV-01": {"lat": 32.9297, "lon": 10.4518, "governorate": "Tataouine", "site": "Centrale Solaire PV-01 (Tataouine)"},
    "PV-02": {"lat": 33.9197, "lon": 8.1335,  "governorate": "Tozeur",    "site": "Centrale Solaire PV-02 (Tozeur)"},
    "PV-03": {"lat": 33.7050, "lon": 8.9690,  "governorate": "Kebili",    "site": "Centrale Solaire PV-03 (Kebili)"},
    "PV-04": {"lat": 33.3549, "lon": 10.5055, "governorate": "Medenine",  "site": "Centrale Solaire PV-04 (Medenine)"},
    "PV-05": {"lat": 34.4250, "lon": 8.7842,  "governorate": "Gafsa",     "site": "Centrale Solaire PV-05 (Gafsa)"},
    "PV-06": {"lat": 35.0382, "lon": 9.4849,  "governorate": "Sidi Bouzid","site": "Centrale Solaire PV-06 (Sidi Bouzid)"},
    "PV-07": {"lat": 35.1676, "lon": 8.8365,  "governorate": "Kasserine", "site": "Centrale Solaire PV-07 (Kasserine)"},
    "PV-08": {"lat": 35.6781, "lon": 10.0963, "governorate": "Kairouan",  "site": "Centrale Solaire PV-08 (Kairouan)"},
    "PV-09": {"lat": 36.4029, "lon": 10.1429, "governorate": "Zaghouan",  "site": "Centrale Solaire PV-09 (Zaghouan)"},
    "PV-10": {"lat": 34.7406, "lon": 10.7603, "governorate": "Sfax",      "site": "Centrale Solaire PV-10 (Sfax)"},
    "PV-11": {"lat": 32.3167, "lon": 10.4000, "governorate": "Tataouine", "site": "Centrale Solaire PV-11 (Remada)"},
    "PV-12": {"lat": 33.8731, "lon": 7.8778,  "governorate": "Tozeur",    "site": "Centrale Solaire PV-12 (Nefta)"},
    "PV-13": {"lat": 33.4663, "lon": 9.0203,  "governorate": "Kebili",    "site": "Centrale Solaire PV-13 (Douz)"},
    "PV-14": {"lat": 33.1389, "lon": 11.2167, "governorate": "Medenine",  "site": "Centrale Solaire PV-14 (Zarzis)"},
    "PV-15": {"lat": 34.3208, "lon": 8.4017,  "governorate": "Gafsa",     "site": "Centrale Solaire PV-15 (Metlaoui)"},
    "PV-16": {"lat": 34.8594, "lon": 9.7847,  "governorate": "Sidi Bouzid","site": "Centrale Solaire PV-16 (Regueb)"},
    "PV-17": {"lat": 35.2289, "lon": 9.1294,  "governorate": "Kasserine", "site": "Centrale Solaire PV-17 (Sbeitla)"},
    "PV-18": {"lat": 35.9333, "lon": 10.0167, "governorate": "Kairouan",  "site": "Centrale Solaire PV-18 (Sbikha)"},
    "PV-19": {"lat": 36.3744, "lon": 9.9056,  "governorate": "Zaghouan",  "site": "Centrale Solaire PV-19 (El Fahs)"},
    "PV-20": {"lat": 34.5358, "lon": 10.5019, "governorate": "Sfax",      "site": "Centrale Solaire PV-20 (Mahres)"},
}

def seed():
    print("1. Checking & Creating Custom Fields for Coordinates...")
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
        ],
        "URANOS Project Profile": [
            {
                "fieldname": "latitude",
                "label": "Latitude",
                "fieldtype": "Float",
                "insert_after": "governorate",
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
        ],
    }

    create_custom_fields(custom_fields, update=True)
    frappe.clear_cache(doctype="Project")
    if frappe.db.exists("DocType", "URANOS Project Profile"):
        frappe.clear_cache(doctype="URANOS Project Profile")
    print("✓ Custom Fields verified / created.")

    print("\n2. Seeding coordinates on Project records...")
    for proj_id, coords in PROJECT_COORDINATES.items():
        if frappe.db.exists("Project", proj_id):
            frappe.db.set_value("Project", proj_id, {
                "latitude": coords["lat"],
                "longitude": coords["lon"],
            }, update_modified=False)
            print(f"  ✓ Project {proj_id} -> Lat: {coords['lat']}, Lon: {coords['lon']}")

    print("\n3. Seeding coordinates on URANOS Project Profile records...")
    for proj_id, coords in PROJECT_COORDINATES.items():
        profiles = frappe.get_all("URANOS Project Profile", filters={"project": proj_id}, fields=["name"])
        for prof in profiles:
            frappe.db.set_value("URANOS Project Profile", prof["name"], {
                "latitude": coords["lat"],
                "longitude": coords["lon"],
            }, update_modified=False)
            print(f"  ✓ Profile {prof['name']} ({proj_id}) -> Lat: {coords['lat']}, Lon: {coords['lon']}")

    frappe.db.commit()
    print("\n✓ All coordinates committed to MariaDB successfully!")

if __name__ == "__main__":
    frappe.init(site="uranos.localhost")
    frappe.connect()
    seed()
