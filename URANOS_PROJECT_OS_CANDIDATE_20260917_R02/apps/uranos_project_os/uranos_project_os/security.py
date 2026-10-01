"""Fail-closed project isolation for both lists and direct document/API reads.

Custom roles never automatically acquire global ERPNext stock/accounting roles.
Trusted services may access ERP ledger records only after scope+role checks and
must return an explicit, finance-free field allowlist to field users.
"""
from __future__ import annotations

import frappe

FINANCE_ROLES = frozenset({"URANOS Executive", "URANOS Finance Controller"})
STANDARD_PROJECT_FIELDS = {
    "Project": "name", "Task": "project", "Warehouse": "uranos_project",
    "Purchase Order": "project", "Purchase Receipt": "project", "Stock Entry": "project",
    "Stock Reconciliation": "uranos_project", "Quality Inspection": "uranos_project",
    "Stock Ledger Entry": "project", "BOM": "uranos_project",
}
FINANCIAL_STANDARD = frozenset({
    "Purchase Order", "Purchase Receipt", "Stock Entry", "Stock Reconciliation", "Stock Ledger Entry", "BOM",
})
CUSTOM_NAMES = (
    "Project Profile", "Baseline", "Work Package", "Activity Template", "Field Progress Entry", "Material Kit Template", "Kit Issue",
    "Kit Reconciliation", "Kit Return", "Cable Reel", "Cable Reel Movement", "Shipment", "Container",
    "Shipment Milestone", "Document Register", "Blocker", "RFI", "NCR", "Field Inspection", "Change Request",
    "Daily Site Report", "Commissioning Dossier", "Executive Alert", "Delegation", "Stage Gate",
    "Approval Policy", "Approval", "Stock Disposition", "Offline Sync Receipt", "Project Cost", "QA Test Result", "Hold Point",
)
SCOPED_FIELDS = STANDARD_PROJECT_FIELDS | {"URANOS " + name: "project" for name in CUSTOM_NAMES}
FINANCIAL_CUSTOM = frozenset({"URANOS Delegation", "URANOS Approval Policy", "URANOS Approval", "URANOS Project Cost"})
DENY_SHARED_DOCS = frozenset(SCOPED_FIELDS) | {"URANOS Offline Identity Key"}


def current_user(user=None):
    user = user or frappe.session.user
    if not user or user == "Guest":
        frappe.throw("An individual authenticated account is required", frappe.PermissionError)
    # Sensitive read models, native scoped records and private evidence must
    # declare the cache boundary server-side, not rely only on fetch options.
    headers = getattr(getattr(frappe, "local", None), "response_headers", None)
    if headers is not None:
        headers.update({"Cache-Control": "no-store, private", "Pragma": "no-cache"})
        vary = [value.strip() for value in headers.get("Vary", "").split(",") if value.strip()]
        if "cookie" not in {value.lower() for value in vary}:
            vary.append("Cookie")
        headers["Vary"] = ", ".join(vary)
    return user


def has_financial_access(user=None):
    return bool(set(frappe.get_roles(current_user(user))) & FINANCE_ROLES)


def allowed_projects(user=None, doctype=None):
    """Only explicit project grants apply. An empty grant set means no projects.

    A grant restricted to a specific DocType does not become a global grant. The
    setup guide uses apply_to_all_doctypes=1 for normal project membership.
    """
    user = current_user(user)
    local_cache = getattr(frappe.local, "uranos_user_perm_cache", None) if hasattr(frappe, "local") else None
    if local_cache is not None and user in local_cache:
        rows = local_cache[user]
    else:
        rows = frappe.get_all("User Permission", filters={"user": user, "allow": "Project"},
                              fields=["for_value", "apply_to_all_doctypes", "applicable_for"])
        if local_cache is not None:
            local_cache[user] = rows
        elif hasattr(frappe, "local"):
            try:
                frappe.local.uranos_user_perm_cache = {user: rows}
            except Exception:
                pass

    grants = set(row.for_value for row in rows if row.apply_to_all_doctypes or
                 (doctype and row.applicable_for == doctype))

    # Strict Assigned-User Visibility: Include projects explicitly assigned to engineer or site team
    if is_engineer(user):
        assigned_eng = frappe.get_all("Project", filters={"custom_assigned_engineer": user}, pluck="name", ignore_permissions=True)
        grants.update(assigned_eng)
    if is_site_team(user):
        assigned_site = frappe.get_all("Project", filters={"custom_assigned_site_team": user}, pluck="name", ignore_permissions=True)
        grants.update(assigned_site)

    return frozenset(grants)


def is_management(user):
    """Management role (Manager): Global read-only access across all projects."""
    if not user:
        return False
    user_roles = set(frappe.get_roles(user))
    return bool(user_roles & {"management", "Direction", "Manager", "URANOS Executive"})


def is_engineer(user):
    """Engineer role (Ingénieur responsable): Assign, verify, and close on assigned projects."""
    if not user:
        return False
    user_roles = set(frappe.get_roles(user))
    return bool(user_roles & {"engineer", "Ingénieur responsable", "URANOS Engineering Director"})


def is_site_team(user):
    """Site team role (Équipe chantier): Read/write on assigned projects; cannot close."""
    if not user:
        return False
    user_roles = set(frappe.get_roles(user))
    return bool(user_roles & {"site_team", "Équipe chantier", "URANOS Site Controller", "URANOS Team Lead"})


def require_project(project, user=None, doctype=None):
    user = current_user(user)
    if not project:
        frappe.throw("Project is required", frappe.ValidationError)
    if user == "Administrator" or is_management(user):
        return project
    if project not in allowed_projects(user, doctype):
        frappe.throw("Project access denied", frappe.PermissionError)
    return project


def require_roles(*roles, user=None):
    user = current_user(user)
    wanted = {role if role.startswith("URANOS ") else "URANOS " + role for role in roles} | set(roles)
    # Administrator/System Manager is not an implicit business approver.
    if not wanted.intersection(frappe.get_roles(user)):
        frappe.throw("This business action requires an authorized role", frappe.PermissionError)
    return user


def project_for(doc):
    fieldname = SCOPED_FIELDS.get(doc.doctype)
    return doc.get(fieldname) if fieldname else None


def is_project_archived(project: str | None) -> bool:
    """Check if a project is completed or moved to the Historical Archive state."""
    if not project:
        return False
    status = frappe.db.get_value("Project", project, "status")
    if status in ("Completed", "Closed"):
        return True
    profile_status = frappe.db.get_value("URANOS Project Profile", {"project": project}, "status")
    if profile_status in ("Archived", "Completed"):
        return True
    return False


def has_permission(doc, user=None, permission_type=None, ptype=None, **kwargs):
    user = user or frappe.session.user
    if not user or user == "Guest":
        return False
    if user == "Administrator":
        return True  # installation/administration, not business approval authority

    ptype = (ptype or permission_type or kwargs.get("ptype") or "read").lower()
    doctype = doc if isinstance(doc, str) else getattr(doc, "doctype", None) or "Project"

    # 1. Project Governance: ONLY Manager (management role) & Admin can create/write projects & profiles
    if doctype in ("Project", "URANOS Project Profile"):
        if ptype in ("create", "write"):
            if user == "Administrator" or is_management(user):
                return True
            if is_engineer(user) or is_site_team(user):
                return False
        if ptype in ("read", "select", "print", "email"):
            if user == "Administrator" or is_management(user):
                return True
            proj_name = doc if isinstance(doc, str) else (getattr(doc, "name", None) or getattr(doc, "project", None))
            if is_engineer(user):
                if not isinstance(doc, str) and getattr(doc, "custom_assigned_engineer", None):
                    return doc.custom_assigned_engineer == user
                return proj_name in allowed_projects(user)
            if is_site_team(user):
                if not isinstance(doc, str) and getattr(doc, "custom_assigned_site_team", None):
                    return doc.custom_assigned_site_team == user
                return proj_name in allowed_projects(user)

    # 1b. Project Type: Universal read access for all authenticated Desk roles
    if doctype == "Project Type":
        if ptype in ("read", "select", "print", "email"):
            return True
        if ptype in ("create", "write"):
            return user == "Administrator" or is_management(user)

    # 2. Historical Archive Rule:
    # When a project is Completed/Archived, field operations are strictly locked (read-only for assigned historical projects).
    # Manager retains full read access to historical archives.
    project = project_for(doc) if not isinstance(doc, str) else None
    if project and is_project_archived(project):
        if is_management(user) or user == "Administrator":
            if ptype in ("read", "select", "print", "email"):
                return True
            return False  # Archived projects are immutable
        if ptype in ("write", "create", "delete", "submit", "cancel"):
            return False  # Field operations locked

    # 3. Management: Governance rights on Project/Profile; Global read-only on operational data
    if is_management(user):
        if ptype in ("read", "select", "print", "email"):
            return True
        if ptype in ("write", "create"):
            if doctype in ("Project", "URANOS Project Profile"):
                return True
            return False
        if ptype in ("delete", "submit", "cancel"):
            return False

    # 4. Financial access check
    if doctype in FINANCIAL_STANDARD | FINANCIAL_CUSTOM and not has_financial_access(user):
        return False

    # 5. Project isolation
    if not is_management(user):
        if not project:
            project = project_for(doc) if not isinstance(doc, str) else None
        if not project or project not in allowed_projects(user, doctype):
            return False

    # 6. Site team: Can only read/write on assigned projects. Cannot transition to Clôturé
    if is_site_team(user) and not is_engineer(user):
        if doctype == "URANOS Blocker" and ptype in ("write", "create"):
            current_status = getattr(doc, "status", None) if not isinstance(doc, str) else None
            if current_status in ("Closed", "Clôturé"):
                return False

    if doctype == "URANOS Offline Sync Receipt" and getattr(doc, "sync_user", None) != user:
        return False
    return True  # v16 intersects this with core role permissions; None would deny


def get_permission_query_conditions_for_project(user=None):
    """Strict Assigned-User Visibility condition generator for Project DocType.
    Management sees all projects; Engineers and Site Team see only explicitly assigned projects.
    """
    user = user or frappe.session.user
    if not user or user == "Guest":
        return "1=0"
    if user == "Administrator" or is_management(user):
        return ""
    conds = []
    if is_engineer(user):
        conds.append(f"custom_assigned_engineer = '{user}'")
    if is_site_team(user):
        conds.append(f"custom_assigned_site_team = '{user}'")
    if conds:
        return f"({' OR '.join(conds)})"
    return "1=0"


def get_permission_query_conditions(user=None):
    """Permission query condition hook for Project DocType."""
    return get_permission_query_conditions_for_project(user)


def scoped_query(doctype, user=None):
    user = user or frappe.session.user
    if not user or user == "Guest":
        return "1=0"
    if user == "Administrator":
        return ""
    if doctype in FINANCIAL_STANDARD | FINANCIAL_CUSTOM and not has_financial_access(user):
        return "1=0"

    # Management: Global read-only access across all projects
    if is_management(user):
        return ""

    # Project doctype: Strict Assigned-User Visibility
    if doctype == "Project":
        return get_permission_query_conditions_for_project(user)

    projects = allowed_projects(user, doctype)
    if not projects:
        return "1=0"
    # Both table/field names are constants, while project values are SQL escaped.
    values = ", ".join(frappe.db.escape(project) for project in sorted(projects))
    condition = f"`tab{doctype}`.`{SCOPED_FIELDS[doctype]}` IN ({values})"
    if doctype == "URANOS Offline Sync Receipt":
        condition += f" AND `tab{doctype}`.`sync_user` = {frappe.db.escape(user)}"
    return condition


def query_function_name(doctype):
    return "query_" + doctype.lower().replace(" ", "_")


def _make_query(doctype):
    def query(user=None):
        return scoped_query(doctype, user)
    return query


for _doctype in SCOPED_FIELDS:
    globals()[query_function_name(_doctype)] = _make_query(_doctype)


def validate_project_links(doc, method=None):
    """Server-side scope validation includes child links and warehouse boundaries."""
    if doc.doctype not in SCOPED_FIELDS:
        return

    user = current_user()

    # Rule 1: Project Creation Governance (Manager & Admin only)
    if doc.doctype == "Project":
        if not doc.get("company"):
            doc.company = (
                frappe.defaults.get_user_default("Company")
                or frappe.db.get_single_value("Global Defaults", "default_company")
                or "URANOS Group"
            )
        if not doc.get("is_active"):
            doc.is_active = "Yes"
        lat = doc.get("latitude")
        lng = doc.get("longitude")
        if not lat or not lng or float(lat or 0) == 0 or float(lng or 0) == 0:
            frappe.throw(
                "Les coordonnées GPS (Latitude et Longitude) sont obligatoires. Veuillez sélectionner l'emplacement via la carte interactive ou renseigner des coordonnées valides.",
                frappe.ValidationError
            )
        if doc.is_new():
            if user != "Administrator" and not is_management(user):
                frappe.throw(
                    "Seul le Manager (rôle management) ou l'Administrateur Système est habilité à créer de nouveaux projets.",
                    frappe.PermissionError
                )
            return
        if user == "Administrator" or is_management(user):
            return

    project = project_for(doc)

    # Rule 3: Historical Archive Guard (Field operations cannot mutate archived projects)
    if project and is_project_archived(project) and doc.doctype != "Project":
        from uranos_project_os.controllers import transition_is_authorized
        if user != "Administrator" and not transition_is_authorized():
            frappe.throw(
                f"Le projet '{project}' est archivé (Historique). Toutes les opérations et obstacles sont strictement verrouillés en lecture seule.",
                frappe.PermissionError
            )

    require_project(project, doctype=doc.doctype)
    old = doc.get_doc_before_save()
    if old and project_for(old) != project:
        frappe.throw("An existing record cannot be moved to another project")
    _validate_links_in_row(doc, project)
    for child in doc.get_all_children():
        child_project = child.get("project")
        if child_project and child_project != project:
            frappe.throw("Child record project differs from its parent")
        _validate_links_in_row(child, project)


def _validate_links_in_row(row, project):
    for df in row.meta.fields:
        if df.fieldtype not in {"Link", "Dynamic Link"} or not row.get(df.fieldname):
            continue
        target = df.options if df.fieldtype == "Link" else row.get(df.options)
        scope_field = SCOPED_FIELDS.get(target)
        if not scope_field:
            continue
        linked_name = row.get(df.fieldname)
        linked_project = linked_name if target == "Project" else frappe.db.get_value(target, linked_name, scope_field)
        if linked_project != project:
            frappe.throw("Linked document must belong to the same project", frappe.PermissionError)


def validate_evidence(doc):
    """Prevent public files and references to another project's private evidence."""
    names = [row.file for row in doc.get_all_children() if row.doctype == "URANOS Evidence" and row.file]
    names.extend(row.evidence_file for row in doc.get_all_children()
                 if row.doctype == "URANOS Checklist Item" and row.get("evidence_file"))
    if doc.doctype == "URANOS Document Register" and doc.get("file"):
        names.append(doc.file)
    for name in names:
        file = frappe.get_doc("File", name)
        from uranos_project_os.file_security import require_unshared_blob
        require_unshared_blob(file)
        if not file.is_private:
            frappe.throw("Project evidence must be a private file")
        file.check_permission("read")
        if file.attached_to_doctype and file.attached_to_name:
            if file.attached_to_doctype not in SCOPED_FIELDS:
                frappe.throw("Evidence must be attached to a project-scoped record")
            target = frappe.get_doc(file.attached_to_doctype, file.attached_to_name)
            target.check_permission("read")
            if project_for(target) != doc.project:
                frappe.throw("Evidence belongs to another project", frappe.PermissionError)
        elif file.owner != frappe.session.user:
            frappe.throw("Unattached evidence must belong to the current user", frappe.PermissionError)
        if (not str(file.get("file_url") or "").startswith("/private/files/") or
                not file.get("content_hash") or file.get("is_folder")):
            frappe.throw("Evidence must be an immutable local private upload, not a remote URL")


def autoname_project(doc, method=None):
    """Enforce explicit PV-#### identifier if supplied in project_name or name."""
    p_name = (doc.get("project_name") or "").strip()
    if p_name.upper().startswith("PV-"):
        doc.name = p_name.upper()
    elif doc.get("name") and str(doc.name).upper().startswith("PV-"):
        doc.name = str(doc.name).upper()


def prevent_operational_delete(doc, method=None):
    if getattr(frappe.flags, "in_uninstall", False):
        return
    frappe.throw("Operational history cannot be deleted; use a controlled cancellation")


def reject_project_sharing(doc, method=None):
    # Frappe v16 ORs DocShare into list conditions after permission-query hooks
    # and can fall back to share rights after a controller permission denial.
    # Project membership is therefore the only supported grant for scoped data.
    protected_file = False
    if doc.share_doctype == "File":
        from uranos_project_os.file_security import project_references
        protected_file = bool(project_references(frappe.get_doc("File", doc.share_name)))
    if doc.share_doctype in DENY_SHARED_DOCS or protected_file:
        frappe.throw("Project-scoped documents cannot be shared; assign a Project User Permission",
                     frappe.PermissionError)


def offline_key_permission(doc, user=None, **kwargs):
    return (user or frappe.session.user) == "Administrator"


def offline_key_query(user=None, **kwargs):
    return "1=0" if (user or frappe.session.user) != "Administrator" else ""


def standard_before_cancel(doc, method=None):
    from uranos_project_os.controllers import transition_is_authorized
    validate_project_links(doc)
    if not transition_is_authorized():
        frappe.throw("Cancellation requires the controlled approval service", frappe.PermissionError)


def validate_standard_transaction(doc, method=None):
    validate_project_links(doc)

    # Project Lifecycle & Archiving: Automatic transition to Historical Archive
    if doc.doctype == "Project":
        if doc.status in ("Completed", "Closed"):
            doc.is_active = "No"
            prof_name = frappe.db.get_value("URANOS Project Profile", {"project": doc.name})
            if prof_name:
                frappe.db.set_value("URANOS Project Profile", prof_name, "status", "Archived", update_modified=False)

    if doc.doctype == "Warehouse":
        old = doc.get_doc_before_save()
        if old and any(doc.get(field) != old.get(field) for field in
                       ("uranos_stock_state", "company", "is_group", "parent_warehouse")):
            frappe.throw("Warehouse stock state, company and hierarchy are immutable; use an authorized master-data migration")
    # Scope and money cannot be bypassed through a standard REST endpoint. Field
    # APIs operate through explicit trusted services after scope/role validation.
    from uranos_project_os.controllers import transition_is_authorized
    if doc.doctype in FINANCIAL_STANDARD and not transition_is_authorized():
        require_roles(*FINANCE_ROLES)
    # Finance may prepare exact native serial/batch bundles in a non-posting
    # draft. No ordinary save/submit may create stock ledger effects: submission
    # remains reachable only through the validated subject-specific services.
    if doc.doctype == "Stock Reconciliation" or (doc.doctype == "Stock Entry" and
            (doc.purpose not in {"Material Transfer", "Material Issue", "Material Receipt"} or doc.docstatus != 0)):
        if not transition_is_authorized():
            frappe.throw("Stock ledger posting requires the controlled stock service", frappe.PermissionError)


def ensure_project_profile_synced(doc, method=None):
    """Ensure that every Project has a linked URANOS Project Profile with GPS coordinates for GIS Map."""
    if doc.doctype != "Project":
        return
    prof_name = frappe.db.get_value("URANOS Project Profile", {"project": doc.name})
    lat = doc.get("latitude") or 36.8065
    lng = doc.get("longitude") or 10.1815
    if not prof_name:
        from uranos_project_os.controllers import authorized_transition
        prof = frappe.get_doc({
            "doctype": "URANOS Project Profile",
            "project": doc.name,
            "short_code": doc.name,
            "site": doc.project_name or doc.name,
            "governorate": "Tunis",
            "capacity_ac_mw": 10.0,
            "capacity_dc_mwp": 12.0,
            "status": "Active" if doc.is_active == "Yes" and doc.status not in ("Completed", "Closed") else "Archived",
            "latitude": lat,
            "longitude": lng,
        })
        prof.flags.ignore_permissions = True
        with authorized_transition():
            prof.insert(ignore_permissions=True)
    else:
        update_vals = {}
        if doc.get("latitude") and doc.get("longitude"):
            update_vals["latitude"] = doc.latitude
            update_vals["longitude"] = doc.longitude
        if doc.status in ("Completed", "Closed"):
            update_vals["status"] = "Archived"
        elif doc.is_active == "Yes":
            update_vals["status"] = "Active"
        if update_vals:
            frappe.db.set_value("URANOS Project Profile", prof_name, update_vals, update_modified=False)

