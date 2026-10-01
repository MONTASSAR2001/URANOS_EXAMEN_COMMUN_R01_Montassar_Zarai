"""Derived in-app alerts only: no email, carrier calls or stock transactions.

The scheduler's technical context can compute facts, never approve business
actions. Outstanding material in WIP is not labelled a confirmed physical loss.
"""
from hashlib import sha256

import frappe

from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.services.common import require_post, scoped_doc


def _maintain(project, doctype, name, rule, message, *, severity="High", open_risk=True):
    identity = sha256((project + "\0" + doctype + "\0" + name + "\0" + rule).encode()).hexdigest()
    exists = frappe.db.exists("URANOS Executive Alert", identity)
    if not exists and not open_risk:
        return
    with authorized_transition():
        doc = frappe.get_doc("URANOS Executive Alert", identity) if exists else frappe.get_doc({
            "doctype": "URANOS Executive Alert", "name": identity, "project": project,
            "rule": rule, "reference_doctype": doctype, "reference_name": name,
            "status": "Open", "generated_at": frappe.utils.now()})
        doc.message, doc.severity = message, severity
        if not open_risk:
            doc.status = "Resolved"
        elif doc.status == "Resolved":
            doc.status, doc.acknowledged = "Open", 0
        if exists:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True, set_name=identity)


def _project(project):
    frappe.db.sql("SELECT name FROM `tabProject` WHERE name=%s FOR UPDATE", (project,))
    today = frappe.utils.getdate()
    for row in frappe.get_all("URANOS NCR", filters={"project": project},
            fields=["name", "status", "severity", "due_date"], limit_page_length=0):
        urgent = row.status != "Closed" and (row.severity == "Critical" or
            (row.severity == "High" and row.due_date and frappe.utils.getdate(row.due_date) < today))
        _maintain(project, "URANOS NCR", row.name, "quality_blocker", "Critical or overdue high-severity NCR requires review",
                  severity="Critical", open_risk=bool(urgent))
    for row in frappe.get_all("URANOS Blocker", filters={"project": project},
            fields=["name", "status", "severity"], limit_page_length=0):
        _maintain(project, "URANOS Blocker", row.name, "critical_blocker", "Critical project blocker remains open",
                  severity="Critical", open_risk=row.severity == "Critical" and row.status not in {"Resolved", "Closed"})
    for row in frappe.get_all("URANOS Kit Issue", filters={"project": project},
            fields=["name", "status", "kit_template"], limit_page_length=0):
        high_risk = frappe.db.exists("URANOS Kit Item", {"parent": row.kit_template, "risk_class": ["in", ["R3", "R4"]]})
        open_issue = row.status in {"Issued", "Partially Used", "Variance Review", "Reconciled"}
        _maintain(project, "URANOS Kit Issue", row.name, "daily_high_risk_reconciliation_due",
            "R3/R4 daily reconciliation is required; outstanding WIP is not yet a confirmed loss",
            open_risk=bool(high_risk and open_issue))
    for row in frappe.get_all("URANOS Shipment", filters={"project": project},
            fields=["name", "status", "eta_initial", "eta_revised", "delay_alert_days", "need_by", "criticality"], limit_page_length=0):
        active = row.status not in {"Site Received", "Closed"}
        eta = row.eta_revised or row.eta_initial
        late = bool(eta and row.eta_initial and row.delay_alert_days is not None and
            (frappe.utils.getdate(eta) - frappe.utils.getdate(row.eta_initial)).days >= row.delay_alert_days and
            frappe.utils.getdate(eta) > frappe.utils.getdate(row.eta_initial))
        late_need = bool(row.need_by and eta and frappe.utils.getdate(eta) > frappe.utils.getdate(row.need_by))
        _maintain(project, "URANOS Shipment", row.name, "shipment_eta_review", "Shipment ETA risks the configured need date or delay limit",
            severity="Critical" if row.criticality == "Critical" else "High", open_risk=active and (late or late_need))


def refresh_alerts():
    """Hourly scheduler entry point, intentionally NOT whitelisted."""
    for row in frappe.get_all("Project", fields=["name"], limit_page_length=0):
        frappe.db.savepoint("uranos_alert_project")
        try:
            if frappe.db.exists("URANOS Project Profile", {"project": row.name}):
                _project(row.name)
        except Exception:
            frappe.db.rollback(save_point="uranos_alert_project")
            frappe.log_error(title="URANOS derived alert evaluation failed", message=frappe.get_traceback())
            raise  # let native scheduler monitoring expose failed evaluation


@frappe.whitelist(methods=["POST"])
def acknowledge(name):
    require_post()
    security.require_roles("Executive", "Engineering Director", "Project Manager", "Site Controller")
    doc = scoped_doc("URANOS Executive Alert", name)
    scoped_doc("Project", doc.project, lock=True)
    doc = scoped_doc(doc.doctype, name, lock=True)
    if doc.status == "Resolved":
        return {"name": name, "status": doc.status}
    with authorized_transition():
        doc.acknowledged, doc.status = 1, "Acknowledged"
        doc.save(ignore_permissions=True)
    return {"name": name, "status": doc.status}
