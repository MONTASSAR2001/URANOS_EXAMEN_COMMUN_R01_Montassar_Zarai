import frappe
from datetime import datetime, timedelta

def run():
    frappe.init(site="uranos.localhost")
    frappe.connect()

    logs_data = [
        {
            "user": "ingenieur_01@uranos.local",
            "full_name": "Ingenieur 01",
            "subject": "Ingenieur 01 logged in",
            "operation": "Login",
            "status": "Success",
            "ip_address": "192.168.1.102",
            "communication_date": datetime(2026, 9, 30, 8, 15, 0),
        },
        {
            "user": "ingenieur_01@uranos.local",
            "full_name": "Ingenieur 01",
            "subject": "Ingenieur 01 logged out",
            "operation": "Logout",
            "status": "Success",
            "ip_address": "192.168.1.102",
            "communication_date": datetime(2026, 9, 30, 11, 30, 0),
        },
        {
            "user": "ingenieur_01@uranos.local",
            "full_name": "Ingenieur 01",
            "subject": "Ingenieur 01 logged in",
            "operation": "Login",
            "status": "Success",
            "ip_address": "192.168.1.102",
            "communication_date": datetime(2026, 9, 30, 11, 45, 0),
        },
        {
            "user": "chantier_01@uranos.local",
            "full_name": "Chantier 01",
            "subject": "Chantier 01 logged in",
            "operation": "Login",
            "status": "Success",
            "ip_address": "10.42.0.15",
            "communication_date": datetime(2026, 9, 30, 7, 5, 0),
        },
        {
            "user": "chantier_01@uranos.local",
            "full_name": "Chantier 01",
            "subject": "Chantier 01 logged out",
            "operation": "Logout",
            "status": "Success",
            "ip_address": "10.42.0.15",
            "communication_date": datetime(2026, 9, 30, 10, 20, 0),
        },
        {
            "user": "chantier_02@uranos.local",
            "full_name": "Chantier 02",
            "subject": "Failed login attempt for Chantier 02",
            "operation": "Login",
            "status": "Failed",
            "ip_address": "10.42.0.28",
            "communication_date": datetime(2026, 9, 30, 9, 12, 0),
        },
        {
            "user": "chantier_02@uranos.local",
            "full_name": "Chantier 02",
            "subject": "Chantier 02 logged in",
            "operation": "Login",
            "status": "Success",
            "ip_address": "10.42.0.28",
            "communication_date": datetime(2026, 9, 30, 9, 13, 30),
        },
        {
            "user": "ingenieur_03@uranos.local",
            "full_name": "Ingenieur 03",
            "subject": "Ingenieur 03 logged in",
            "operation": "Login",
            "status": "Success",
            "ip_address": "192.168.1.115",
            "communication_date": datetime(2026, 9, 30, 8, 45, 0),
        }
    ]

    for item in logs_data:
        # Check if identical record already exists
        exists = frappe.db.exists(
            "Activity Log",
            {
                "user": item["user"],
                "operation": item["operation"],
                "communication_date": item["communication_date"]
            }
        )
        if not exists:
            doc = frappe.get_doc({
                "doctype": "Activity Log",
                "owner": item["user"],
                "user": item["user"],
                "full_name": item["full_name"],
                "subject": item["subject"],
                "operation": item["operation"],
                "status": item["status"],
                "ip_address": item["ip_address"],
                "communication_date": item["communication_date"],
            })
            doc.insert(ignore_permissions=True)
            print(f"Created Activity Log: {item['subject']} ({item['status']})")
        else:
            print(f"Already exists: {item['subject']}")

    frappe.db.commit()
    print("Successfully seeded Activity Logs.")

if __name__ == "__main__":
    run()
