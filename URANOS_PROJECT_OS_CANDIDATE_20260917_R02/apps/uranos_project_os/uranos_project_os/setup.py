"""Additive installation/migration setup. Never seeds real authority or demo data."""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from uranos_project_os.security import DENY_SHARED_DOCS, FINANCE_ROLES, STANDARD_PROJECT_FIELDS

ROLES = (
    "Executive", "Engineering Director", "Civil Director", "Electrical Execution Manager",
    "Project Manager", "Site Controller", "Storekeeper", "Procurement Logistics", "QA QC",
    "HSE", "Digital Admin", "Finance Controller", "Read Only Auditor", "Team Lead",
)


def before_install():
    from frappe.utils.change_log import get_versions
    versions = get_versions()
    for app in ("frappe", "erpnext"):
        version = str(versions.get(app, {}).get("version", ""))
        if not version.startswith("16."):
            frappe.throw(f"URANOS requires {app} version 16; found {version or 'not installed'}")
    _reject_existing_project_shares()
    _roles()


def _roles():
    for name in ROLES:
        role = "URANOS " + name
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def after_migrate():
    _reject_existing_project_shares()
    _roles()
    fields = {}
    for doctype, fieldname in STANDARD_PROJECT_FIELDS.items():
        if doctype == "Project" or not frappe.db.exists("DocType", doctype):
            continue
        if not frappe.get_meta(doctype).has_field(fieldname):
            fields[doctype] = [{"fieldname": fieldname, "label": "URANOS Project", "fieldtype": "Link",
                                "options": "Project", "insert_after": "company", "in_standard_filter": 1}]
    fields.setdefault("Item", []).extend([
        {"fieldname": "uranos_risk_class", "label": "URANOS Risk Class", "fieldtype": "Select",
         "options": "\nR1\nR2\nR3\nR4", "insert_after": "item_group"},
        {"fieldname": "uranos_reel_tracking", "label": "URANOS Reel Tracking", "fieldtype": "Check",
         "insert_after": "uranos_risk_class"},
        {"fieldname": "uranos_tolerance_percent", "label": "URANOS Tolerance Percent", "fieldtype": "Percent",
         "insert_after": "uranos_reel_tracking"},
    ])
    fields.setdefault("Warehouse", []).append({
        "fieldname": "uranos_stock_state", "label": "URANOS Stock State", "fieldtype": "Select",
        "options": "\nReceiving\nAvailable\nWIP\nQuarantine\nReturns\nScrap", "insert_after": "warehouse_name",
    })
    fields.setdefault("Purchase Receipt Item", []).extend([
        {"fieldname": "uranos_shipment", "label": "URANOS Shipment", "fieldtype": "Link",
         "options": "URANOS Shipment", "insert_after": "purchase_order"},
        {"fieldname": "uranos_container", "label": "URANOS Container", "fieldtype": "Link",
         "options": "URANOS Container", "insert_after": "uranos_shipment"},
    ])
    fields.setdefault("Stock Entry Detail", []).extend([
        {"fieldname": "uranos_kit_issue", "label": "URANOS Kit Issue", "fieldtype": "Link",
         "options": "URANOS Kit Issue", "insert_after": "item_code"},
        {"fieldname": "uranos_reel", "label": "URANOS Cable Reel", "fieldtype": "Link",
         "options": "URANOS Cable Reel", "insert_after": "uranos_kit_issue"},
    ])
    fields.setdefault("Project", []).extend([
        {"fieldname": "latitude", "label": "Latitude", "fieldtype": "Float",
         "insert_after": "status", "read_only": 0, "in_list_view": 1},
        {"fieldname": "longitude", "label": "Longitude", "fieldtype": "Float",
         "insert_after": "latitude", "read_only": 0, "in_list_view": 1},
        {"fieldname": "custom_assigned_engineer", "label": "Assigned Engineer", "fieldtype": "Link",
         "options": "User", "insert_after": "longitude", "read_only": 0, "in_list_view": 1, "in_standard_filter": 1},
        {"fieldname": "custom_assigned_site_team", "label": "Assigned Site Team", "fieldtype": "Link",
         "options": "User", "insert_after": "custom_assigned_engineer", "read_only": 0, "in_list_view": 1, "in_standard_filter": 1},
    ])
    create_custom_fields(fields, update=True)
    _project_finance_levels()
    _standard_permissions()
    _unique_constraints()
    frappe.clear_cache()


def _reject_existing_project_shares():
    if frappe.db.exists("DocShare", {"share_doctype": ["in", list(DENY_SHARED_DOCS)]}):
        frappe.throw("Existing document shares bypass project isolation. Review and remove shares for "
                     "project-scoped records through an authorized migration before enabling URANOS. "
                     "No shares have been deleted automatically.")
    from uranos_project_os.file_security import project_references
    for row in frappe.get_all("DocShare", filters={"share_doctype": "File"}, fields=["share_name"]):
        if project_references(frappe.get_doc("File", row.share_name)):
            frappe.throw("An existing File share bypasses project proof isolation. Review it before migration; no share was deleted.")


def _project_finance_levels():
    # Project remains usable as a link by field users. Amounts are protected by
    # real field permission levels (including REST), never just hidden with JS.
    protected_item_fields = {
        "last_purchase_rate", "max_discount", "item_defaults", "taxes", "supplier_items", "customer_items",
        "opening_stock", "total_projected_qty", "reorder_levels", "safety_stock", "over_billing_allowance",
    }
    for doctype in ("Project", "Task", "Item"):
        for df in frappe.get_meta(doctype).fields:
            if (df.fieldtype == "Currency" or df.fieldname in {"gross_margin", "per_gross_margin"}
                    or (doctype == "Item" and df.fieldname in protected_item_fields)):
                make_property_setter(doctype, df.fieldname, "permlevel", 1, "Int", validate_fields_for_doctype=False)


def _standard_permissions():
    # Add explicit application role rows; do not grant broad ERPNext Stock User,
    # Accounts User or System Manager roles to field users.
    from frappe.permissions import add_permission, update_permission_property
    readers = ["URANOS " + role for role in ROLES if role != "Digital Admin"]
    for doctype in ("Project", "Task", "Warehouse", "Item", "UOM"):
        for role in readers:
            add_permission(doctype, role, 0)
            update_permission_property(doctype, role, 0, "read", 1)
            update_permission_property(doctype, role, 0, "select", 1)
    for doctype in ("Project", "Task", "Item"):
        for role in FINANCE_ROLES:
            add_permission(doctype, role, 1)
            update_permission_property(doctype, role, 1, "read", 1)
    for doctype in ("Supplier", "Batch", "Currency", "User", "Role"):
        permitted = readers if doctype in {"Supplier", "Batch", "Currency", "User"} else list(FINANCE_ROLES)
        for role in permitted:
            add_permission(doctype, role, 0, ptype="select")
            update_permission_property(doctype, role, 0, "select", 1)
    for doctype in ("Purchase Order", "Purchase Receipt", "Stock Entry", "Stock Reconciliation", "BOM"):
        for role in FINANCE_ROLES:
            add_permission(doctype, role, 0)
            for action in ("read", "select", "create", "write", "submit"):
                update_permission_property(doctype, role, 0, action, 1)
    # Engineering can maintain scoped project master data, but business
    # approval always occurs through domain-specific controlled services.
    for doctype in ("Project", "Task", "Warehouse"):
        for role in ("URANOS Engineering Director", "URANOS Project Manager"):
            add_permission(doctype, role, 0)
            for action in ("create", "write"):
                update_permission_property(doctype, role, 0, action, 1)


def _unique_constraints():
    constraints = (
        ("URANOS Project Profile", ["project"], "uranos_profile_project_unique"),
        ("URANOS Work Package", ["project", "code", "baseline_version"], "uranos_wp_version_unique"),
        ("URANOS Baseline", ["project", "version"], "uranos_baseline_unique"),
        ("URANOS Material Kit Template", ["project", "kit_code", "kit_version"], "uranos_kit_version_unique"),
        ("URANOS Document Register", ["project", "document_code", "revision"], "uranos_document_revision_unique"),
        ("URANOS Offline Sync Receipt", ["sync_user", "sync_uuid"], "uranos_sync_actor_uuid_unique"),
        ("URANOS Daily Site Report", ["project", "site", "posting_date"], "uranos_daily_site_unique"),
        ("URANOS Stage Gate", ["project", "gate_number"], "uranos_project_gate_unique"),
    )
    for doctype, columns, name in constraints:
        frappe.db.add_unique(doctype, columns, constraint_name=name)
    for doctype, columns in (
        ("URANOS Field Progress Entry", ["project", "work_package", "status", "posting_date"]),
        ("URANOS NCR", ["project", "status", "severity", "due_date"]),
        ("URANOS Blocker", ["project", "status", "severity"]),
        ("URANOS Shipment", ["project", "status", "eta_revised"]),
    ):
        frappe.db.add_index(doctype, columns, index_name="uranos_operational_lookup")
