"""Frozen source-backed daily reports and evidenced RFI/blocker resolution."""
from __future__ import annotations

import hashlib
import json

import frappe

from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain.controls import calendar_date, evidence_present, identifier, number
from uranos_project_os.services.common import require_post, scoped_doc

REPORT_ROLES = ("Team Lead", "Site Controller", "Project Manager")
COORDINATOR_ROLES = ("Site Controller", "Project Manager", "Engineering Director")
OPERATIONAL_ROLES = (*REPORT_ROLES, "Civil Director", "Electrical Execution Manager", "Storekeeper",
                     "Procurement Logistics", "QA QC", "HSE", "Engineering Director")
SUMMARY_FIELDS = ("progress_summary", "stock_summary", "blockers_summary", "qa_hse_summary")


def _locked(doctype, name):
    initial = scoped_doc(doctype, name)
    scoped_doc("Project", initial.project, lock=True)
    return scoped_doc(doctype, name, lock=True)


def _result(doc, **extra):
    return {"doctype": doc.doctype, "name": doc.name, "status": doc.status,
            "modified": str(doc.modified), **extra}


def _save(doc):
    with authorized_transition():
        doc.save(ignore_permissions=True)
    return _result(doc)


def _set_evidence(doc, field, evidence_files):
    if isinstance(evidence_files, str):
        try:
            evidence_files = json.loads(evidence_files)
        except (ValueError, TypeError):
            frappe.throw("Evidence must be a list of uploaded File identifiers")
    if not isinstance(evidence_files, list) or not 1 <= len(evidence_files) <= 20:
        frappe.throw("Between one and twenty persisted evidence files are required")
    files = [identifier(value, "evidence File") for value in evidence_files]
    if len(files) != len(set(files)):
        frappe.throw("Duplicate evidence files are not accepted")
    doc.set(field, [])
    for name in files:
        doc.append(field, {"file": name, "captured_by": frappe.session.user, "captured_at": frappe.utils.now()})
    security.validate_evidence(doc)


def _enabled_scoped_user(user, project, doctype):
    identifier(user, "responsible user")
    if user in {"Guest", "Administrator"} or not frappe.db.get_value("User", user, "enabled"):
        frappe.throw("An enabled individual business account is required")
    security.require_project(project, user=user, doctype=doctype)
    security.require_roles(*OPERATIONAL_ROLES, user=user)


def _rows(doctype, project, fields, *, filters=None, trusted_native=False):
    security.require_project(project)
    if trusted_native and doctype not in {"Stock Entry", "Purchase Receipt"}:
        frappe.throw("Unsupported nonfinancial ERP summary source")
    getter = frappe.get_all if trusted_native else frappe.get_list
    result, offset = [], 0
    while True:
        batch = getter(doctype, filters={**(filters or {}), "project": project}, fields=fields,
                       limit_start=offset, limit_page_length=1000, order_by="name asc")
        result.extend(batch)
        if len(batch) < 1000:
            return result
        offset += 1000


def _safe_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def effective_daily_progress(project, site, posting_date, entries, packages):
    """Portable adapter projection, not an alternate operational ledger.

    Quantities are kept by activity/UOM and immutable source reference. Verified
    corrections replace an ancestor; pending corrections never add to totals.
    The complete project history is required to resolve correction chains.
    """
    day = calendar_date(posting_date, "posting_date")
    records = {}
    for entry in entries:
        if entry.get("project") != project or entry.get("name") in records:
            raise ValueError("Progress history contains a cross-project or duplicate record")
        records[identifier(entry.get("name"), "progress name")] = entry
    replaced, successors = set(), {}
    for entry in entries:
        parent = entry.get("correction_of")
        if not parent:
            continue
        original = records.get(parent)
        if not original or original.get("status") != "Verified":
            raise ValueError("Correction requires its complete verified ancestor")
        for field in ("work_package", "activity", "zone", "baseline_version", "kit_issue", "cable_reel", "posting_date"):
            if str(entry.get(field) or "") != str(original.get(field) or ""):
                raise ValueError("Correction cannot change daily contribution identity")
        if entry.get("status") == "Verified":
            if parent in successors:
                raise ValueError("Correction history cannot fork")
            successors[parent] = entry["name"]
            replaced.add(parent)
    for name in records:
        seen, current = set(), name
        while current:
            if current in seen:
                raise ValueError("Correction history cannot cycle")
            seen.add(current)
            current = records[current].get("correction_of")
    verified, pending = [], []
    for entry in entries:
        if (entry["name"] in replaced or calendar_date(entry["posting_date"], "posting_date") != day or
                (entry.get("site") or site) != site):
            continue
        if entry.get("correction_of") and entry.get("status") != "Verified":
            continue
        wp = packages.get(entry.get("work_package"))
        if not wp or wp.get("project") != project or not wp.get("uom"):
            raise ValueError("Daily progress needs its project work package and UOM")
        reported = number(entry.get("qty_reported"), "reported quantity")
        quantity = number(entry.get("qty_verified") or 0, "verified quantity")
        if quantity > reported:
            raise ValueError("Verified quantity exceeds declaration")
        item = {field: entry.get(field) for field in ("name", "work_package", "activity", "zone", "crew",
            "reported_by", "verifier", "correction_of", "kit_issue", "cable_reel")}
        item.update(uom=wp["uom"], work_package_code=wp.get("code"), qty_reported=str(reported), qty_verified=str(quantity))
        if entry.get("status") == "Verified":
            if not entry.get("verifier") or entry["verifier"] == entry.get("reported_by"):
                raise ValueError("Official daily quantities require independent verification")
            verified.append(item)
        elif entry.get("status") in {"Reported", "Pending Verification"}:
            if quantity:
                raise ValueError("Unverified declaration cannot contain verified work")
            pending.append(item)
    return {"verified_installed": verified, "pending_declarations": pending,
            "quantity_basis": "per activity and UOM; no cross-unit quantity total"}


def _stock_summary(project, day):
    output = []
    sources = (
        ("Stock Entry", "Stock Entry Detail", ["name", "posting_date", "purpose"],
         ["name", "parent", "item_code", "transfer_qty", "stock_uom", "s_warehouse", "t_warehouse", "uranos_kit_issue", "uranos_reel"]),
        ("Purchase Receipt", "Purchase Receipt Item", ["name", "posting_date"],
         ["name", "parent", "item_code", "stock_qty", "stock_uom", "warehouse", "uranos_shipment", "uranos_container"]),
    )
    for doctype, childtype, fields, childfields in sources:
        parents = _rows(doctype, project, fields, filters={"posting_date": str(day), "docstatus": 1}, trusted_native=True)
        for start in range(0, len(parents), 500):
            group = parents[start:start+500]
            if not group:
                continue
            names = {row.name for row in group}
            children = frappe.get_all(childtype, filters={"parenttype": doctype, "parent": ["in", sorted(names)]},
                                      fields=childfields, limit_page_length=0)
            by_parent = {name: [] for name in names}
            for child in children:
                if child.parent not in names:
                    frappe.throw("Unexpected stock snapshot parent")
                # Hard field allowlist: no amount, rate, valuation or accounts.
                by_parent[child.parent].append({field: child.get(field) for field in childfields})
            output.extend({"doctype": doctype, "name": row.name, "posting_date": str(row.posting_date),
                           "purpose": row.get("purpose") or "Purchase Receipt", "items": by_parent[row.name]} for row in group)
    return {"submitted_erp_movements": output, "physical_progress_effect": "none"}


def _snapshot(doc):
    day = calendar_date(str(doc.posting_date), "posting_date")
    if day > frappe.utils.getdate():
        frappe.throw("A daily report cannot summarize a future date")
    profiles = _rows("URANOS Project Profile", doc.project, ["name", "site"])
    if len(profiles) != 1 or profiles[0].site != doc.site:
        frappe.throw("Daily report site must match the configured project profile")
    entries = _rows("URANOS Field Progress Entry", doc.project, ["name", "project", "work_package", "site", "activity",
        "zone", "crew", "posting_date", "baseline_version", "qty_reported", "qty_verified", "reported_by", "verifier",
        "correction_of", "kit_issue", "cable_reel", "status"])
    packages = {row.name: row for row in _rows("URANOS Work Package", doc.project, ["name", "project", "code", "uom"])}
    progress = effective_daily_progress(doc.project, doc.site, day, entries, packages)
    progress["as_of"] = frappe.utils.now()
    progress["reporting_date"] = str(day)
    for row in progress["verified_installed"]:
        source = scoped_doc("URANOS Field Progress Entry", row["name"])
        security.validate_evidence(source)
        if not evidence_present(source.as_dict().get("evidence")):
            frappe.throw("Verified daily progress is missing persisted evidence")
        row["evidence"] = [proof.file for proof in source.evidence]
    blockers = _rows("URANOS Blocker", doc.project, ["name", "title", "category", "severity", "status", "responsible",
        "opened_at", "target_resolution", "resolution_submitted_at", "resolved_at", "lost_hours"])
    ncrs = _rows("URANOS NCR", doc.project, ["name", "severity", "status", "requirement", "defect", "due_date"])
    inspections = _rows("URANOS Field Inspection", doc.project, ["name", "inspection_type", "posting_date", "status", "verifier"],
                        filters={"posting_date": str(day)})
    return {"progress_summary": _safe_json(progress), "stock_summary": _safe_json(_stock_summary(doc.project, day)),
            "blockers_summary": _safe_json({"as_of": frappe.utils.now(), "records": blockers}),
            "qa_hse_summary": _safe_json({"as_of": frappe.utils.now(), "ncrs": ncrs, "inspections": inspections,
                                          "hse_notes": doc.hse_notes or ""})}


def _snapshot_hash(doc):
    value = {field: doc.get(field) for field in (*SUMMARY_FIELDS, "name", "project", "site", "posting_date", "manpower",
        "equipment_summary", "weather", "hse_notes", "notes", "recorded_by", "snapshot_at", "submitted_by", "submitted_at")}
    value["evidence"] = [{"file": row.file, "caption": row.get("caption")} for row in doc.get("evidence", [])]
    return hashlib.sha256(_safe_json(value).encode()).hexdigest()


@frappe.whitelist(methods=["POST"])
def submit_daily_report(name):
    require_post()
    user = security.require_roles(*REPORT_ROLES)
    doc = _locked("URANOS Daily Site Report", name)
    if doc.status != "Draft" or doc.recorded_by != user:
        frappe.throw("Only the named author can submit their draft daily report")
    if type(doc.manpower) is bool or int(doc.manpower or 0) < 0:
        frappe.throw("Manpower must be a nonnegative integer")
    security.validate_evidence(doc)
    for field, value in _snapshot(doc).items():
        doc.set(field, value)
    doc.submitted_by, doc.submitted_at, doc.snapshot_at = user, frappe.utils.now(), frappe.utils.now()
    doc.status = "Submitted"
    doc.snapshot_hash = _snapshot_hash(doc)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def approve_daily_report(name):
    require_post()
    user = security.require_roles("Site Controller", "Project Manager")
    doc = _locked("URANOS Daily Site Report", name)
    if doc.status != "Submitted" or user in {doc.recorded_by, doc.submitted_by}:
        frappe.throw("Daily report approval requires an independent reviewer of a submitted snapshot")
    if not doc.snapshot_hash or doc.snapshot_hash != _snapshot_hash(doc):
        frappe.throw("Daily report snapshot integrity failed")
    security.validate_evidence(doc)
    doc.approved_by, doc.approved_at, doc.status = user, frappe.utils.now(), "Approved"
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def assign_rfi(name, assignee):
    require_post()
    security.require_roles("Engineering Director", "Project Manager")
    doc = _locked("URANOS RFI", name)
    if doc.status != "Open":
        frappe.throw("Only an open RFI can be assigned")
    _enabled_scoped_user(assignee, doc.project, doc.doctype)
    security.require_roles("Engineering Director", "Project Manager", "Civil Director", "Electrical Execution Manager", user=assignee)
    doc.assignee, doc.status = assignee, "Assigned"
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def answer_rfi(name, response, evidence_files):
    require_post()
    user = security.require_roles("Engineering Director", "Project Manager", "Civil Director", "Electrical Execution Manager")
    doc = _locked("URANOS RFI", name)
    if doc.status != "Assigned" or user != doc.assignee:
        frappe.throw("Only the named RFI assignee can submit an answer")
    doc.response = identifier(response, "RFI response")
    _set_evidence(doc, "answer_evidence", evidence_files)
    doc.answered_by, doc.answered_at, doc.status = user, frappe.utils.now(), "Answered"
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def close_rfi(name):
    require_post()
    user = security.require_roles("Engineering Director", "Project Manager", "Site Controller", "Team Lead")
    doc = _locked("URANOS RFI", name)
    if doc.status != "Answered" or user in {doc.assignee, doc.answered_by}:
        frappe.throw("RFI closure requires an independent reviewer of the evidenced answer")
    if user != doc.requester:
        security.require_roles("Engineering Director", "Project Manager")
    if not doc.response or not evidence_present(doc.as_dict().get("answer_evidence")):
        frappe.throw("RFI response and proof are required")
    security.validate_evidence(doc)
    doc.closed_by, doc.closed_at, doc.status = user, frappe.utils.now(), "Closed"
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def assign_blocker(name, responsible):
    require_post()
    security.require_roles(*COORDINATOR_ROLES)
    doc = _locked("URANOS Blocker", name)
    if doc.status != "Open":
        frappe.throw("Only an open blocker can be assigned")
    _enabled_scoped_user(responsible, doc.project, doc.doctype)
    doc.responsible, doc.status = responsible, "Assigned"
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def resolve_blocker(name, resolution, lost_hours, evidence_files):
    require_post()
    user = security.require_roles(*OPERATIONAL_ROLES)
    doc = _locked("URANOS Blocker", name)
    if doc.status != "Assigned" or doc.responsible != user or doc.resolution_submitted_at:
        frappe.throw("Only the named responsible user can submit an outstanding blocker resolution")
    doc.resolution = identifier(resolution, "resolution")
    doc.lost_hours = str(number(lost_hours, "lost hours"))
    _set_evidence(doc, "resolution_evidence", evidence_files)
    doc.resolved_by, doc.resolution_submitted_at = user, frappe.utils.now()
    # Remain Assigned: critical risk must not disappear before independent review.
    _save(doc)
    return _result(doc, pending_independent_review=True)


@frappe.whitelist(methods=["POST"])
def close_blocker(name):
    require_post()
    user = security.require_roles(*COORDINATOR_ROLES)
    doc = _locked("URANOS Blocker", name)
    if (doc.status != "Assigned" or not doc.resolution_submitted_at or not doc.resolution or
            user in {doc.responsible, doc.resolved_by} or not evidence_present(doc.as_dict().get("resolution_evidence"))):
        frappe.throw("Blocker closure requires independent review of an evidenced resolution")
    security.validate_evidence(doc)
    doc.closed_by, doc.closed_at, doc.resolved_at, doc.status = user, frappe.utils.now(), frappe.utils.now(), "Closed"
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def review_blocker_severity(name, severity, reason):
    require_post()
    security.require_roles(*COORDINATOR_ROLES)
    doc = _locked("URANOS Blocker", name)
    if doc.status not in {"Open", "Assigned"} or severity not in {"Low", "Medium", "High", "Critical"}:
        frappe.throw("An open blocker and explicit severity are required")
    doc.review_reason, doc.severity = identifier(reason, "review reason"), severity
    return _save(doc)
