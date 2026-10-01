"""Narrow project-control transitions with server-owned identity and evidence."""
from __future__ import annotations

import frappe

from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain.controls import validate_baseline, validate_progress_entry
from uranos_project_os.domain.quality import (
    current_ifc,
    validate_document_transition,
    validate_ncr_transition,
)
from uranos_project_os.services.common import actor, require_post, scoped_doc


def _locked(doctype, name):
    # Consistent project-first lock order serializes competing approval/correction
    # chains and document-code revisions within one project, including phantoms.
    initial = scoped_doc(doctype, name, permission="write")
    scoped_doc("Project", initial.project, lock=True)
    return scoped_doc(doctype, name, permission="write", lock=True)


def _save(doc):
    with authorized_transition():
        doc.save()
    return {"doctype": doc.doctype, "name": doc.name, "status": doc.status, "modified": str(doc.modified)}


def _approved_wp(doc):
    if doc.get("kit_issue") and doc.get("cable_reel"):
        frappe.throw("Progress must use at most one material allocation")
    wp = scoped_doc("URANOS Work Package", doc.work_package, lock=True)
    if wp.project != doc.project or wp.baseline_version != doc.baseline_version or not wp.baseline_approved:
        frappe.throw("Progress must use an approved work package baseline")
    if not doc.get("correction_of"):
        baseline_name = frappe.db.get_value("URANOS Project Profile", {"project": doc.project}, "current_baseline")
        current = scoped_doc("URANOS Baseline", baseline_name) if baseline_name else None
        if not current or current.status != "Approved" or current.version != doc.baseline_version:
            frappe.throw("New work must use the current approved baseline; review stale declarations")
    for field, doctype in (("kit_issue", "URANOS Kit Issue"), ("cable_reel", "URANOS Cable Reel")):
        if doc.get(field):
            allocation = scoped_doc(doctype, doc.get(field), lock=True)
            states = {"Issued", "Partially Used", "Variance Review"} if field == "kit_issue" else {"In Use", "Reconciliation"}
            if allocation.project != doc.project or allocation.status not in states:
                frappe.throw("Material allocation must be issued and open")
            if allocation.get("work_package") and allocation.work_package != doc.work_package:
                previous_wp = scoped_doc("URANOS Work Package", allocation.work_package)
                if (not previous_wp.baseline_approved or previous_wp.project != wp.project or
                        previous_wp.code != wp.code or previous_wp.uom != wp.uom):
                    frappe.throw("Material allocation belongs to another work package")
            if field == "kit_issue" and any(doc.get(key) != allocation.get(key) for key in ("activity", "zone", "crew")):
                frappe.throw("Progress activity, zone and crew must match its issued kit")
    for requirement in wp.required_documents:
        if not requirement.mandatory:
            continue
        revisions = frappe.get_list("URANOS Document Register", filters={"project": doc.project, "document_code": requirement.document_code},
            fields=["name", "project", "document_code", "revision", "issuer", "approver", "file", "status", "is_current"], limit_page_length=0)
        if requirement.required_status != "IFC" or not current_ifc(doc.project, requirement.document_code, revisions):
            frappe.throw("An applicable current IFC document is required")
    return wp


@frappe.whitelist(methods=["POST"])
def approve_baseline(name):
    require_post()
    user = security.require_roles("Engineering Director")
    baseline = _locked("URANOS Baseline", name)
    if baseline.status not in {"Draft", "Pending Approval"} or baseline.owner == user:
        frappe.throw("Baseline approval requires an independent engineering approver and an unapproved revision")
    packages = []
    for row in baseline.packages:
        wp = scoped_doc("URANOS Work Package", row.work_package, lock=True)
        if wp.project != baseline.project or wp.baseline_version != baseline.version:
            frappe.throw("Baseline work package version/project mismatch")
        # Freeze the exact approved snapshot; draft rows cannot invent a second
        # set of quantities that differs from the authoritative work package.
        for field in ("code", "uom", "qty_planned", "weight", "baseline_start", "baseline_finish"):
            if str(row.get(field) or "") != str(wp.get(field) or ""):
                frappe.throw("Baseline snapshot differs from the work package")
        packages.append(dict(wp.as_dict(), name=wp.name))
    validate_baseline(baseline.project, baseline.version, packages)
    profiles = frappe.get_list("URANOS Project Profile", filters={"project": baseline.project}, fields=["name"], limit_page_length=2)
    if len(profiles) != 1:
        frappe.throw("One complete project profile is required")
    profile = scoped_doc("URANOS Project Profile", profiles[0].name, permission="write", lock=True)
    if profile.current_baseline:
        previous = scoped_doc("URANOS Baseline", profile.current_baseline, permission="write", lock=True)
        if baseline.supersedes != previous.name or not baseline.change_request:
            frappe.throw("Baseline revision requires the current baseline and an approved change")
        from uranos_project_os.services.changes import verify_baseline_authorization
        change = scoped_doc("URANOS Change Request", baseline.change_request, lock=True)
        # Exact target, assessed proposed data and independent signatures must
        # all match under locks before any baseline/WP/profile is mutated.
        verify_baseline_authorization(change, baseline)
        current_by_code = {row["code"]: row for row in packages}
        if len(current_by_code) != len(packages):
            frappe.throw("Work package codes must be unique within a baseline")
        history = frappe.get_list("URANOS Work Package", filters={"project": baseline.project, "baseline_approved": 1},
            fields=["name", "code", "uom"], limit_page_length=0)
        for old in history:
            replacement = current_by_code.get(old.code)
            has_progress = frappe.db.exists("URANOS Field Progress Entry", {"work_package": old.name})
            if (replacement and replacement["uom"] != old.uom) or (has_progress and not replacement):
                frappe.throw("A revised baseline must preserve historical work package code and UOM; explicit scope remapping is not configured")
        previous.status = "Superseded"
        _save(previous)
    elif baseline.supersedes or baseline.change_request:
        frappe.throw("An initial baseline cannot reuse revision/change authority without a current baseline")
    baseline.status = "Approved"
    baseline.approved_by = user
    baseline.approved_at = frappe.utils.now()
    result = _save(baseline)
    with authorized_transition():
        for row in baseline.packages:
            wp = frappe.get_doc("URANOS Work Package", row.work_package)
            wp.baseline_approved = 1
            wp.baseline = baseline.name
            wp.save()
        profile.current_baseline = baseline.name
        profile.save()
    return result


@frappe.whitelist(methods=["POST"])
def submit_progress(name):
    require_post()
    user = actor()
    security.require_roles("Team Lead", "Site Controller", "Civil Director", "Electrical Execution Manager", "Project Manager")
    doc = _locked("URANOS Field Progress Entry", name)
    _approved_wp(doc)
    previous = doc.as_dict()
    correction = scoped_doc("URANOS Field Progress Entry", doc.correction_of, lock=True).as_dict() if doc.correction_of else None
    if correction and any(doc.get(field) != correction.get(field) for field in ("kit_issue", "cable_reel")):
        frappe.throw("A correction must preserve its original material allocation")
    doc.status = "Pending Verification"
    validate_progress_entry(doc.as_dict(), user, {doc.project}, previous=previous, correction=correction)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def verify_progress(name, qty_verified):
    require_post()
    user = security.require_roles("Site Controller")
    doc = _locked("URANOS Field Progress Entry", name)
    _approved_wp(doc)
    previous = doc.as_dict()
    correction = None
    if doc.correction_of:
        correction = scoped_doc("URANOS Field Progress Entry", doc.correction_of, lock=True).as_dict()
        if any(doc.get(field) != correction.get(field) for field in ("kit_issue", "cable_reel")):
            frappe.throw("A correction must preserve its original material allocation")
        if frappe.db.exists("URANOS Field Progress Entry", {"correction_of": doc.correction_of, "status": "Verified"}):
            frappe.throw("This contribution already has a verified correction; correct the latest entry instead")
    security.validate_evidence(doc)
    doc.status = "Verified"
    doc.qty_verified = qty_verified
    doc.verifier = user
    doc.verified_at = frappe.utils.now()
    validate_progress_entry(doc.as_dict(), user, {doc.project}, can_verify=True, previous=previous, correction=correction)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def report_correction(name, qty_reported, reason):
    require_post()
    user = security.require_roles("Team Lead", "Site Controller", "Project Manager")
    old = _locked("URANOS Field Progress Entry", name)
    if old.status != "Verified":
        frappe.throw("Only verified work may be corrected")
    if frappe.db.exists("URANOS Field Progress Entry", {"correction_of": old.name, "status": ["in", ["Draft", "Reported", "Pending Verification", "Verified"]]}):
        frappe.throw("An active correction already exists; follow that correction chain")
    values = {key: old.get(key) for key in ("project", "work_package", "baseline_version", "activity", "site", "zone", "crew", "posting_date", "kit_issue", "cable_reel")}
    new = frappe.get_doc({"doctype": old.doctype, **values, "qty_reported": qty_reported, "qty_verified": 0,
        "reported_by": user, "correction_of": old.name, "revision_reason": reason, "status": "Draft"})
    new.insert()
    validate_progress_entry(new.as_dict(), user, {new.project}, correction=old.as_dict())
    return {"doctype": new.doctype, "name": new.name, "status": new.status}


@frappe.whitelist(methods=["POST"])
def reject_or_cancel_progress(name, status, reason):
    require_post()
    user = security.require_roles("Team Lead", "Site Controller", "Civil Director", "Electrical Execution Manager", "Project Manager")
    doc = _locked("URANOS Field Progress Entry", name)
    reviewer = "URANOS Site Controller" in frappe.get_roles(user)
    if status not in {"Rejected", "Cancelled"} or not str(reason or "").strip():
        frappe.throw("An explicit rejection/cancellation and reason are required")
    if status == "Rejected" and (not reviewer or doc.reported_by == user or doc.status != "Pending Verification"):
        frappe.throw("A pending declaration needs independent controller rejection")
    previous = doc.as_dict()
    doc.status, doc.rejection_reason = status, reason
    validate_progress_entry(doc.as_dict(), user, {doc.project}, previous=previous, can_verify=reviewer)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def transition_document(name, status):
    require_post()
    user = actor()
    security.require_roles("Engineering Director", "Project Manager")
    doc = _locked("URANOS Document Register", name)
    previous = doc.as_dict()
    approval = status in {"Approved", "IFC", "As-built", "Superseded"}
    if approval:
        security.require_roles("Engineering Director")
    if status == "Superseded":
        frappe.throw("Supersession is performed atomically by issuing the replacement revision")
    replaced = scoped_doc("URANOS Document Register", doc.supersedes, lock=True) if doc.supersedes else None
    security.validate_evidence(doc)
    doc.status = status
    if approval:
        doc.approver = user
        doc.approval_date = frappe.utils.now()
    doc.is_current = int(status in {"IFC", "As-built"})
    validate_document_transition(doc.as_dict(), user, {doc.project}, previous=previous, can_approve=approval,
                                 supersedes=replaced.as_dict() if replaced else None)
    if status in {"IFC", "As-built"}:
        currents = frappe.get_list("URANOS Document Register", filters={"project": doc.project,
            "document_code": doc.document_code, "is_current": 1, "name": ["!=", doc.name]}, fields=["name"], limit_page_length=0)
        if currents and (len(currents) != 1 or not replaced or currents[0].name != replaced.name):
            frappe.throw("Issue the revision explicitly replacing the current document")
        if replaced:
            old = replaced.as_dict()
            replaced.status = "Superseded"
            replaced.is_current = 0
            validate_document_transition(replaced.as_dict(), user, {doc.project}, previous=old, can_approve=True)
            with authorized_transition():
                replaced.save(ignore_permissions=True)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def transition_ncr(name, status, closure_verification=None):
    require_post()
    user = actor()
    security.require_roles("QA QC", "Site Controller", "Project Manager")
    doc = _locked("URANOS NCR", name)
    previous = doc.as_dict()
    can_close = "URANOS QA QC" in frappe.get_roles(user)
    if status == "Closed":
        security.require_roles("QA QC")
        doc.closure_verifier = user
        doc.closure_verification = closure_verification
        doc.closed_at = frappe.utils.now()
    if status == "Corrective Action":
        if user != doc.responsible:
            frappe.throw("Corrective action must be recorded by the named responsible user")
        doc.corrected_by = user
    doc.status = status
    security.validate_evidence(doc)
    validate_ncr_transition(doc.as_dict(), user, {doc.project}, previous=previous, can_close=can_close)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def review_ncr_severity(name, severity, reason):
    require_post()
    security.require_roles("QA QC")
    doc = _locked("URANOS NCR", name)
    if doc.status == "Closed" or severity not in {"Low", "Medium", "High", "Critical"} or not str(reason or "").strip():
        frappe.throw("An open NCR, explicit severity and QA review reason are required")
    doc.severity, doc.severity_change_reason = severity, reason
    return _save(doc)  # Frappe Version records named reviewer and before/after values
