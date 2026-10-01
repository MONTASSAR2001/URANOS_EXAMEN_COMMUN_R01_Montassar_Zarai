import frappe
from frappe.apps import get_default_path

no_cache = True


def get_context(context):
    redirect_to = frappe.local.request.args.get("redirect-to")
    if frappe.session.user != "Guest":
        if not redirect_to:
            redirect_to = get_default_path() or "/app"
        if redirect_to != "login":
            frappe.local.flags.redirect_location = redirect_to
            raise frappe.Redirect

    context.no_header = True
    context.no_breadcrumbs = True
    context.no_sidebar = True
    context["title"] = "Sign In — URANOS Group"
    context["redirect_to"] = redirect_to or "/app"
    return context
