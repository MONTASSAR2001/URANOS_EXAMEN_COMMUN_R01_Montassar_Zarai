"""Controlled change authority, independent signatures and propagation evidence.

Approving a change never mutates any affected BOM, baseline, order or ledger.
Every exposed mutation requires POST, a current business role and project scope.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal

import frappe

from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain.controls import (
    identifier,
    number,
    validate_baseline,
    validate_change_transition,
)
from uranos_project_os.services.common import require_post, scoped_doc

FINANCIAL_ROLES = {"URANOS Executive", "URANOS Finance Controller"}
TECHNICAL_ROLES = ("Engineering Director",)
IMPLEMENTATION_ROLES = ("Project Manager", "Civil Director", "Electrical Execution Manager", "Engineering Director")
IMPACT_TYPES = {
    "BOM": "BOM", "URANOS Material Kit Template": "Kit", "URANOS Document Register": "Document",
    "URANOS Baseline": "Baseline", "Purchase Order": "Purchase Order", "Stock Entry": "Stock",
    "URANOS Cable Reel": "Stock", "Task": "Task", "URANOS Activity Template": "Test Procedure",
    "URANOS Work Package": "Work Package",
}


def _locked(name):
    initial = scoped_doc("URANOS Change Request", name)
    scoped_doc("Project", initial.project, lock=True)
    return scoped_doc(initial.doctype, name, lock=True)


def _result(doc, **extra):
    # Never dump hidden costs, policy contents or the financial approval ledger.
    return {"doctype": doc.doctype, "name": doc.name, "status": doc.status,
            "modified": str(doc.modified), **extra}


def _save(doc):
    with authorized_transition():
        # Finance Controller has read + monetary field authority, not general
        # write rights. Narrow methods supply the authorization before this call.
        doc.save(ignore_permissions=True)
    return _result(doc)


def _policy(name, project, *, active=True):
    identifier(name, "policy")
    security.require_project(project)
    policy = frappe.get_doc("URANOS Approval Policy", name)
    if policy.project != project:
        frappe.throw("Change policy belongs to another project", frappe.PermissionError)
    if policy.action != "Change Cost" or policy.first_role not in FINANCIAL_ROLES or policy.second_role not in FINANCIAL_ROLES:
        frappe.throw("Change Cost policy must identify explicit financial business roles")
    number(policy.threshold, "policy threshold")
    start = frappe.utils.getdate(policy.valid_from)
    finish = frappe.utils.getdate(policy.valid_to) if policy.valid_to else None
    if not policy.valid_from or (finish and finish < start):
        frappe.throw("Change policy validity period is invalid")
    company = scoped_doc("Project", project).company
    currency = frappe.db.get_value("Company", company, "default_currency") if company else None
    if not currency or policy.currency != currency:
        frappe.throw("Change policy requires the project's company currency; implicit exchange is forbidden")
    if active:
        today = frappe.utils.getdate()
        if (policy.status != "Approved" or not policy.enabled or not policy.approved_by or
                policy.approved_by == policy.owner or start > today or (finish and finish < today)):
            frappe.throw("An enabled, current, independently approved Change Cost policy is required")
    return policy


def _affected(doc):
    result, seen = [], set()
    for row in doc.impacted_objects:
        doctype, name = row.reference_doctype, row.reference_name
        if doctype not in IMPACT_TYPES:
            frappe.throw("Unsupported change propagation record")
        identifier(name, "affected record")
        key = (doctype, name)
        if key in seen:
            frappe.throw("Change propagation records must be unique")
        seen.add(key)
        # Only project identity is read from rate-bearing native documents. A
        # technical approver must not receive their monetary payload.
        linked_project = frappe.db.get_value(doctype, name, security.SCOPED_FIELDS[doctype])
        if linked_project != doc.project:
            frappe.throw("Affected record is outside the change project", frappe.PermissionError)
        identifier(row.impact, "record impact")
        result.append({"project": doc.project, "name": name, "type": IMPACT_TYPES[doctype],
                       "doctype": doctype, "impact": row.impact})
    if not result:
        frappe.throw("An explicit affected-record propagation checklist is required")
    return result


def _state(doc, affected):
    values = doc.as_dict()
    values["financial_approval_required"] = bool(doc.financial_approval_required)
    values["affected_records"] = affected
    return values


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _baseline_value(field, value):
    if field in {"qty_planned", "weight"}:
        return format(number(value, field).normalize(), "f")
    if field in {"baseline_start", "baseline_finish"}:
        return frappe.utils.getdate(value).isoformat() if value else ""
    return str(value or "")


def _baseline_snapshot(name, project, change_request, *, draft=False):
    """Lock and capture proposed scope, never application state or timestamps.

    Callers already hold the project lock. Child-table saves lock their parent;
    retaining the baseline and WP locks protects these reads through commit.
    ``baseline``/``baseline_approved`` on WP, status, actor/time of application
    are deliberately absent: applying the signed revision is not a scope edit.
    """
    baseline = scoped_doc("URANOS Baseline", name, lock=True)
    if baseline.project != project or baseline.change_request != change_request:
        frappe.throw("The proposed baseline must belong to this project and name this change request")
    if draft and baseline.status not in {"Draft", "Pending Approval"}:
        frappe.throw("Only an unapproved proposed baseline can receive a new scope assessment")
    if baseline.supersedes:
        previous = scoped_doc("URANOS Baseline", baseline.supersedes, lock=True)
        if previous.project != project or previous.name == baseline.name:
            frappe.throw("The proposed baseline predecessor is invalid")
    fields = ("code", "uom", "qty_planned", "weight", "baseline_start", "baseline_finish")
    packages, domain_packages, seen = [], [], set()
    for row in sorted(baseline.packages, key=lambda row: str(row.work_package or "")):
        identifier(row.work_package, "proposed work package")
        if row.work_package in seen:
            frappe.throw("The proposed baseline contains a duplicate work package")
        seen.add(row.work_package)
        wp = scoped_doc("URANOS Work Package", row.work_package, lock=True)
        if wp.project != project or wp.baseline_version != baseline.version:
            frappe.throw("Proposed baseline work package version/project mismatch")
        values = {field: _baseline_value(field, wp.get(field)) for field in fields}
        if any(_baseline_value(field, row.get(field)) != values[field] for field in fields):
            frappe.throw("Proposed baseline rows differ from the authoritative work packages")
        requirements = []
        for requirement in wp.get("required_documents", []):
            if requirement.mandatory not in (0, 1, False, True):
                frappe.throw("Proposed document requirement must have an explicit mandatory flag")
            requirements.append({"document_code": identifier(requirement.document_code, "document code"),
                "required_status": identifier(requirement.required_status, "required document status"),
                "mandatory": int(requirement.mandatory)})
        values.update(work_package=wp.name, baseline_version=wp.baseline_version,
                      required_documents=sorted(requirements, key=_canonical_json))
        for field in ("title", "site", "discipline", "criticality"):
            values[field] = str(wp.get(field) or "")
        packages.append(values)
        domain_packages.append(wp.as_dict())
    validate_baseline(project, baseline.version, domain_packages)
    return {"name": baseline.name, "project": project, "version": baseline.version,
            "supersedes": baseline.supersedes or "", "change_request": baseline.change_request,
            "revision_reason": baseline.revision_reason or "", "packages": packages}


def _capture_scope(doc, affected, *, draft=False):
    return {"version": 1, "baselines": [_baseline_snapshot(row["name"], doc.project, doc.name, draft=draft)
        for row in sorted(affected, key=lambda row: (row["doctype"], row["name"]))
        if row["doctype"] == "URANOS Baseline"]}


def _stored_scope(doc):
    try:
        scope = json.loads(doc.get("scope_snapshot") or "")
    except (TypeError, ValueError):
        frappe.throw("A server-assessed scope snapshot is required; legacy approvals cannot authorize a revision")
    if (not isinstance(scope, dict) or set(scope) != {"version", "baselines"} or
            type(scope["version"]) is not int or scope["version"] != 1 or not isinstance(scope["baselines"], list)):
        frappe.throw("Unsupported change scope snapshot; create a newly assessed proposal")
    return scope


def _verify_scope(doc, affected):
    scope = _stored_scope(doc)
    if scope != _capture_scope(doc, affected):
        frappe.throw("Proposed baseline scope changed after assessment; existing assessment and approvals are invalid")
    return scope


def _digest(doc, policy, affected):
    # Numeric values are normalized across JSON/Float/Decimal round trips.
    money = format(number(doc.cost_impact, "cost impact", minimum=Decimal("-1e18")).normalize(), "f")
    values = {field: doc.get(field) for field in ("name", "project", "work_package", "requested_by", "description",
        "reason", "urgency", "technical_impact", "material_impact", "document_impact", "proposed_solution")}
    values.update(cost_impact=money, schedule_impact_days=str(int(doc.schedule_impact_days or 0)),
                  currency=doc.currency, affected=affected, scope_snapshot=_stored_scope(doc),
                  cost_assessed_by=doc.cost_assessed_by,
                  policy={field: str(policy.get(field) or "") for field in ("name", "currency", "threshold",
                      "first_role", "second_role", "valid_from", "valid_to", "approved_by")})
    return hashlib.sha256(_canonical_json(values).encode()).hexdigest()


def verify_baseline_authorization(change, baseline):
    """Private check for approve_baseline, under its project/record locks.

    Neither project membership nor approval of another impact grants baseline
    authority. No snapshot is manufactured for an already approved/legacy CR.
    """
    if (change.project != baseline.project or change.name != baseline.change_request or
            change.status not in {"Approved", "Implemented", "Verified", "Closed"}):
        frappe.throw("Baseline revision change is not approved for this project")
    affected = _affected(change)
    if not any(row["doctype"] == "URANOS Baseline" and row["name"] == baseline.name for row in affected):
        frappe.throw("Approved change must explicitly include this exact target baseline revision")
    _verify_scope(change, affected)
    policy = _policy(change.policy, change.project, active=False)
    digest = _digest(change, policy, affected)
    if (not change.cost_assessed or not change.cost_assessed_by or
            change.cost_assessment_hash != digest or change.payload_hash != digest or
            not change.technical_approver or change.technical_approver == change.requested_by or
            not policy.approved_by or policy.approved_by == policy.owner or change.currency != policy.currency):
        frappe.throw("Baseline revision lacks an intact independently approved scope signature")
    if number(change.cost_impact, "cost impact", minimum=Decimal("-1e18")) or change.financial_approval_required:
        signatures = _signed_roles(change)
        if not change.financial_approver or change.financial_approver not in signatures or not _financial_ready(change, policy, signatures):
            frappe.throw("Baseline revision lacks the required independent financial signatures")


def _signed_roles(doc):
    signatures = frappe.get_all("URANOS Approval", filters={"project": doc.project,
        "reference_doctype": doc.doctype, "reference_name": doc.name, "action": "Change Cost"},
        fields=["policy", "requester", "approver", "payload_hash", "approved_roles"], limit_page_length=0)
    result = {}
    for signature in signatures:
        if (signature.policy != doc.policy or signature.requester != doc.requested_by or
                signature.payload_hash != doc.payload_hash or signature.approver in {doc.requested_by, doc.technical_approver}):
            frappe.throw("Financial signature does not match the frozen independent change request")
        try:
            roles = json.loads(signature.approved_roles or "[]")
        except (TypeError, ValueError):
            frappe.throw("Financial signature role evidence is invalid")
        if not isinstance(roles, list) or any(role not in FINANCIAL_ROLES for role in roles):
            frappe.throw("Financial signature role evidence is invalid")
        if signature.approver in result:
            frappe.throw("Duplicate financial signature for this change")
        result[signature.approver] = set(roles)
    return result


def _financial_ready(doc, policy, signatures):
    first = {user for user, roles in signatures.items() if policy.first_role in roles}
    amount = abs(number(doc.cost_impact, "cost impact", minimum=Decimal("-1e18")))
    if not first:
        return False
    if amount <= number(policy.threshold, "policy threshold"):
        return True
    second = {user for user, roles in signatures.items() if policy.second_role in roles}
    return any(user != other for user in first for other in second)


@frappe.whitelist(methods=["POST"])
def approve_change_policy(name):
    require_post()
    user = security.require_roles(*FINANCIAL_ROLES)
    initial = scoped_doc("URANOS Approval Policy", name)
    scoped_doc("Project", initial.project, lock=True)
    doc = scoped_doc(initial.doctype, name, lock=True)
    if doc.status != "Draft" or doc.owner == user or not doc.enabled:
        frappe.throw("An enabled draft policy requires independent financial approval")
    _policy(name, doc.project, active=False)
    doc.status, doc.approved_by = "Approved", user
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def assess_change_cost(name, cost_impact, policy):
    require_post()
    user = security.require_roles(*FINANCIAL_ROLES)
    doc = _locked(name)
    if doc.status not in {"Proposed", "Impact Analysis"}:
        frappe.throw("Cost assessment must precede technical approval")
    policy_doc = _policy(policy, doc.project)
    doc.cost_impact = str(number(cost_impact, "cost impact", minimum=Decimal("-1e18")))
    doc.policy, doc.currency = policy_doc.name, policy_doc.currency
    doc.cost_assessed, doc.cost_assessed_by = 1, user
    doc.financial_approval_required = int(abs(Decimal(str(doc.cost_impact))) > Decimal(str(policy_doc.threshold)))
    affected = _affected(doc)
    doc.scope_snapshot = _canonical_json(_capture_scope(doc, affected, draft=True))
    doc.cost_assessment_hash = _digest(doc, policy_doc, affected)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def transition_change(name, status, note=None, evidence_files=None):
    require_post()
    if status == "Financial Approval":
        user = security.require_roles(*FINANCIAL_ROLES)
    elif status in {"Technical Approval", "Verified", "Closed"}:
        user = security.require_roles(*TECHNICAL_ROLES)
    elif status == "Approved":
        user = security.require_roles(*TECHNICAL_ROLES, *FINANCIAL_ROLES)
    else:
        user = security.require_roles(*IMPLEMENTATION_ROLES)
    doc = _locked(name)
    affected = _affected(doc)
    previous = _state(doc, affected)
    if doc.status == "Proposed" and status == "Impact Analysis" and user != doc.requested_by:
        security.require_roles("Project Manager", "Engineering Director")
    policy = None
    if status not in {"Impact Analysis", "Rejected"}:
        if not doc.cost_assessed or not doc.cost_assessed_by:
            frappe.throw("An explicit financial cost assessment, including confirmed zero, is required")
        _verify_scope(doc, affected)
        policy = _policy(doc.policy, doc.project, active=doc.status not in {"Approved", "Implemented", "Verified"})
        if not policy.approved_by or policy.approved_by == policy.owner:
            frappe.throw("Historical change policy lacks independent approval evidence")
        if doc.currency != policy.currency:
            frappe.throw("Change currency differs from its approval policy")
        if doc.status not in {"Proposed", "Impact Analysis"} and doc.payload_hash != _digest(doc, policy, affected):
            frappe.throw("Approved change payload or policy changed; create a new proposal")
    technical = "URANOS Engineering Director" in frappe.get_roles(user)
    financial = bool(set(frappe.get_roles(user)) & FINANCIAL_ROLES)
    if status == "Technical Approval":
        if doc.cost_assessment_hash != _digest(doc, policy, affected):
            frappe.throw("The proposal changed after cost assessment; reassess the complete impact first")
        doc.technical_approver = user
        doc.financial_approval_required = int(abs(Decimal(str(doc.cost_impact))) > Decimal(str(policy.threshold)))
        doc.payload_hash = _digest(doc, policy, affected)
    elif status == "Financial Approval":
        if doc.status != "Technical Approval" or user in {doc.requested_by, doc.technical_approver}:
            frappe.throw("Financial approval requires a separate reviewer of a technically approved request")
        if not (doc.cost_impact or doc.financial_approval_required):
            frappe.throw("This confirmed zero-cost change does not require financial approval")
        roles = set(frappe.get_roles(user)) & FINANCIAL_ROLES
        if not roles.intersection({policy.first_role, policy.second_role}):
            frappe.throw("Your financial role is not authorized by this policy", frappe.PermissionError)
        signatures = _signed_roles(doc)
        if user in signatures:
            frappe.throw("You have already signed this exact change")
        identifier(note, "financial approval reason")
        with authorized_transition():
            frappe.get_doc({"doctype": "URANOS Approval", "project": doc.project, "policy": policy.name,
                "reference_doctype": doc.doctype, "reference_name": doc.name, "action": "Change Cost",
                "payload_hash": doc.payload_hash, "requester": doc.requested_by, "approver": user,
                "approved_roles": json.dumps(sorted(roles)), "approved_at": frappe.utils.now(), "reason": note}).insert(ignore_permissions=True)
        signatures[user] = roles
        if not _financial_ready(doc, policy, signatures):
            return _result(doc, pending_independent_signature=True)
        doc.financial_approver = user
    elif status == "Approved":
        if (doc.cost_impact or doc.financial_approval_required) and not _financial_ready(doc, policy, _signed_roles(doc)):
            frappe.throw("Required independent financial policy signatures are missing")
        if user == doc.requested_by:
            frappe.throw("A requester cannot release their own change")
    elif status == "Implemented":
        doc.implemented_by = user
        doc.implementation_note = identifier(note, "implementation note")
    elif status == "Verified":
        from uranos_project_os.services.reports import _set_evidence
        doc.verified_by = user
        doc.verification_note = identifier(note, "verification note")
        _set_evidence(doc, "verification_evidence", evidence_files)
    elif status == "Rejected":
        security.require_roles("Engineering Director", "Project Manager")
        doc.decision_reason = identifier(note, "rejection reason")
    doc.status = status
    security.validate_evidence(doc)
    validate_change_transition(_state(doc, affected), user, {doc.project}, previous=previous,
                               can_approve_technical=technical, can_approve_financial=financial)
    return _save(doc)
