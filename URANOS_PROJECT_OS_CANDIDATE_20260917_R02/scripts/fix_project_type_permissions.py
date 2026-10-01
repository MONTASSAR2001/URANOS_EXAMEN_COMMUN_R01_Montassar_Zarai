#!/usr/bin/env python3
"""Programmatically configure Custom DocPerm for Project Type DocType.

Grants read: 1 to management, URANOS Executive, Desk User, engineer, site_team, and All.
Grants write: 1, create: 1 to management and URANOS Executive.
"""

import frappe

def fix_project_type_permissions():
    frappe.init(site="uranos.localhost")
    frappe.connect()

    print("Configuring Custom DocPerm for 'Project Type'...")

    roles_perms = [
        {"role": "management", "read": 1, "write": 1, "create": 1, "delete": 0},
        {"role": "URANOS Executive", "read": 1, "write": 1, "create": 1, "delete": 0},
        {"role": "Desk User", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"role": "engineer", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"role": "site_team", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"role": "All", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"role": "Projects Manager", "read": 1, "write": 1, "create": 1, "delete": 0},
        {"role": "Projects User", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 0},
    ]

    doctype = "Project Type"
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
    print("✓ Project Type permissions successfully configured in MariaDB!")

if __name__ == "__main__":
    fix_project_type_permissions()
