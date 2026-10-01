import frappe

def grant_access():
    if not frappe.db:
        frappe.init(site="uranos.localhost")
        frappe.connect()

    target_email = "direction_01@uranos.local"
    if frappe.db.exists("User", target_email):
        user = frappe.get_doc("User", target_email)
        roles = [r.role for r in user.roles]
        if "System Manager" not in roles:
            user.append("roles", {"role": "System Manager"})
            user.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"Granted 'System Manager' role to {target_email}")
        else:
            print(f"{target_email} already has 'System Manager' role")

    # Grant read permissions on Page DocType for Executive & Desk User
    for role in ["URANOS Executive", "Desk User", "System Manager"]:
        if not frappe.db.exists("Role", role):
            continue
        existing = frappe.db.exists("Custom DocPerm", {"parent": "Page", "role": role, "permlevel": 0})
        if not existing:
            perm = frappe.new_doc("Custom DocPerm")
            perm.parent = "Page"
            perm.parenttype = "DocType"
            perm.parentfield = "permissions"
            perm.role = role
            perm.permlevel = 0
            perm.read = 1
            perm.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"Granted Page read permission to role '{role}'")
        else:
            print(f"Role '{role}' already has Custom DocPerm on Page")

    frappe.clear_cache(user=target_email)
    frappe.clear_cache()
    print("Permissions successfully updated and cache cleared.")

if __name__ == "__main__":
    grant_access()
