"""Frappe extension hooks only; never patches framework/ERPNext core."""
from uranos_project_os.security import SCOPED_FIELDS, query_function_name

app_name = "uranos_project_os"
app_title = "URANOS Project OS"
app_publisher = "URANOS GROUP"
app_description = "Photovoltaic project execution and verified control"
app_email = ""
app_license = "UNLICENSED"
required_apps = ["erpnext"]

before_install = "uranos_project_os.setup.before_install"
after_install = "uranos_project_os.setup.after_migrate"
after_migrate = "uranos_project_os.setup.after_migrate"
scheduler_events = {"hourly": ["uranos_project_os.services.monitoring.refresh_alerts"]}

# Custom Desk Overhaul Theme & Scripts
app_logo_url = "/assets/uranos_project_os/images/uranos-logo.jpeg"
favicon = "/assets/uranos_project_os/images/uranos-logo.jpeg"
website_context = {
    "favicon": "/assets/uranos_project_os/images/uranos-logo.jpeg",
    "splash_image": "/assets/uranos_project_os/images/uranos-logo.jpeg"
}

app_include_css = [
    "/assets/uranos_project_os/leaflet/leaflet.css",
    "/assets/uranos_project_os/css/desk_theme.css",
    "/assets/uranos_project_os/css/uranos_ai_copilot.css"
]
app_include_js = [
    "/assets/uranos_project_os/js/desk_theme.js"
]

doctype_js = {name: "public/js/workflows.js" for name in (
    "URANOS Change Request", "URANOS Daily Site Report", "URANOS RFI",
    "URANOS Blocker", "URANOS Approval Policy",
)}
doctype_list_js = {
    "Project": "public/js/project_list.js"
}

permission_query_conditions = {
    doctype: "uranos_project_os.security." + query_function_name(doctype) for doctype in SCOPED_FIELDS
}
permission_query_conditions["Project"] = "uranos_project_os.security.get_permission_query_conditions_for_project"
has_permission = {doctype: "uranos_project_os.security.has_permission" for doctype in SCOPED_FIELDS}
has_permission["URANOS Offline Identity Key"] = "uranos_project_os.security.offline_key_permission"
has_permission["File"] = "uranos_project_os.file_security.file_permission"
permission_query_conditions["File"] = "uranos_project_os.file_security.file_query"
extend_doctype_class = {"File": ["uranos_project_os.file_security.ProjectEvidenceFileMixin"]}
permission_query_conditions["URANOS Offline Identity Key"] = "uranos_project_os.security.offline_key_query"
doc_events = {
    doctype: {
        "validate": "uranos_project_os.security.validate_standard_transaction",
        "before_cancel": "uranos_project_os.security.standard_before_cancel",
        "on_trash": "uranos_project_os.security.prevent_operational_delete",
    }
    for doctype in SCOPED_FIELDS if not doctype.startswith("URANOS ")
}
doc_events["DocShare"] = {"validate": "uranos_project_os.security.reject_project_sharing"}
doc_events["Project"] = {
    "autoname": "uranos_project_os.security.autoname_project",
    "validate": "uranos_project_os.security.validate_standard_transaction",
    "on_update": "uranos_project_os.security.ensure_project_profile_synced",
    "before_cancel": "uranos_project_os.security.standard_before_cancel",
    "on_trash": "uranos_project_os.security.prevent_operational_delete",
}
