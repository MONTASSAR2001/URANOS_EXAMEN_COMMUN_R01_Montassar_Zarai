"""Generate committed Frappe schemas. Changes to this source require regeneration.

No operational data is generated. No defaults authorize financial/stock variance.
Run with Python from repository root; --check detects schema drift without writes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "apps/uranos_project_os/uranos_project_os/uranos_project_os/doctype"
PREFIX = "URANOS "
ROLES = (
    "Executive", "Engineering Director", "Civil Director", "Electrical Execution Manager",
    "Project Manager", "Site Controller", "Storekeeper", "Procurement Logistics", "QA QC",
    "HSE", "Digital Admin", "Finance Controller", "Read Only Auditor", "Team Lead",
)
OPERATIONAL = tuple(r for r in ROLES if r != "Digital Admin")
OPERATIONAL_WRITERS = tuple(r for r in OPERATIONAL if r not in ("Finance Controller", "Read Only Auditor"))
FINANCE = ("Executive", "Finance Controller")
ENGINEERING = ("Engineering Director", "Project Manager")
STOCK = ("Storekeeper", "Project Manager")
LOGISTICS = ("Procurement Logistics", "Project Manager")


def field(name, kind="Data", options=None, required=False, **kw):
    result = {"fieldname": name, "label": name.replace("_", " ").title(), "fieldtype": kind}
    if options is not None:
        result["options"] = options
    if required:
        result["reqd"] = 1
    return result | kw


def link(name, target, required=False, **kw):
    return field(name, "Link", target, required, **kw)


def select(name, choices, default=None, **kw):
    return field(name, "Select", "\n".join(choices), default=default or choices[0], **kw)


def qty(name, **kw):
    return field(name, "Float", precision="6", **kw)


def table(name, target):
    return field(name, "Table", PREFIX + target)


def status(*choices):
    return select("status", choices, in_list_view=1)


PROJECT = link("project", "Project", True, in_list_view=1, in_standard_filter=1)
WP = link("work_package", PREFIX + "Work Package", in_standard_filter=1)
EVIDENCE = table("evidence", "Evidence")
PROVENANCE = [field("sync_uuid", unique=1, read_only=1, no_copy=1), link("recorded_by", "User", read_only=1)]


def permissions(writers=(), readers=OPERATIONAL, finance=False, extra_roles=()):
    out = []
    if finance:
        readers = tuple(dict.fromkeys((*readers, *FINANCE)))
    for role in dict.fromkeys((*readers, *writers)):
        row = {"role": PREFIX + role, "read": 1, "select": 1}
        if role in writers:
            row.update(create=1, write=1)
        out.append(row)
    if finance:
        out.extend({"role": PREFIX+r, "permlevel": 1, "read": 1, "write": 1} for r in FINANCE)
    for r in extra_roles:
        out.append(dict(r))
    return out


SCHEMAS = {}


def define(name, fields, writers=(), readers=OPERATIONAL, project=True, child=False,
           finance=False, submittable=False, autoname="hash", extra_roles=()):
    name = PREFIX + name
    fields = ([PROJECT.copy()] if project and not child else []) + fields
    SCHEMAS[name] = {
        "doctype": "DocType", "name": name, "module": "URANOS Project OS", "custom": 0,
        "autoname": autoname, "engine": "InnoDB", "track_changes": 1,
        "allow_rename": 0, "is_submittable": int(submittable), "istable": int(child),
        "field_order": [f["fieldname"] for f in fields], "fields": fields,
        "permissions": [] if child else permissions(writers, readers, finance, extra_roles),
        "sort_field": "modified", "sort_order": "DESC",
    }


define("Evidence", [link("file", "File", True), field("caption"), field("captured_at", "Datetime"),
                    link("captured_by", "User", read_only=1)], child=True)
define("Kit Item", [link("item_code", "Item", True), qty("qty_per_unit", required=True),
                    link("uom", "UOM", True), select("risk_class", ("R1", "R2", "R3", "R4")),
                    qty("tolerance_percent"), field("returnable", "Check"), field("batch_required", "Check"),
                    field("serial_required", "Check")], child=True)
define("Reconciliation Item", [link("item_code", "Item", True), qty("issued_qty", read_only=1),
                              qty("installed_qty", read_only=1), qty("returned_qty", read_only=1),
                              qty("approved_scrap_qty", read_only=1), qty("variance", read_only=1),
                              qty("approved_variance_qty", read_only=1),
                              field("reason", "Small Text"), link("approval", PREFIX+"Approval")], child=True)
define("Checklist Item", [field("code", required=True), field("description", "Small Text"),
                         field("required", "Check", default="1"), field("completed", "Check"),
                         link("verified_by", "User", read_only=1), field("verified_at", "Datetime", read_only=1),
                         link("document", PREFIX+"Document Register"), link("inspection", "Quality Inspection"),
                         field("acceptance_reference"), field("result", "Small Text"),
                         field("procedure_reference"), link("performed_by", "User"),
                         status("Pending", "Passed", "Failed"), link("evidence_file", "File")], child=True)
define("Document Requirement", [field("document_code", required=True), field("required_status", default="IFC"),
                               field("mandatory", "Check", default="1")], child=True)
define("Purchase Order Link", [link("purchase_order", "Purchase Order", True)], child=True)
define("Baseline Item", [WP, field("code", required=True), qty("qty_planned", required=True),
                        qty("weight", required=True), link("uom", "UOM"), field("baseline_start", "Date"),
                        field("baseline_finish", "Date")], child=True)
define("Impacted Object", [link("reference_doctype", "DocType", True),
                          field("reference_name", "Dynamic Link", "reference_doctype", True),
                          field("impact", "Small Text")], child=True)

define("Project Profile", [field("short_code", required=True, unique=1), field("site", required=True),
                          field("governorate"), qty("capacity_ac_mw"), qty("capacity_dc_mwp"),
                          field("site_location", "Geolocation"), link("project_manager", "User"),
                          link("site_controller", "User"), field("baseline_start", "Date"),
                          field("baseline_finish", "Date"), link("current_baseline", PREFIX+"Baseline", read_only=1),
                          status("Draft", "Active", "On Hold", "Commissioning", "Completed", "Cancelled"),
                          field("scope", "Text"), field("client_reference"),
                          select("risk_level", ("Unassessed", "Low", "Medium", "High", "Critical"))], ENGINEERING)
define("Baseline", [field("version", required=True), link("supersedes", PREFIX+"Baseline"),
                    link("change_request", PREFIX+"Change Request"), table("packages", "Baseline Item"),
                    status("Draft", "Pending Approval", "Approved", "Superseded"),
                    link("approved_by", "User", read_only=1), field("approved_at", "Datetime", read_only=1),
                    field("revision_reason", "Small Text")], ENGINEERING)
define("Work Package", [field("code", required=True), field("title", required=True), field("site"),
                        field("discipline", required=True), link("uom", "UOM", True),
                        qty("qty_planned", required=True), qty("weight", required=True),
                        field("baseline_version", required=True), link("baseline", PREFIX+"Baseline"),
                        field("baseline_start", "Date"), field("baseline_finish", "Date"),
                        select("criticality", ("Normal", "High", "Critical")),
                        status("Planned", "Ready", "In Progress", "Blocked", "Completed", "Cancelled"),
                        table("required_documents", "Document Requirement"),
                        field("material_ready", "Check", read_only=1), field("access_ready", "Check"),
                        field("baseline_approved", "Check", read_only=1)], ENGINEERING)
define("Activity Template", [field("activity_code", required=True, unique=1), field("title", required=True),
                             link("uom", "UOM", True), link("source_bom", "BOM"),
                             table("checks", "Checklist Item"), field("evidence_required", "Check"),
                             qty("tolerance_percent"), field("declarant_role"), field("verifier_role"),
                             field("segregation_required", "Check", default="1")], ENGINEERING)
define("Field Progress Entry", [WP | {"reqd": 1}, field("activity", required=True), field("site"),
                                field("zone", required=True), field("crew", required=True),
                                field("posting_date", "Date", required=True),
                                qty("qty_reported", required=True), qty("qty_verified", read_only=1),
                                field("baseline_version", required=True), link("reported_by", "User", read_only=1),
                                link("verifier", "User", read_only=1), field("verified_at", "Datetime", read_only=1),
                                status("Draft", "Reported", "Pending Verification", "Verified", "Rejected", "Cancelled"),
                                link("correction_of", PREFIX+"Field Progress Entry"), field("revision_reason", "Small Text"),
                                field("rejection_reason", "Small Text", read_only=1),
                                link("kit_issue", PREFIX+"Kit Issue"), link("cable_reel", PREFIX+"Cable Reel"),
                                field("notes", "Small Text"), EVIDENCE, *PROVENANCE],
       ("Team Lead", "Site Controller", "Civil Director", "Electrical Execution Manager", "Project Manager"))
define("Material Kit Template", [field("kit_code", required=True), field("kit_version", required=True),
                                 field("activity", required=True), link("source_bom", "BOM", True),
                                 link("output_uom", "UOM", read_only=1),
                                 qty("bom_output_qty", read_only=1), table("items", "Kit Item"),
                                 status("Draft", "Pending Approval", "Approved", "Superseded"),
                                 link("approved_by", "User", read_only=1), field("approved_at", "Datetime", read_only=1)], ENGINEERING)
define("Kit Issue", [WP, field("site"), field("crew", required=True), field("activity", required=True),
                     field("zone"), link("kit_template", PREFIX+"Material Kit Template", True),
                     field("kit_version", read_only=1), qty("qty_kits", required=True),
                     link("from_warehouse", "Warehouse", True), link("to_warehouse", "Warehouse", True),
                     link("stock_entry", "Stock Entry", read_only=1), link("issued_by", "User", read_only=1),
                     link("received_by", "User"),
                     status("Draft Request", "Approved", "Issued", "Partially Used", "Variance Review", "Reconciled", "Closed", "Cancelled"),
                     field("notes", "Small Text"), EVIDENCE, *PROVENANCE], (*STOCK, "Team Lead"))
define("Kit Reconciliation", [link("kit_issue", PREFIX+"Kit Issue", True),
                              table("items", "Reconciliation Item"), link("return_stock_entry", "Stock Entry"),
                              link("scrap_stock_entry", "Stock Entry"),
                              link("consumption_stock_entry", "Stock Entry", read_only=1),
                              table("verified_progress", "Impacted Object"),
                              status("Draft", "Variance Review", "Approved", "Closed"),
                              field("reason", "Small Text"), link("approved_by", "User", read_only=1), EVIDENCE], STOCK)
define("Kit Return", [link("kit_issue", PREFIX+"Kit Issue", True), link("item_code", "Item", True),
                      qty("returned_qty", required=True), link("uom", "UOM", True), field("notes", "Small Text"),
                      link("to_warehouse", "Warehouse", True),
                      link("stock_entry", "Stock Entry", read_only=1),
                      status("Draft", "Pending Approval", "Posted", "Rejected"), EVIDENCE, *PROVENANCE], (*STOCK, "Team Lead"))
define("Cable Reel", [field("reel_id", required=True, unique=1), link("item_code", "Item", True),
                      field("manufacturer_ref"), link("batch_no", "Batch"), qty("original_length", required=True),
                      qty("current_expected_length", read_only=1), qty("measured_length"),
                      link("warehouse", "Warehouse", True), status("Draft", "Available", "In Use", "Reconciliation", "Closed"),
                      link("purchase_receipt", "Purchase Receipt"), field("purchase_receipt_item"),
                      link("receipt_release_stock_entry", "Stock Entry", read_only=1),
                      link("receipt_release_inspection", "Quality Inspection", read_only=1),
                      link("consumption_stock_entry", "Stock Entry", read_only=1), EVIDENCE], STOCK)
define("Cable Reel Movement", [link("reel", PREFIX+"Cable Reel", True), WP,
                               link("issue_movement", PREFIX+"Cable Reel Movement"),
                               select("movement_type", ("Issue", "Return", "Scrap", "Reconcile")),
                               field("posting_date", "Date", required=True), link("from_warehouse", "Warehouse"),
                               link("to_warehouse", "Warehouse"), qty("issued_length"), qty("installed_length"),
                               qty("scrap_length"), qty("returned_length"), field("destination_circuit"), field("zone"),
                               link("stock_entry", "Stock Entry", read_only=1), link("performed_by", "User", read_only=1),
                               link("approval", PREFIX+"Approval"), status("Draft", "Posted", "Cancelled"), EVIDENCE, *PROVENANCE], STOCK)
define("Shipment", [link("supplier", "Supplier", True), table("purchase_orders", "Purchase Order Link"),
                    field("incoterm"), field("forwarder"), field("origin"), field("destination"),
                    field("etd", "Datetime"), field("eta_initial", "Datetime"), field("eta_revised", "Datetime"),
                    field("need_by", "Date"), field("delay_alert_days", "Int"),
                    select("criticality", ("Normal", "High", "Critical")),
                    status("Planned", "PO Confirmed", "Production", "Ready for Pickup", "At Origin Port", "Departed", "In Transit", "Destination Port", "Customs", "Released", "Trucking", "Site Received", "Closed"),
                    link("purchase_receipt", "Purchase Receipt"), field("packing_allocations", "Long Text"),
                    table("required_documents", "Document Requirement"), EVIDENCE], LOGISTICS)
define("Container", [link("shipment", PREFIX+"Shipment", True), field("container_number", required=True),
                     field("seal_number"), field("container_type"), field("bill_of_lading"), qty("gross_weight"),
                     field("content_summary", "Small Text"), status("Planned", "Sealed", "In Transit", "Customs", "Received", "Closed")], LOGISTICS)
define("Shipment Milestone", [link("shipment", PREFIX+"Shipment", True), link("container", PREFIX+"Container"),
                              field("milestone_type", required=True), field("planned_at", "Datetime"),
                              field("actual_at", "Datetime"), select("source_type", ("Manual Verified", "API", "Forwarder Email", "Carrier Portal")),
                              field("source_timestamp", "Datetime", required=True), field("provider_event_id", unique=1),
                              field("payload_hash", read_only=1), field("location"), field("provider"),
                              field("source_reference"), field("eta", "Datetime"), link("purchase_receipt", "Purchase Receipt"),
                              link("recorded_by", "User", read_only=1), field("event_payload", "Long Text", read_only=1), EVIDENCE], LOGISTICS)
define("Document Register", [WP, field("document_code", required=True), field("title", required=True),
                             field("discipline", required=True), field("revision", required=True),
                             status("Draft", "Internal Review", "Approved", "IFC", "Superseded", "As-built"),
                             link("file", "File", True), link("issuer", "User", read_only=1),
                             link("approver", "User", read_only=1), field("approval_date", "Datetime", read_only=1),
                             link("supersedes", PREFIX+"Document Register"),
                             field("is_current", "Check", read_only=1), field("revision_reason", "Small Text")], ENGINEERING)
define("Blocker", [WP, field("activity"), field("title", required=True),
                   select("category", ("Material", "Logistics", "Document", "Access", "Crew", "Equipment", "Weather", "Quality", "Safety", "Administration", "Client Decision", "Other")),
                   select("severity", ("Low", "Medium", "High", "Critical")), field("opened_at", "Datetime", read_only=1),
                   link("reported_by", "User", read_only=1), link("responsible", "User", read_only=1),
                   field("target_resolution", "Datetime"), field("due_date", "Date"), field("resolved_at", "Datetime", read_only=1),
                   qty("lost_hours"), field("resolution", "Text", read_only=1), field("corrective_action", "Text"),
                   link("resolved_by", "User", read_only=1), field("resolution_submitted_at", "Datetime", read_only=1),
                   table("resolution_evidence", "Evidence"), link("closed_by", "User", read_only=1),
                   field("closed_at", "Datetime", read_only=1), field("review_reason", "Small Text", read_only=1),
                   status("Open", "In Progress", "Pending Verification", "Closed", "Ouvert", "En cours", "À vérifier", "Clôturé"), field("description", "Text"), EVIDENCE],
       OPERATIONAL_WRITERS,
       extra_roles=(
           {"role": "site_team", "read": 1, "select": 1, "create": 1, "write": 1},
           {"role": "engineer", "read": 1, "select": 1, "create": 1, "write": 1},
           {"role": "management", "read": 1, "select": 1},
       ))
define("RFI", [WP, field("question", "Text", required=True), table("documents", "Impacted Object"),
               link("requester", "User", read_only=1), link("assignee", "User", read_only=1), field("response", "Text", read_only=1),
               link("answered_by", "User", read_only=1), field("answered_at", "Datetime", read_only=1),
               table("answer_evidence", "Evidence"), link("closed_by", "User", read_only=1), field("closed_at", "Datetime", read_only=1),
               field("due_date", "Date"), field("impact", "Small Text"), status("Open", "Assigned", "Answered", "Closed"), EVIDENCE],
       ("Team Lead", "Site Controller", "Engineering Director", "Project Manager"))
define("NCR", [WP, select("severity", ("Low", "Medium", "High", "Critical")),
               link("source_inspection", "Quality Inspection"), field("requirement", "Small Text", required=True),
               field("defect", "Text", required=True), link("responsible", "User"), field("corrective_action", "Text"),
               field("due_date", "Date", required=True), link("closure_verifier", "User", read_only=1),
               field("closed_at", "Datetime", read_only=1), status("Open", "Assigned", "Corrective Action", "Pending Verification", "Closed", "Rejected correction", "Escalated"),
               link("reported_by", "User", read_only=1), link("corrected_by", "User", read_only=1),
               field("closure_verification", "Small Text", read_only=1),
               field("severity_change_reason", "Small Text"),
               table("before_evidence", "Evidence"), table("after_evidence", "Evidence"),
               EVIDENCE], ("QA QC", "Site Controller", "Project Manager"))
define("Field Inspection", [WP, field("activity"), field("zone", required=True),
                            field("inspection_type", required=True),
                            link("hold_point", PREFIX+"Hold Point"), field("procedure_reference"),
                            link("procedure_document", PREFIX+"Document Register"),
                            field("posting_date", "Date", required=True),
                            link("activity_template", PREFIX+"Activity Template"),
                            table("checklist", "Checklist Item"), field("notes", "Small Text"),
                            link("quality_inspection", "Quality Inspection", read_only=1),
                            link("verifier", "User", read_only=1),
                            status("Draft", "Pending Verification", "Accepted", "Rejected"), EVIDENCE, *PROVENANCE],
       ("Team Lead", "QA QC", "Site Controller", "Project Manager"))
define("QA Test Result", [WP, field("test_code", required=True), field("procedure_reference", required=True),
                          field("system_name", required=True),
                          link("supersedes", PREFIX+"QA Test Result"), field("revision_reason", "Small Text"),
                          link("performed_by", "User", read_only=1), link("verifier", "User", read_only=1),
                          field("tested_at", "Datetime"), field("verified_at", "Datetime", read_only=1),
                          field("result", "Small Text"), status("Pending", "Passed", "Failed"), EVIDENCE],
       ("QA QC", "Site Controller", "Electrical Execution Manager"))
define("Hold Point", [WP | {"reqd": 1}, field("activity"), field("zone", required=True),
                      field("requirement", "Small Text", required=True), field("procedure_reference", required=True),
                      link("procedure_document", PREFIX+"Document Register"),
                      link("performed_by", "User", read_only=1), link("verifier", "User", read_only=1),
                      link("inspection", PREFIX+"Field Inspection"), select("result", ("Pending", "Passed", "Failed")),
                      field("released_at", "Datetime", read_only=1),
                      status("Open", "Pending Inspection", "Failed", "Released"), EVIDENCE],
       ("QA QC", "Site Controller", "Project Manager"))
define("Change Request", [WP, field("description", "Text", required=True), field("reason", "Small Text", required=True),
                          link("requested_by", "User", read_only=1),
                          select("urgency", ("Normal", "High", "Critical")), field("technical_impact", "Text"),
                          field("schedule_impact_days", "Int"), field("cost_impact", "Currency", permlevel=1),
                          field("material_impact", "Text"), field("document_impact", "Text"), table("impacted_objects", "Impacted Object"),
                          link("policy", PREFIX+"Approval Policy", read_only=1, permlevel=1),
                          link("currency", "Currency", read_only=1, permlevel=1),
                          field("cost_assessed", "Check", read_only=1), link("cost_assessed_by", "User", read_only=1),
                          field("cost_assessment_hash", read_only=1),
                          field("scope_snapshot", "Long Text", read_only=1),
                          field("financial_approval_required", "Check", read_only=1), field("payload_hash", read_only=1),
                          field("proposed_solution", "Text"), link("technical_approver", "User", read_only=1),
                          link("financial_approver", "User", read_only=1),
                          link("implemented_by", "User", read_only=1), field("implementation_note", "Text", read_only=1),
                          link("verified_by", "User", read_only=1), table("verification_evidence", "Evidence"),
                          field("verification_note", "Text", read_only=1), field("decision_reason", "Small Text", read_only=1),
                          status("Proposed", "Impact Analysis", "Technical Approval", "Financial Approval", "Approved", "Rejected", "Implemented", "Verified", "Closed")],
       (*ENGINEERING, "Civil Director", "Electrical Execution Manager"), finance=True)
define("Daily Site Report", [field("site", required=True), field("posting_date", "Date", required=True),
                            field("manpower", "Int"), field("equipment_summary", "Small Text"), field("weather"),
                            field("progress_summary", "Text", read_only=1), field("stock_summary", "Text", read_only=1),
                            field("blockers_summary", "Text", read_only=1), field("qa_hse_summary", "Text", read_only=1),
                            field("hse_notes", "Text"), field("snapshot_preview", "HTML"),
                            field("snapshot_hash", read_only=1), field("snapshot_at", "Datetime", read_only=1),
                            link("submitted_by", "User", read_only=1), field("submitted_at", "Datetime", read_only=1),
                            link("approved_by", "User", read_only=1), field("approved_at", "Datetime", read_only=1),
                            field("notes", "Text"), link("pdf_snapshot", "File", read_only=1),
                            status("Draft", "Submitted", "Approved"), EVIDENCE, *PROVENANCE],
       ("Team Lead", "Site Controller", "Project Manager"))
define("Commissioning Dossier", [WP, field("system_name", required=True), table("required_tests", "Checklist Item"),
                                 table("required_documents", "Document Requirement"), table("punch_list", "Checklist Item"),
                                 link("accepted_by", "User", read_only=1), field("accepted_at", "Datetime", read_only=1),
                                 link("prepared_by", "User", read_only=1), table("acceptance_evidence", "Evidence"),
                                 status("Draft", "Testing", "Pending Acceptance", "Accepted", "Closed"), EVIDENCE],
       ("QA QC", "Site Controller", "Engineering Director", "Electrical Execution Manager", "Project Manager"))
define("Executive Alert", [field("rule", required=True), select("severity", ("Low", "Medium", "High", "Critical")),
                           field("message", "Small Text", required=True), field("generated_at", "Datetime", read_only=1),
                           link("responsible", "User"), field("acknowledged", "Check"),
                           link("reference_doctype", "DocType"), field("reference_name", "Dynamic Link", "reference_doctype"),
                           status("Open", "Acknowledged", "Resolved")], (), OPERATIONAL)
define("Delegation", [link("delegator", "User", True), link("delegate", "User", True),
                      link("role", "Role", True), field("valid_from", "Datetime", required=True),
                      field("valid_to", "Datetime", required=True), field("transaction_limit", "Currency", permlevel=1),
                      field("scope", "Small Text", required=True), link("approved_by", "User", read_only=1),
                      status("Draft", "Approved", "Expired", "Revoked")], FINANCE, FINANCE, finance=True)
define("Stage Gate", [field("gate_number", "Int", required=True), field("title", required=True),
                      table("checklist", "Checklist Item"), status("Draft", "Pending Approval", "Approved", "Blocked"),
                      link("approved_by", "User", read_only=1), field("approved_at", "Datetime", read_only=1)], ENGINEERING)
define("Approval Policy", [field("policy_code", required=True),
                           select("action", ("Stock Adjustment", "Cancellation", "Change Cost", "Delegation")),
                           field("currency", "Link", "Currency", True), field("threshold", "Currency", required=True, permlevel=1),
                           field("first_role", "Link", "Role", True), field("second_role", "Link", "Role", True),
                           field("enabled", "Check"), field("valid_from", "Date", required=True),
                           field("valid_to", "Date"), status("Draft", "Approved", "Retired"),
                           link("approved_by", "User", read_only=1)], FINANCE, FINANCE, finance=True)
define("Approval", [link("policy", PREFIX+"Approval Policy", True), link("reference_doctype", "DocType", True),
                    field("reference_name", "Dynamic Link", "reference_doctype", True),
                    field("action", required=True), field("payload_hash", required=True),
                    link("requester", "User", read_only=1), link("approver", "User", read_only=1),
                    field("approved_roles", "Small Text", read_only=1),
                    field("approved_at", "Datetime", read_only=1), field("reason", "Small Text", required=True)],
       (), FINANCE)
define("Stock Disposition", [link("kit_issue", PREFIX+"Kit Issue"), link("cable_reel", PREFIX+"Cable Reel"),
                             link("item_code", "Item", True),
                             select("kind", ("Scrap", "Variance", "Adjustment In", "Adjustment Out")),
                             qty("quantity", required=True), link("warehouse", "Warehouse", True),
                             link("currency", "Currency", True, read_only=1, permlevel=1),
                             field("valuation_rate", "Currency", read_only=1, permlevel=1),
                             field("amount", "Currency", read_only=1, permlevel=1),
                             field("reason", "Small Text", required=True), link("requester", "User", read_only=1),
                             field("requested_at", "Datetime", read_only=1), field("payload_hash", read_only=1),
                             link("policy", PREFIX+"Approval Policy", True), link("stock_entry", "Stock Entry", read_only=1),
                             status("Draft", "Pending Approval", "Approved", "Posted", "Rejected")],
       STOCK, OPERATIONAL, finance=True)
define("Offline Sync Receipt", [link("sync_user", "User", True, read_only=1), field("sync_uuid", required=True, read_only=1),
                                field("payload_hash", required=True, read_only=1), link("reference_doctype", "DocType", read_only=1),
                                field("reference_name", "Dynamic Link", "reference_doctype", read_only=1),
                                status("Accepted", "Pending", "Rejected"), field("result_json", "Long Text", read_only=1)],
       (), (), autoname="hash")
define("Offline Identity Key", [link("user", "User", True, unique=1),
                                field("encryption_key", "Password", required=True, no_copy=1)],
       (), (), project=False)
define("Project Cost", [WP, field("currency", "Link", "Currency", True),
                       field("budget", "Currency", permlevel=1), field("committed", "Currency", read_only=1, permlevel=1),
                       field("received", "Currency", read_only=1, permlevel=1), field("invoiced", "Currency", read_only=1, permlevel=1),
                       field("paid", "Currency", permlevel=1), field("forecast", "Currency", permlevel=1),
                       field("basis", "Small Text"), status("Draft", "Approved", "Revised")], FINANCE, FINANCE, finance=True)


def expected_files():
    for name, schema in SCHEMAS.items():
        slug = name.lower().replace(" ", "_")
        base = DEST / slug
        yield base / (slug+".json"), json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
        yield base / "__init__.py", ""
        cls = name.replace(" ", "")
        parent = "Document" if schema["istable"] else "UranosDocument"
        imported = "frappe.model.document" if schema["istable"] else "uranos_project_os.controllers"
        target_py = base / (slug + ".py")
        if target_py.exists():
            current_py = target_py.read_text(encoding="utf-8")
            if "pass\n" not in current_py or len(current_py.splitlines()) > 10:
                yield target_py, current_py
                continue
        yield target_py, f'"""{name} controller; business enforcement is shared."""\nfrom {imported} import {parent}\n\n\nclass {cls}({parent}):\n    pass\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    failures = []
    for path, data in expected_files():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != data:
                failures.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, encoding="utf-8", newline="\n")
    if failures:
        raise SystemExit("Schema drift:\n" + "\n".join(failures))
    print(f"{len(SCHEMAS)} DocTypes {'verified' if args.check else 'generated'}")


if __name__ == "__main__":
    main()
