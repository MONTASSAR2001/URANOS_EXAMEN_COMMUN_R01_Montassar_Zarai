"""Machine-readable project gates backed by measured state and human evidence."""
import frappe

from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain.controls import GATE_CONDITIONS, evaluate_stage_gate
from uranos_project_os.services.common import require_post, scoped_doc
from uranos_project_os.services.operations import _locked, _save


@frappe.whitelist(methods=["POST"])
def initialize_gates(project):
    require_post()
    security.require_roles("Engineering Director", "Project Manager")
    scoped_doc("Project", project, permission="write", lock=True)
    names = []
    for number, codes in GATE_CONDITIONS.items():
        existing = frappe.db.get_value("URANOS Stage Gate", {"project": project, "gate_number": number}, "name")
        if existing:
            names.append(existing)
            continue
        doc = frappe.get_doc({"doctype": "URANOS Stage Gate", "project": project, "gate_number": number,
            "title": f"Gate {number}", "status": "Draft", "checklist": [{"code": code, "required": 1,
                "description": code.replace("_", " ")} for code in codes]})
        doc.insert()
        names.append(doc.name)
    return {"project": project, "gates": names}


@frappe.whitelist(methods=["POST"])
def attest_condition(name, code, evidence_file, note):
    require_post()
    user = security.require_roles("Engineering Director", "Project Manager")
    gate = _locked("URANOS Stage Gate", name)
    if gate.status == "Approved":
        frappe.throw("Approved gate evidence is immutable")
    matches = [row for row in gate.checklist if row.code == code]
    if len(matches) != 1 or code not in GATE_CONDITIONS.get(gate.gate_number, ()) or not note:
        frappe.throw("An exact gate condition and attestation note are required")
    row = matches[0]
    row.evidence_file, row.result = evidence_file, note
    row.verified_by, row.verified_at, row.completed = user, frappe.utils.now(), 1
    security.validate_evidence(gate)
    return _save(gate)


def _assessment(gate, approval_user=None):
    project = gate.project
    conditions = {}
    for row in gate.checklist:
        if row.code in conditions:
            frappe.throw("Duplicate gate condition")
        conditions[row.code] = bool(row.completed and row.verified_by and row.evidence_file)
    profiles = frappe.get_list("URANOS Project Profile", filters={"project": project}, fields=["name"], limit_page_length=2)
    profile = scoped_doc("URANOS Project Profile", profiles[0].name) if len(profiles) == 1 else None
    baseline = scoped_doc("URANOS Baseline", profile.current_baseline) if profile and profile.current_baseline else None
    wps = [scoped_doc("URANOS Work Package", row.work_package) for row in baseline.packages] if baseline and baseline.status == "Approved" else []
    def provided(value):
        return bool(value and str(value).strip() != "A COMPLETER")
    conditions.update({
        "project_identity": bool(profile and provided(profile.short_code)),
        "site_location": bool(profile and provided(profile.site) and provided(profile.governorate)),
        "capacity": bool(profile and (profile.capacity_ac_mw or 0) > 0),
        "client": bool(profile and provided(profile.client_reference)),
        "responsible_people": bool(profile and profile.project_manager and profile.site_controller),
        "scope": bool(profile and provided(profile.scope)),
        "approved_baseline": bool(baseline and baseline.status == "Approved"),
        "warehouses": bool(frappe.db.exists("Warehouse", {"uranos_project": project, "is_group": 0})),
        "work_package_template": bool(wps and baseline),
    })
    # Actual verified physical quantities override any manual attestation.
    quantity_gate_codes = {"piling_scope_verified": "WP-030", "structures_verified": "WP-040",
        "modules_verified": "WP-050", "dc_scope_verified": "WP-060", "inverters_installed_verified": "WP-070",
        "trenches_verified": "WP-080", "cables_verified": "WP-090", "station_scope_verified": "WP-100",
        "mv_scope_verified": "WP-120", "civil_scope_verified": "WP-020"}
    if any(key in GATE_CONDITIONS.get(gate.gate_number, ()) for key in quantity_gate_codes):
        from uranos_project_os.services.api import _progress
        progress = _progress(project)
        actual = {row["work_package"]: row["completion_percent"] for row in progress["work_packages"]}
        for condition, wp_code in quantity_gate_codes.items():
            matches = [wp for wp in wps if wp.code == wp_code and baseline and wp.baseline_version == baseline.version]
            conditions[condition] = bool(matches and all(actual.get(wp.name, 0) >= 100 for wp in matches))
    documents = [scoped_doc("URANOS Document Register", row.name).as_dict() for row in frappe.get_list("URANOS Document Register", filters={"project": project}, fields=["name"], limit_page_length=0)]
    required_ifc = sorted({row.document_code for wp in wps for row in wp.required_documents if row.mandatory})
    completed = [row.gate_number for row in frappe.get_list("URANOS Stage Gate", filters={"project": project, "status": "Approved"}, fields=["gate_number"], limit_page_length=0)]
    holds = frappe.get_list("URANOS Hold Point", filters={"project": project}, fields=["name", "project", "status"], limit_page_length=0)
    ncrs = frappe.get_list("URANOS NCR", filters={"project": project}, fields=["name", "project", "status", "severity"], limit_page_length=0)
    if gate.gate_number in {14, 15}:
        from uranos_project_os.services.quality import _dossier_assessment
        dossiers = [scoped_doc("URANOS Commissioning Dossier", row.name) for row in frappe.get_list(
            "URANOS Commissioning Dossier", filters={"project": project}, fields=["name"], limit_page_length=0)]
        assessments = [_dossier_assessment(doc) for doc in dossiers]
        # Commissioning/handover cannot be made green by a generic attestation.
        conditions["commissioning_tests_passed"] = bool(assessments) and all(
            not any(reason.startswith("test") for reason in item["missing"]) for item in assessments)
        conditions["commissioning_documents_complete"] = bool(assessments) and all(
            not any(reason.startswith("as_built:") for reason in item["missing"]) for item in assessments)
        conditions["as_built_complete"] = conditions["commissioning_documents_complete"]
        conditions["punchlist_resolved"] = bool(assessments) and all(
            not any(reason.startswith("punchlist:") for reason in item["missing"]) for item in assessments)
        conditions["handover_accepted"] = bool(dossiers) and all(doc.status in {"Accepted", "Closed"} for doc in dossiers)
        conditions["residual_stock_reconciled"] = not any((
            frappe.db.exists("URANOS Kit Issue", {"project": project, "status": ["in", ["Issued", "Partially Used", "Variance Review", "Reconciled"]]}),
            frappe.db.exists("URANOS Cable Reel", {"project": project, "status": ["in", ["Available", "In Use", "Reconciliation"]]}),
            frappe.db.exists("URANOS Stock Disposition", {"project": project, "status": ["in", ["Pending Approval", "Approved"]]}),
        ))
    approvals = [{"project": project, "gate": gate.gate_number, "status": "Approved",
                  "approved_by": approval_user, "requested_by": gate.owner}] if approval_user else []
    return evaluate_stage_gate(project, gate.gate_number, conditions, completed_gates=completed,
        required_ifc_codes=required_ifc if gate.gate_number == 1 else (), documents=documents,
        holds=holds, ncrs=ncrs, approvals=approvals, required_approvals=1)


@frappe.whitelist()
def readiness(name):
    return _assessment(scoped_doc("URANOS Stage Gate", name))


@frappe.whitelist(methods=["POST"])
def approve_gate(name):
    require_post()
    user = security.require_roles("Engineering Director")
    gate = _locked("URANOS Stage Gate", name)
    if gate.status == "Approved":
        frappe.throw("Gate is already approved")
    security.validate_evidence(gate)
    assessment = _assessment(gate, approval_user=user)
    if not assessment["ready"]:
        frappe.throw("Gate conditions missing: " + ", ".join(assessment["missing"]))
    gate.status, gate.approved_by, gate.approved_at = "Approved", user, frappe.utils.now()
    return _save(gate)
