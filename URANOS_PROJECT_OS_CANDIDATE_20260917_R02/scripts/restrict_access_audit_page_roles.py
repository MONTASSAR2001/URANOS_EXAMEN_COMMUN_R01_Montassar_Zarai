import frappe

def run():
    frappe.init(site="uranos.localhost")
    frappe.connect()

    frappe.flags.in_patch = True

    # 1. Fetch Page access-audit
    doc = frappe.get_doc("Page", "access-audit")
    print("Previous roles in DB:", [r.role for r in doc.roles])

    # 2. Clear all existing roles
    doc.set("roles", [])

    # 3. Add strictly allowed roles
    allowed_roles = ["URANOS Executive", "System Manager", "Administrator"]
    for role in allowed_roles:
        doc.append("roles", {"role": role})

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # 4. Verify in DB
    reloaded = frappe.get_doc("Page", "access-audit")
    print("Updated roles in DB:", [r.role for r in reloaded.roles])

    # 5. Check is_permitted for test users
    frappe.set_user("direction_01@uranos.local")
    print("direction_01 permitted:", bool(reloaded.is_permitted()))

    frappe.set_user("ingenieur_01@uranos.local")
    print("ingenieur_01 permitted:", bool(reloaded.is_permitted()))

    frappe.set_user("chantier_01@uranos.local")
    print("chantier_01 permitted:", bool(reloaded.is_permitted()))

if __name__ == "__main__":
    run()
