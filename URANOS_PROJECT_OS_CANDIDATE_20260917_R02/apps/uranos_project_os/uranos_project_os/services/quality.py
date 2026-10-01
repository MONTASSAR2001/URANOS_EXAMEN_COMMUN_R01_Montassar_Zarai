"""Project-bound QA decisions and commissioning acceptance from persisted proof."""
import frappe

from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain.controls import evidence_present
from uranos_project_os.domain.quality import evaluate_commissioning, validate_commissioning_acceptance, validate_hold_release
from uranos_project_os.services.common import require_post, scoped_doc
from uranos_project_os.services.operations import _locked, _save


@frappe.whitelist(methods=["POST"])
def verify_test_result(name, result):
    require_post()
    user = security.require_roles("QA QC", "Site Controller")
    doc = _locked("URANOS QA Test Result", name)
    if result not in {"Passed", "Failed"} or doc.status != "Pending":
        frappe.throw("Only a pending test can receive an explicit verified result")
    if doc.performed_by == user or not doc.performed_by or not doc.procedure_reference or not doc.result or not doc.system_name:
        frappe.throw("A performed test, procedure, recorded result and independent verifier are required")
    if doc.supersedes:
        previous = scoped_doc("URANOS QA Test Result", doc.supersedes, lock=True)
        if previous.status not in {"Passed", "Failed"} or not doc.revision_reason:
            frappe.throw("Retest requires a verified predecessor and a reason")
        for field in ("project", "work_package", "system_name", "test_code", "procedure_reference"):
            if previous.get(field) != doc.get(field):
                frappe.throw("Retest cannot change its engineering subject or procedure")
        if frappe.db.exists(doc.doctype, {"supersedes": previous.name, "name": ["!=", doc.name]}):
            frappe.throw("Retest history cannot fork")
    security.validate_evidence(doc)
    if not evidence_present(doc.as_dict().get("evidence")):
        frappe.throw("Persisted test evidence is required")
    doc.status = result
    doc.verifier = user
    doc.verified_at = frappe.utils.now()
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def request_retest(name, reason):
    require_post()
    security.require_roles("QA QC", "Site Controller", "Electrical Execution Manager")
    previous = _locked("URANOS QA Test Result", name)
    if previous.status not in {"Passed", "Failed"} or not str(reason or "").strip():
        frappe.throw("Retest requires a verified predecessor and explicit reason")
    if frappe.db.exists(previous.doctype, {"supersedes": previous.name}):
        frappe.throw("An existing successor must be completed/reviewed instead")
    values = {field: previous.get(field) for field in ("project", "work_package", "system_name", "test_code", "procedure_reference")}
    doc = frappe.get_doc({"doctype": previous.doctype, **values, "supersedes": previous.name,
        "revision_reason": reason, "status": "Pending"}).insert()
    return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def verify_inspection(name, accept):
    require_post()
    user = security.require_roles("QA QC", "Site Controller")
    doc = _locked("URANOS Field Inspection", name)
    if not doc.recorded_by or doc.recorded_by == user or doc.status not in {"Draft", "Pending Verification"}:
        frappe.throw("Inspection verification requires an independent reviewer and an unverified inspection")
    if str(accept) not in {"0", "1", "True", "False", "true", "false"}:
        frappe.throw("Inspection decision must be explicit")
    accepted = str(accept) in {"1", "True", "true"}
    if not doc.checklist:
        frappe.throw("Inspection checklist is required")
    if accepted and any(row.get("required") and row.result != "Pass" for row in doc.checklist):
        frappe.throw("Required inspection checks have not passed")
    security.validate_evidence(doc)
    if accepted and not evidence_present(doc.as_dict().get("evidence")):
        frappe.throw("Accepted inspection requires persisted evidence")
    if doc.get("hold_point"):
        hold = scoped_doc("URANOS Hold Point", doc.hold_point, lock=True)
        if hold.status == "Released":
            frappe.throw("A released hold cannot receive a replacement inspection")
        _validate_hold_inspection(hold, doc)
    doc.status = "Accepted" if accepted else "Rejected"
    doc.verifier = user
    with authorized_transition():
        for row in doc.checklist:
            row.completed = int(row.result == "Pass")
            row.verified_by = user
            row.verified_at = frappe.utils.now()
        doc.save()
    return {"name": doc.name, "status": doc.status}


def _validate_hold_inspection(hold, inspection):
    """Bind proof to the exact hold and an approved immutable procedure revision."""
    if inspection.get("hold_point") != hold.name:
        frappe.throw("Inspection must explicitly identify this hold point")
    for field in ("project", "work_package", "activity", "zone", "procedure_reference", "procedure_document"):
        if inspection.get(field) != hold.get(field):
            frappe.throw("Hold inspection must match its exact subject and approved procedure")
    if not hold.get("procedure_reference") or not hold.get("procedure_document"):
        frappe.throw("Hold release requires a referenced approved procedure document")
    procedure = scoped_doc("URANOS Document Register", hold.procedure_document, lock=True)
    if (procedure.project != hold.project or procedure.status not in {"Approved", "IFC"}
            or not procedure.is_current or not procedure.file or not procedure.approver
            or procedure.approver == procedure.issuer):
        frappe.throw("Hold procedure must be an independently approved current document revision")
    security.validate_evidence(procedure)


@frappe.whitelist(methods=["POST"])
def release_hold(name):
    require_post()
    user = security.require_roles("QA QC", "Site Controller")
    doc = _locked("URANOS Hold Point", name)
    if doc.status not in {"Open", "Pending Inspection", "Failed"} or not doc.inspection:
        frappe.throw("A controlled inspection is required for this hold point")
    inspection = scoped_doc("URANOS Field Inspection", doc.inspection, lock=True)
    _validate_hold_inspection(doc, inspection)
    if (inspection.status != "Accepted" or inspection.project != doc.project or inspection.work_package != doc.work_package
            or inspection.zone != doc.zone or inspection.verifier != user or not inspection.recorded_by
            or inspection.recorded_by == user or not evidence_present(inspection.as_dict().get("evidence"))):
        frappe.throw("Hold inspection must match the project, activity zone and authorized reviewer")
    security.validate_evidence(doc)
    doc.status, doc.result, doc.verifier = "Released", "Passed", user
    doc.released_at = frappe.utils.now()
    validate_hold_release(doc.as_dict(), user, {doc.project}, can_release=True)
    return _save(doc)


def _dossier_assessment(doc):
    def documents(doctype):
        names = frappe.get_list(doctype, filters={"project": doc.project}, fields=["name"], limit_page_length=0)
        return [scoped_doc(doctype, row.name).as_dict() for row in names]
    tests = documents("URANOS QA Test Result")
    holds = documents("URANOS Hold Point")
    ncrs = documents("URANOS NCR")
    # An equipment/work-package dossier needs all project-critical NCRs, plus
    # all applicable holds/tests. It cannot hide critical NCRs in another WP.
    if doc.work_package:
        tests = [row for row in tests if row.get("work_package") == doc.work_package]
        holds = [row for row in holds if row.get("work_package") == doc.work_package]
    requirements = {row.code: row.acceptance_reference for row in doc.required_tests if row.required}
    if len(requirements) != sum(bool(row.required) for row in doc.required_tests) or not doc.system_name:
        frappe.throw("Commissioning needs unique requirements and a specific system identity")
    # An unrelated inverter or procedure cannot satisfy a dossier just because
    # its test code happens to match. Mismatches remain missing requirements.
    tests = [row for row in tests if row.get("system_name") == doc.system_name and
             row.get("test_code") in requirements and requirements[row["test_code"]] and
             row.get("procedure_reference") == requirements[row["test_code"]]]
    punchlist = [{"name": row.code, "project": doc.project,
                  "status": "Closed" if row.completed and row.verified_by and row.evidence_file and row.verified_by != row.performed_by else "Open"}
                 for row in doc.punch_list]
    return evaluate_commissioning(doc.project, required_tests=[row.code for row in doc.required_tests if row.required], tests=tests,
        required_documents=[row.document_code for row in doc.required_documents if row.mandatory],
        documents=documents("URANOS Document Register"), holds=holds, ncrs=ncrs, punchlist=punchlist)


@frappe.whitelist()
def commissioning_readiness(name):
    security.require_roles("QA QC", "Engineering Director", "Electrical Execution Manager", "Project Manager")
    return _dossier_assessment(scoped_doc("URANOS Commissioning Dossier", name))


@frappe.whitelist(methods=["POST"])
def submit_commissioning(name):
    require_post()
    security.require_roles("QA QC", "Engineering Director", "Electrical Execution Manager", "Project Manager")
    doc = _locked("URANOS Commissioning Dossier", name)
    if doc.status != "Draft" or not doc.required_tests or not doc.required_documents:
        frappe.throw("Commissioning requires a draft dossier with explicit test and document requirements")
    if any(row.required and not row.acceptance_reference for row in doc.required_tests):
        frappe.throw("Required tests need approved engineering acceptance references")
    doc.status = "Testing"
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def close_punch_item(name, code, evidence_file):
    require_post()
    user = security.require_roles("QA QC", "Site Controller")
    doc = _locked("URANOS Commissioning Dossier", name)
    if doc.status not in {"Testing", "Pending Acceptance"}:
        frappe.throw("Punch item closure requires a dossier in testing")
    matches = [row for row in doc.punch_list if row.code == code]
    if len(matches) != 1 or not matches[0].performed_by or matches[0].performed_by == user:
        frappe.throw("An independently corrected, unique punch item is required")
    row = matches[0]
    row.evidence_file = evidence_file
    row.completed, row.verified_by, row.verified_at = 1, user, frappe.utils.now()
    security.validate_evidence(doc)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def accept_commissioning(name):
    require_post()
    user = security.require_roles("QA QC", "Engineering Director")
    doc = _locked("URANOS Commissioning Dossier", name)
    if doc.status not in {"Testing", "Pending Acceptance"}:
        frappe.throw("Commissioning acceptance requires a submitted dossier")
    security.validate_evidence(doc)
    assessment = _dossier_assessment(doc)
    doc.accepted_by = user
    doc.accepted_at = frappe.utils.now()
    validate_commissioning_acceptance(doc.as_dict(), assessment, actor=user, permitted_projects={doc.project}, can_accept=True)
    doc.status = "Accepted"
    return _save(doc)
