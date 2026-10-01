import frappe

def run():
    frappe.init(site="uranos.localhost")
    frappe.connect()

    frappe.conf.developer_mode = 1
    frappe.flags.in_patch = True
    frappe.flags.in_import = True

    page_name = "blocker-kanban"
    page_title = "URANOS — Kanban Board"
    allowed_roles = [
        "URANOS Executive",
        "URANOS Project Manager",
        "URANOS Engineering Director",
        "Administrator",
        "System Manager"
    ]

    if frappe.db.exists("Page", page_name):
        doc = frappe.get_doc("Page", page_name)
        print(f"Updating existing Page '{page_name}'...")
    else:
        doc = frappe.new_doc("Page")
        doc.name = page_name
        doc.page_name = page_name
        print(f"Creating new Page '{page_name}'...")

    doc.title = page_title
    doc.module = "URANOS Project OS"
    doc.standard = "Yes"

    # Set roles
    doc.set("roles", [])
    for role in allowed_roles:
        doc.append("roles", {"role": role})

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    reloaded = frappe.get_doc("Page", page_name)
    print(f"✓ Page '{reloaded.name}' successfully configured!")
    print(f"  Title: {reloaded.title}")
    print(f"  Roles: {[r.role for r in reloaded.roles]}")

    # Verify permission for test users
    for user in ["direction_01@uranos.local", "ingenieur_01@uranos.local", "Administrator"]:
        frappe.set_user(user)
        print(f"  User {user} permitted: {bool(reloaded.is_permitted())}")

if __name__ == "__main__":
    run()
