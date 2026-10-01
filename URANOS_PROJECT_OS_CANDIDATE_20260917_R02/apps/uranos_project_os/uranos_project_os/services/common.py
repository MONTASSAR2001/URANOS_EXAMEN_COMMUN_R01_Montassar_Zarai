"""Trusted request, scope and locking helpers shared by narrow business services."""
from __future__ import annotations

import frappe

from uranos_project_os import security


def actor():
    return security.current_user()


def require_post():
    request = getattr(frappe.local, "request", None)
    if request is not None and request.method != "POST":
        frappe.throw("POST is required for this action", frappe.PermissionError)
    if request is not None and hasattr(request, "headers"):
        expected = request.headers.get("X-URANOS-User")
        if expected and expected != actor():
            frappe.throw("Session identity changed; authenticate again", frappe.PermissionError)


def scoped_doc(doctype, name, *, permission="read", lock=False):
    if doctype not in security.SCOPED_FIELDS:
        frappe.throw("Unsupported operational record", frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    security.require_project(security.project_for(doc), doctype=doctype)
    doc.check_permission(permission)
    if lock:
        # Table names are selected solely from the server's constant allowlist.
        rows = frappe.db.sql(f"SELECT name FROM `tab{doctype}` WHERE name=%s FOR UPDATE", (name,))
        if not rows:
            frappe.throw("Operational record was not found", frappe.DoesNotExistError)
        # v16's explicit locking read includes the child tables. A nonlocking
        # reload after FOR UPDATE could still use an older REPEATABLE READ
        # snapshot instead of the just-locked business state.
        doc = frappe.get_doc(doctype, name, for_update=True)
        security.require_project(security.project_for(doc), doctype=doctype)
        doc.check_permission(permission)
    return doc


def project_rows(doctype, project, fields, *, limit=500, order_by="modified desc"):
    security.require_project(project, doctype=doctype)
    return frappe.get_list(doctype, filters={security.SCOPED_FIELDS[doctype]: project},
                           fields=fields, limit_page_length=limit, order_by=order_by, ignore_permissions=True)


def require_project(project_or_doc, user=None, doctype=None):
    if hasattr(project_or_doc, "doctype"):
        project = security.project_for(project_or_doc) or getattr(project_or_doc, "project", None)
        return security.require_project(project, user=user, doctype=project_or_doc.doctype)
    return security.require_project(project_or_doc, user=user, doctype=doctype)

