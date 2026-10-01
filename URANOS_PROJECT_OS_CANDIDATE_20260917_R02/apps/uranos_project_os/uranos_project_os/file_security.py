"""Frappe v16 File extension: enforce proof boundaries before disk operations.

doc_events.validate/on_trash alone run after File's own disk-changing method.
The supported v16 mixin runs first, without patching framework core.
"""
import frappe
from frappe.model.document import Document

from uranos_project_os import security


def project_references(file):
    """Resolve proof usage; private URLs cannot confer cross-project authority."""
    parents = set()
    copies = [file]
    if file.get("file_url"):
        copies.extend(frappe.get_all("File", filters={"file_url": file.file_url},
            fields=["name", "attached_to_doctype", "attached_to_name"]))
    names = {row.get("name") for row in copies if row.get("name")}
    for row in copies:
        if row.get("attached_to_doctype") in security.SCOPED_FIELDS and row.get("attached_to_name"):
            parents.add((row.attached_to_doctype, row.attached_to_name))
    if names and frappe.db.table_exists("URANOS Evidence"):
        for doctype, field in (("URANOS Evidence", "file"), ("URANOS Checklist Item", "evidence_file")):
            for row in frappe.get_all(doctype, filters={field: ["in", sorted(names)]}, fields=["parenttype", "parent"]):
                if row.parenttype in security.SCOPED_FIELDS:
                    parents.add((row.parenttype, row.parent))
        for doctype, field in (("URANOS Document Register", "file"), ("URANOS Daily Site Report", "pdf_snapshot")):
            for row in frappe.get_all(doctype, filters={field: ["in", sorted(names)]}, fields=["name"]):
                parents.add((doctype, row.name))
    return parents


def require_file_scope(file, user=None):
    parents = project_references(file)
    if not parents:
        return parents
    user = security.current_user(user)
    projects = set()
    for doctype, name in parents:
        project = name if doctype == "Project" else frappe.db.get_value(doctype, name, security.SCOPED_FIELDS[doctype])
        security.require_project(project, user=user, doctype=doctype)
        projects.add(project)
        parent = frappe.get_doc(doctype, name)
        if not parent.has_permission("read", user=user):
            frappe.throw("Access to the evidence parent is denied", frappe.PermissionError)
    if len(projects) > 1:
        frappe.throw("A private evidence file cannot be shared across projects", frappe.PermissionError)
    return parents


def file_permission(doc, user=None, permission_type=None, **kwargs):
    from frappe.core.doctype.file.file import has_permission
    try:
        require_file_scope(doc, user)
    except frappe.PermissionError:
        return False
    return has_permission(doc, permission_type, user)


def require_unshared_blob(file):
    names = {file.get("name")} if file.get("name") else set()
    if file.get("file_url"):
        names.update(row.name for row in frappe.get_all("File", filters={"file_url": file.file_url}, fields=["name"]))
    if names and frappe.db.exists("DocShare", {"share_doctype": "File", "share_name": ["in", sorted(names)]}):
        frappe.throw("Shared uploads or file aliases cannot become project evidence; review existing shares first", frappe.PermissionError)


def guard_write(file):
    old = file.get_doc_before_save()
    parents = require_file_scope(file)
    if old:
        parents |= require_file_scope(old)
    if not parents:
        return
    require_unshared_blob(file)
    if not file.get("is_private"):
        frappe.throw("Project evidence must remain private", frappe.PermissionError)
    if old:
        protected = ("is_private", "file_url", "content_hash", "file_name", "file_size", "owner")
        if any(file.get(field) != old.get(field) for field in protected) or file.get("content"):
            frappe.throw("Persisted project evidence cannot be overwritten; upload a new revision")
        # An initially unattached upload can be attached once, only to its own
        # project. Subsequent detach/move/reassignment is always forbidden.
        if old.get("attached_to_doctype") or old.get("attached_to_name"):
            for field in ("attached_to_doctype", "attached_to_name", "attached_to_field"):
                if file.get(field) != old.get(field):
                    frappe.throw("Project evidence attachment identity is immutable")


def file_query(user=None):
    """AND constraint on File lists, including proof-only references/blob copies.

    Frappe's standard File list query permits any readable parent DocType; that
    is not project membership. All table/field identifiers below are constants.
    Values are escaped and every alias of a protected blob inherits its scope.
    """
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    if not user or user == "Guest" or not frappe.db.table_exists("URANOS Evidence"):
        return "1=0"
    grants = {doctype: security.allowed_projects(user, doctype) for doctype in security.SCOPED_FIELDS}
    finance = security.has_financial_access(user)

    def denied_parent(type_expression, name_expression):
        clauses = []
        for doctype, project_field in security.SCOPED_FIELDS.items():
            kind = frappe.db.escape(doctype)
            projects = grants[doctype]
            if not projects or (doctype in security.FINANCIAL_CUSTOM | security.FINANCIAL_STANDARD and not finance):
                clauses.append(f"({type_expression}={kind})")
            else:
                scope = ",".join(frappe.db.escape(project) for project in sorted(projects))
                clauses.append(f"({type_expression}={kind} AND NOT EXISTS (SELECT 1 FROM `tab{doctype}` allowed_parent "
                    f"WHERE allowed_parent.name={name_expression} AND allowed_parent.`{project_field}` IN ({scope})))")
        return "(" + " OR ".join(clauses) + ")"

    attached = denied_parent("proof_file.attached_to_doctype", "proof_file.attached_to_name")
    evidence = denied_parent("ev.parenttype", "ev.parent")
    checklist = denied_parent("ck.parenttype", "ck.parent")
    document = denied_parent(frappe.db.escape("URANOS Document Register"), "dr.name")
    daily = denied_parent(frappe.db.escape("URANOS Daily Site Report"), "ds.name")
    return ("NOT EXISTS (SELECT 1 FROM `tabFile` proof_file WHERE "
        "(proof_file.name=`tabFile`.name OR (COALESCE(`tabFile`.file_url,'')<>'' AND proof_file.file_url=`tabFile`.file_url)) AND ("
        + attached + " OR EXISTS (SELECT 1 FROM `tabURANOS Evidence` ev WHERE ev.file=proof_file.name AND " + evidence + ")"
        " OR EXISTS (SELECT 1 FROM `tabURANOS Checklist Item` ck WHERE ck.evidence_file=proof_file.name AND " + checklist + ")"
        " OR EXISTS (SELECT 1 FROM `tabURANOS Document Register` dr WHERE dr.file=proof_file.name AND " + document + ")"
        " OR EXISTS (SELECT 1 FROM `tabURANOS Daily Site Report` ds WHERE ds.pdf_snapshot=proof_file.name AND " + daily + ")))" )


class ProjectEvidenceFileMixin(Document):
    def before_insert(self):
        guard_write(self)
        return super().before_insert()

    def validate(self):
        guard_write(self)
        return super().validate()

    def on_trash(self):
        if project_references(self):
            frappe.throw("Project evidence cannot be deleted; use a new auditable revision")
        return super().on_trash()

    def is_downloadable(self):
        try:
            require_file_scope(self)
        except frappe.PermissionError:
            return False
        return super().is_downloadable()

    def get_content(self, *args, **kwargs):
        require_file_scope(self)
        return super().get_content(*args, **kwargs)

    def save_file(self, *args, **kwargs):
        # optimize_file() calls save_file before save/validate; close that path.
        if self.get("name") and frappe.db.exists("File", self.name) and project_references(self):
            frappe.throw("Referenced project evidence cannot be rewritten or optimized")
        return super().save_file(*args, **kwargs)
