#!/usr/bin/env python3
"""
Seed script to create real support issues, sales invoices, and purchase invoices
for URANOS Project OS.
"""
import frappe
from frappe.utils import today, add_days

def run():
    frappe.set_user("Administrator")
    print("--- 1. Ensuring Company Accounts & Currency ---")
    comp = frappe.get_doc("Company", "URANOS Group")
    comp.reporting_currency = "USD"
    comp.stock_received_but_not_billed = "Stock Received But Not Billed - UG"
    comp.stock_adjustment_account = "Stock Adjustment - UG"
    comp.save()
    frappe.db.commit()
    print("Company configured with reporting_currency and stock defaults.")

    print("--- 2. Ensuring IT Issues ---")
    existing_issues = frappe.get_all("Issue", fields=["name", "subject"])
    if not existing_issues:
        issue1 = frappe.new_doc("Issue")
        issue1.subject = "Substation SCADA Gateway Telemetry Link Intermittent Failure"
        issue1.status = "Open"
        issue1.priority = "High"
        issue1.description = "Loss of real-time telemetry packets from MV Inverter Substation 02 to central SCADA dispatch."
        issue1.raised_by = "direction_01@uranos.local"
        issue1.insert(ignore_permissions=True)

        issue2 = frappe.new_doc("Issue")
        issue2.subject = "Drone Photogrammetry Orthophoto Alignment Error on Sector 4"
        issue2.status = "Open"
        issue2.priority = "Medium"
        issue2.description = "RTK base station coordinate offset resulted in 12cm drift in orthomosaic tile rendering."
        issue2.raised_by = "direction_01@uranos.local"
        issue2.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Created 2 real Issues: {issue1.name}, {issue2.name}")
    else:
        print(f"Issues already exist: {len(existing_issues)}")

    print("--- 3. Creating & Submitting Real Sales Invoice ---")
    existing_sinv = frappe.get_all("Sales Invoice", fields=["name", "docstatus"])
    if not existing_sinv:
        si = frappe.new_doc("Sales Invoice")
        si.company = "URANOS Group"
        si.customer = "Sonelgaz Renewable Energy SPA"
        si.posting_date = today()
        si.due_date = add_days(today(), 30)
        si.currency = "USD"
        si.append("items", {
            "item_code": "SOLAR-PANEL-500W",
            "qty": 400,
            "rate": 275.0,
            "income_account": "Sales - UG",
            "cost_center": "Main - UG"
        })
        si.append("items", {
            "item_code": "INVERTER-STRING-100KW",
            "qty": 10,
            "rate": 11700.0,
            "income_account": "Sales - UG",
            "cost_center": "Main - UG"
        })
        si.insert(ignore_permissions=True)
        si.submit()
        frappe.db.commit()
        print(f"Created and submitted Sales Invoice: {si.name}, Grand Total: {si.grand_total}")
    else:
        print(f"Sales Invoices already exist: {len(existing_sinv)}")

    print("--- 4. Creating & Submitting Real Purchase Invoice ---")
    existing_pinv = frappe.get_all("Purchase Invoice", fields=["name", "docstatus"])
    if not existing_pinv:
        pi = frappe.new_doc("Purchase Invoice")
        pi.company = "URANOS Group"
        pi.supplier = "Tier-1 Solar Manufacturing Ltd"
        pi.posting_date = today()
        pi.due_date = add_days(today(), 45)
        pi.currency = "USD"
        pi.append("items", {
            "item_code": "CABLE-COPPER-50MM",
            "qty": 5000,
            "rate": 14.50,
            "expense_account": "Cost of Goods Sold - UG",
            "cost_center": "Main - UG"
        })
        pi.append("items", {
            "item_code": "TRANSFORMER-OIL-DRUM",
            "qty": 20,
            "rate": 800.00,
            "expense_account": "Cost of Goods Sold - UG",
            "cost_center": "Main - UG"
        })
        pi.insert(ignore_permissions=True)
        pi.submit()
        frappe.db.commit()
        print(f"Created and submitted Purchase Invoice: {pi.name}, Grand Total: {pi.grand_total}")
    else:
        print(f"Purchase Invoices already exist: {len(existing_pinv)}")

    print("--- 5. Verification Summary ---")
    print(f"Issues in DB: {frappe.db.count('Issue')}")
    print(f"Blockers in DB: {frappe.db.count('URANOS Blocker')}")
    print(f"Sales Invoices in DB: {frappe.db.count('Sales Invoice')}")
    print(f"Purchase Invoices in DB: {frappe.db.count('Purchase Invoice')}")

if __name__ == "__main__":
    frappe.init(site="uranos.localhost")
    frappe.connect()
    run()
