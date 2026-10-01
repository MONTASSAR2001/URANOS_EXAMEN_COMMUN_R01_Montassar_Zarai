"""Document, quality hold, NCR and commissioning invariants (no persistence)."""

from .controls import RuleViolation, calendar_date, check_scope, evidence_present, identifier, same_project


DOCUMENT_TRANSITIONS = {
    "Draft": {"Draft", "Internal Review", "For Review"},
    "Internal Review": {"Draft", "Approved", "As-built"},
    "For Review": {"Draft", "Approved", "As-built"},
    "Approved": {"IFC", "Superseded"},
    "IFC": {"Superseded"},
    "As-built": {"Superseded"},
    "Superseded": set(),
}


def _document_shape(document, project):
    same_project(document, project)
    for field in ("name", "document_code", "revision", "issuer"):
        identifier(document.get(field), field)
    if document.get("status") not in DOCUMENT_TRANSITIONS:
        raise RuleViolation("invalid document status")
    if document.get("status") in {"Approved", "IFC", "As-built"}:
        approver = identifier(document.get("approver"), "approver")
        if approver == document["issuer"]:
            raise RuleViolation("document issuer cannot approve their own revision")
        identifier(document.get("file"), "file")
    if document.get("status") == "Superseded" and document.get("is_current"):
        raise RuleViolation("superseded document cannot be current")


def current_ifc(project, document_code, documents):
    """Only exactly one valid IFC revision can be returned; ambiguity blocks."""
    project = identifier(project, "project")
    document_code = identifier(document_code, "document_code")
    candidates = []
    identities = set()
    for document in documents:
        _document_shape(document, project)
        if document["name"] in identities:
            raise RuleViolation("duplicate document identity")
        identities.add(document["name"])
        if document["document_code"] == document_code and document["status"] == "IFC":
            if document.get("is_current") is False or document.get("is_current") == 0:
                continue
            candidates.append(document)
    if len(candidates) > 1:
        raise RuleViolation("multiple IFC revisions: reconcile current revision before construction")
    return candidates[0] if candidates else None


def validate_document_transition(document, actor, permitted_projects, *, previous=None, can_approve=False, supersedes=None):
    actor = identifier(actor, "actor")
    project = check_scope(document.get("project"), permitted_projects)
    _document_shape(document, project)
    status = document["status"]
    if previous is None:
        if status != "Draft" or document["issuer"] != actor:
            raise RuleViolation("new document revisions must begin as an attributable draft")
    else:
        _document_shape(previous, project)
        for field in ("name", "project", "document_code", "revision", "issuer", "supersedes"):
            if document.get(field) != previous.get(field):
                raise RuleViolation(f"document {field} is immutable; create a new revision")
        if status not in DOCUMENT_TRANSITIONS[previous["status"]]:
            raise RuleViolation("invalid document transition")
        if previous["status"] in {"Approved", "IFC", "As-built"} and document.get("file") != previous.get("file"):
            raise RuleViolation("approved file cannot be overwritten; issue a new revision")
    if status in {"Approved", "IFC", "As-built", "Superseded"}:
        if can_approve is not True:
            raise RuleViolation("document status change requires authorized approval")
        if status != "Superseded" and document["approver"] != actor:
            raise RuleViolation("approver must be the authenticated actor")
    if document.get("supersedes"):
        if supersedes is None or supersedes.get("name") != document["supersedes"]:
            raise RuleViolation("superseded revision must be loaded from the system of record")
        _document_shape(supersedes, project)
        if supersedes["name"] == document["name"] or supersedes["document_code"] != document["document_code"] or supersedes["revision"] == document["revision"]:
            raise RuleViolation("invalid replaced document revision")
    return dict(document)


NCR_TRANSITIONS = {
    "Open": {"Assigned", "Escalated"},
    "Assigned": {"Corrective Action", "Escalated"},
    "Corrective Action": {"Pending Verification", "Escalated"},
    "Pending Verification": {"Closed", "Rejected correction", "Escalated"},
    "Rejected correction": {"Corrective Action", "Escalated"},
    "Escalated": {"Assigned", "Corrective Action", "Pending Verification"},
    "Closed": set(),
}


def validate_ncr_transition(ncr, actor, permitted_projects, *, previous=None, can_close=False):
    actor = identifier(actor, "actor")
    project = check_scope(ncr.get("project"), permitted_projects)
    for field in ("name", "requirement", "defect", "responsible"):
        identifier(ncr.get(field), field)
    if ncr.get("severity") not in {"Low", "Medium", "High", "Critical"}:
        raise RuleViolation("invalid NCR severity")
    calendar_date(ncr.get("due_date"), "due_date")
    status = ncr.get("status")
    if status not in NCR_TRANSITIONS:
        raise RuleViolation("invalid NCR status")
    if previous is None:
        if status != "Open" or ncr.get("reported_by") != actor:
            raise RuleViolation("new NCR must be Open and attributed to authenticated reporter")
    else:
        same_project(previous, project)
        if ncr["name"] != previous.get("name") or ncr.get("reported_by") != previous.get("reported_by"):
            raise RuleViolation("NCR identity and reporter are immutable")
        if previous.get("status") not in NCR_TRANSITIONS or status not in NCR_TRANSITIONS[previous["status"]]:
            raise RuleViolation("invalid NCR transition")
        if ncr["severity"] != previous.get("severity") and can_close is not True:
            raise RuleViolation("NCR severity change requires authorized QA review")
        if ncr["severity"] != previous.get("severity"):
            identifier(ncr.get("severity_change_reason"), "severity_change_reason")
        if previous["status"] == "Pending Verification" and status == "Closed":
            for field in ("responsible", "corrected_by", "corrective_action", "before_evidence", "after_evidence"):
                if ncr.get(field) != previous.get(field):
                    raise RuleViolation("submitted corrective action cannot change during closure")
    if status in {"Pending Verification", "Closed"}:
        identifier(ncr.get("corrective_action"), "corrective_action")
        if not evidence_present(ncr.get("before_evidence")) or not evidence_present(ncr.get("after_evidence")):
            raise RuleViolation("NCR correction requires before and after evidence")
    if status == "Closed":
        if can_close is not True or ncr.get("closure_verifier") != actor:
            raise RuleViolation("NCR closure requires authenticated authorized QA verification")
        if actor == ncr["responsible"] or actor == ncr.get("corrected_by"):
            raise RuleViolation("corrective action cannot be self-verified")
        identifier(ncr.get("closure_verification"), "closure_verification")
    return dict(ncr)


def validate_hold_release(hold, actor, permitted_projects, *, can_release=False):
    project = check_scope(hold.get("project"), permitted_projects)
    identifier(project, "project")
    actor = identifier(actor, "actor")
    for field in ("name", "work_package", "procedure_reference", "performed_by"):
        identifier(hold.get(field), field)
    if hold.get("status") != "Released" or hold.get("result") != "Passed":
        raise RuleViolation("hold point requires an explicit passed inspection to release")
    if can_release is not True or hold.get("verifier") != actor or actor == hold["performed_by"]:
        raise RuleViolation("hold release requires independent authorized verification")
    if not evidence_present(hold.get("evidence")):
        raise RuleViolation("hold release requires inspection evidence")
    return dict(hold)


def blocking_quality_items(project, holds=(), ncrs=()):
    """Never infer closure from absence of data; caller supplies all scoped items."""
    missing = []
    for hold in holds:
        same_project(hold, project)
        name = identifier(hold.get("name"), "name")
        if hold.get("status") not in {"Open", "Pending Inspection", "Failed", "Released"}:
            raise RuleViolation("invalid hold status")
        if hold["status"] != "Released":
            missing.append(f"hold:{name}")
    for ncr in ncrs:
        same_project(ncr, project)
        name = identifier(ncr.get("name"), "name")
        if ncr.get("status") not in NCR_TRANSITIONS or ncr.get("severity") not in {"Low", "Medium", "High", "Critical"}:
            raise RuleViolation("invalid NCR status or severity")
        if ncr["severity"] == "Critical" and ncr["status"] != "Closed":
            missing.append(f"ncr:{name}")
    return missing


def evaluate_commissioning(project, *, required_tests, tests, required_documents, documents, holds=(), ncrs=(), punchlist=()):
    """Assess dossier readiness against project-approved test/document lists.

    Test engineering limits and result calculations belong to approved test
    procedures, not hard-coded generic photovoltaic limits.
    """
    project = identifier(project, "project")
    if not required_tests or not required_documents:
        raise RuleViolation("commissioning requirements must be explicitly configured")
    if len(set(required_tests)) != len(required_tests) or len(set(required_documents)) != len(required_documents):
        raise RuleViolation("duplicate commissioning requirement")
    for item in tuple(required_tests) + tuple(required_documents):
        identifier(item, "commissioning requirement")
    missing = blocking_quality_items(project, holds, ncrs)
    history = {test["name"]: test for test in tests if test.get("name")}
    if len(history) != sum(bool(test.get("name")) for test in tests):
        raise RuleViolation("duplicate commissioning test identity")
    successors = {}
    for test in tests:
        target = test.get("supersedes")
        if not target:
            continue
        if not test.get("name") or target not in history or target in successors:
            raise RuleViolation("retest must replace one available result without a fork")
        prior = history[target]
        if prior.get("status") not in {"Passed", "Failed"}:
            raise RuleViolation("only a verified test result can be retested")
        for field in ("project", "test_code", "system_name", "work_package", "procedure_reference"):
            if test.get(field) != prior.get(field):
                raise RuleViolation("retest subject and approved procedure must remain unchanged")
        identifier(test.get("revision_reason"), "retest revision_reason")
        successors[target] = test["name"]
    for name in history:
        seen, current = set(), name
        while current:
            if current in seen:
                raise RuleViolation("cyclic test result history")
            seen.add(current)
            current = history[current].get("supersedes")
    by_test = {}
    for test in tests:
        same_project(test, project)
        if test.get("name") in successors:
            continue
        code = identifier(test.get("test_code"), "test_code")
        if code in by_test:
            raise RuleViolation("duplicate commissioning test result")
        by_test[code] = test
    for code in required_tests:
        test = by_test.get(code)
        if not test or test.get("status") != "Passed":
            missing.append(f"test:{code}")
            continue
        if not test.get("procedure_reference") or not test.get("verifier") or not test.get("performed_by") or test["verifier"] == test["performed_by"] or not evidence_present(test.get("evidence")):
            missing.append(f"test_evidence:{code}")
    by_document = {}
    for document in documents:
        _document_shape(document, project)
        if document["status"] == "As-built":
            code = document["document_code"]
            if code in by_document:
                raise RuleViolation("ambiguous as-built revision")
            by_document[code] = document
    for code in required_documents:
        if code not in by_document:
            missing.append(f"as_built:{code}")
    for item in punchlist:
        same_project(item, project)
        if item.get("status") != "Closed":
            missing.append(f"punchlist:{identifier(item.get('name'), 'name')}")
    return {"project": project, "ready": not missing, "missing": missing}


def validate_commissioning_acceptance(dossier, assessment, *, actor, permitted_projects, can_accept=False):
    project = check_scope(dossier.get("project"), permitted_projects)
    same_project(assessment, project)
    actor = identifier(actor, "actor")
    if can_accept is not True or dossier.get("accepted_by") != actor:
        raise RuleViolation("commissioning acceptance requires authorized authenticated approval")
    if actor == identifier(dossier.get("prepared_by"), "prepared_by"):
        raise RuleViolation("commissioning dossier cannot be self-accepted")
    if assessment.get("ready") is not True or assessment.get("missing"):
        raise RuleViolation("commissioning acceptance is blocked by incomplete requirements")
    if not evidence_present(dossier.get("acceptance_evidence")):
        raise RuleViolation("commissioning acceptance requires acceptance evidence")
    return dict(dossier)
