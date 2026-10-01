"""Authenticated entry point; no operational data is rendered into cacheable HTML."""
import frappe

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=%2Furanos"
        raise frappe.Redirect
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.local.response_headers.update({"Cache-Control": "no-store, private", "Pragma": "no-cache"})
    return context
