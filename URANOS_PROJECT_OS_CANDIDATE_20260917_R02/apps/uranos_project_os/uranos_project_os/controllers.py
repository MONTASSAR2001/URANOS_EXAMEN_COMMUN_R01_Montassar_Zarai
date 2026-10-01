"""All normal Desk/REST writes pass these guards; trusted services own transitions."""
from contextlib import contextmanager
from contextvars import ContextVar
from decimal import Decimal, InvalidOperation

import frappe
from frappe.model.document import Document

from uranos_project_os import security

_transition = ContextVar("uranos_authorized_transition", default=False)


@contextmanager
def authorized_transition():
    """Private server capability. Call only after business validation, role/scope checks and locks.

    Never expose a whitelisted function that enters this context for arbitrary
    payloads. A client-supplied Document.flags value cannot enable it.
    """
    token = _transition.set(True)
    try:
        yield
    finally:
        _transition.reset(token)


def transition_is_authorized():
    return _transition.get()


INITIAL_STATES = {
    "URANOS Work Package": "Planned", "URANOS Kit Issue": "Draft Request",
    "URANOS Shipment": "Planned", "URANOS Container": "Planned", "URANOS Blocker": "Open",
    "URANOS RFI": "Open", "URANOS NCR": "Open", "URANOS Change Request": "Proposed",
    "URANOS Executive Alert": "Open", "URANOS Offline Sync Receipt": "Pending",
    "URANOS QA Test Result": "Pending", "URANOS Hold Point": "Open",
    "URANOS Project Profile": "Active",
}
PROTECTED = frozenset({
    "qty_verified", "verifier", "verified_at", "approved_by", "approved_at", "approver", "approval_date",
    "accepted_by", "accepted_at", "closure_verifier", "closed_at", "is_current", "current_baseline",
    "baseline_approved", "material_ready", "issued_by", "stock_entry", "current_expected_length",
    "performed_by", "technical_approver", "financial_approver", "resolved_at", "generated_at",
    "progress_summary", "stock_summary", "blockers_summary", "pdf_snapshot", "quality_inspection",
    "committed", "received", "invoiced", "sync_uuid", "payload_hash", "reference_name", "sync_user",
    "kit_version", "bom_output_qty", "output_uom",
    "corrected_by", "closure_verification", "released_at", "event_payload", "consumption_stock_entry", "rejection_reason",
    "receipt_release_stock_entry", "receipt_release_inspection",
})
IMMUTABLE_STATES = frozenset({"Verified", "Approved", "IFC", "Superseded", "As-built", "Accepted", "Closed", "Posted",
                              "Issued", "Partially Used", "Variance Review", "Reconciled", "Available", "In Use", "Released"})
SERVICE_ONLY = frozenset({"URANOS Approval", "URANOS Offline Sync Receipt", "URANOS Offline Identity Key",
                          "URANOS Executive Alert", "URANOS Shipment Milestone"})


class UranosDocument(Document):
    def before_insert(self):
        for field in ("recorded_by", "reported_by", "issuer", "requester", "requested_by", "prepared_by", "performed_by"):
            if self.meta.has_field(field):
                if not (transition_is_authorized() and self.get(field)):
                    self.set(field, frappe.session.user)
        if self.doctype == "URANOS Blocker":
            self.opened_at = frappe.utils.now()

    def validate(self):
        if self.doctype in security.SCOPED_FIELDS:
            security.validate_project_links(self)
            security.validate_evidence(self)
        _finite_quantities(self)
        self._guard_server_state()
        if self.doctype == "URANOS Field Progress Entry":
            if self.get("kit_issue") and self.get("cable_reel"):
                frappe.throw("Progress must reference at most one material allocation")
            reported = _decimal(self.qty_reported)
            verified = _decimal(self.qty_verified or 0)
            if reported < 0 or verified < 0 or verified > reported:
                frappe.throw("Verified quantity must be between zero and reported quantity")
            if verified and self.status != "Verified":
                frappe.throw("Only a Verified entry can hold verified quantity")
            if self.status == "Verified":
                if not self.verifier or self.verifier == self.reported_by:
                    frappe.throw("Verification requires an independent verifier")
                security.require_roles("Site Controller", user=self.verifier)
                security.require_project(self.project, user=self.verifier, doctype=self.doctype)

    def _guard_server_state(self):
        old = self.get_doc_before_save()
        if old:
            for actor in ("recorded_by", "reported_by", "issuer", "requester", "requested_by", "prepared_by", "performed_by"):
                if self.meta.has_field(actor) and self.get(actor) != old.get(actor):
                    frappe.throw("Original actor identity is immutable")
        if transition_is_authorized():
            return
        if self.doctype in SERVICE_ONLY:
            frappe.throw("This record is maintained by a controlled server service", frappe.PermissionError)
        if old and old.get("status") in IMMUTABLE_STATES:
            frappe.throw("Approved records are immutable; create an auditable correction or revision")
        if old and self.doctype == "URANOS Shipment" and old.status != "Planned":
            frappe.throw("Released shipment changes require the controlled tracking service")
        if old and self.doctype in {"URANOS QA Test Result", "URANOS Hold Point"} and old.status in {"Passed", "Failed", "Released"}:
            frappe.throw("A quality decision is immutable; create a controlled correction")
        if old and self.doctype == "URANOS Hold Point" and frappe.db.exists("URANOS Field Inspection", {"hold_point": self.name}):
            for fieldname in ("project", "work_package", "activity", "zone", "requirement", "procedure_reference", "procedure_document"):
                if old.get(fieldname) != self.get(fieldname):
                    frappe.throw("An inspected hold subject/procedure is immutable; create a reviewed replacement")
        if old and self.doctype == "URANOS Commissioning Dossier" and old.status in {"Testing", "Pending Acceptance"}:
            frappe.throw("Commissioning requirements and evidence require controlled, audited amendments")
        self._guard_support_workflows(old)
        if old and self.doctype == "URANOS NCR":
            if old.get("severity") != self.get("severity"):
                frappe.throw("NCR severity changes require the controlled QA review service")
            if old.status == "Pending Verification":
                for fieldname in ("responsible", "corrected_by", "corrective_action", "requirement", "defect", "due_date"):
                    if old.get(fieldname) != self.get(fieldname):
                        frappe.throw("Submitted NCR correction is immutable until reviewed")
                for fieldname in ("before_evidence", "after_evidence", "evidence"):
                    previous = [(row.file, row.get("caption"), str(row.get("captured_at"))) for row in old.get(fieldname, [])]
                    current = [(row.file, row.get("caption"), str(row.get("captured_at"))) for row in self.get(fieldname, [])]
                    if previous != current:
                        frappe.throw("Submitted NCR evidence is immutable until reviewed")
        if self.doctype == "URANOS Stock Disposition":
            if old and old.status != "Draft":
                frappe.throw("A requested disposition is immutable; submit a new controlled request")
            for fieldname in ("currency", "valuation_rate", "amount", "requested_at"):
                expected = old.get(fieldname) if old else None
                if self.get(fieldname) not in (None, "", 0) and self.get(fieldname) != expected:
                    frappe.throw("Disposition valuation and identity are assigned by the server")
            if bool(self.kit_issue) == bool(self.cable_reel):
                frappe.throw("A stock disposition must reference exactly one kit issue or cable reel")
        if old and old.get("baseline_approved"):
            for fieldname in ("code", "uom", "discipline", "title", "site", "criticality", "qty_planned", "weight", "baseline_version", "baseline", "baseline_start", "baseline_finish"):
                if old.get(fieldname) != self.get(fieldname):
                    frappe.throw("Approved baseline quantities and dates require a controlled revision")
            before = [(row.document_code, row.required_status, row.mandatory) for row in old.get("required_documents", [])]
            after = [(row.document_code, row.required_status, row.mandatory) for row in self.get("required_documents", [])]
            if before != after:
                frappe.throw("Approved drawing requirements require a controlled baseline revision")
        if old and self.doctype == "URANOS Field Progress Entry" and old.status in {"Reported", "Pending Verification"}:
            for fieldname in ("qty_reported", "activity", "zone", "crew", "posting_date", "baseline_version",
                              "work_package", "correction_of", "revision_reason", "kit_issue", "cable_reel"):
                if old.get(fieldname) != self.get(fieldname):
                    frappe.throw("A submitted declaration is immutable; use a controlled correction")
            previous = {(row.file, row.caption, str(row.captured_at)) for row in old.get("evidence", [])}
            current = {(row.file, row.caption, str(row.captured_at)) for row in self.get("evidence", [])}
            if previous != current:
                frappe.throw("Submitted evidence requires a controlled, audited amendment")
        if self.meta.has_field("status") and self.doctype != "URANOS Blocker":
            allowed = old.get("status") if old else INITIAL_STATES.get(self.doctype, "Draft")
            if self.get("status") != allowed:
                frappe.throw("State changes require the controlled workflow service", frappe.PermissionError)
        for fieldname in PROTECTED:
            if not self.meta.has_field(fieldname):
                continue
            if self.doctype == "URANOS Blocker" and fieldname in ("closed_at", "resolved_at"):
                continue
            # User-entered template version and a draft's legitimate dynamic link
            # are not authority. Guard kit issue snapshots, not template versions.
            if fieldname == "kit_version" and self.doctype == "URANOS Material Kit Template":
                continue
            if fieldname == "reference_name" and self.doctype not in SERVICE_ONLY:
                continue
            expected = old.get(fieldname) if old else None
            value = self.get(fieldname)
            if fieldname == "performed_by" and not old and value == frappe.session.user:
                continue
            if value != expected and value not in (None, "", 0):
                frappe.throw(f"{fieldname} is controlled by the server", frappe.PermissionError)
            if old and value != expected:
                frappe.throw(f"{fieldname} is controlled by the server", frappe.PermissionError)
        for row in self.get_all_children():
            if row.get("verified_by") or row.get("verified_at") or row.get("completed"):
                frappe.throw("Checklist verification requires the controlled server service")

    def on_trash(self):
        security.prevent_operational_delete(self)

    def _guard_support_workflows(self, old):
        protected = {
            "URANOS Change Request": {"cost_impact", "policy", "currency", "cost_assessed", "cost_assessed_by", "cost_assessment_hash",
                "scope_snapshot", "financial_approval_required", "implemented_by", "implementation_note", "verified_by", "verification_note", "decision_reason"},
            "URANOS Daily Site Report": {"qa_hse_summary", "snapshot_hash", "snapshot_at", "submitted_by", "submitted_at"},
            "URANOS RFI": {"assignee", "response", "answered_by", "answered_at", "closed_by"},
        }
        for field in protected.get(self.doctype, ()):
            expected = old.get(field) if old else None
            if self.get(field) != expected and (old or self.get(field) not in (None, "", 0)):
                frappe.throw(f"{field} requires the controlled workflow service", frappe.PermissionError)
        if old and ((self.doctype == "URANOS Daily Site Report" and old.status != "Draft") or
                    (self.doctype == "URANOS Change Request" and old.status not in {"Proposed", "Impact Analysis"}) or
                    (self.doctype == "URANOS RFI" and old.status == "Answered")):
            frappe.throw("Submitted workflow evidence and impacts are immutable")
        for field in {"URANOS Change Request": ("verification_evidence",), "URANOS RFI": ("answer_evidence",),
                      "URANOS Blocker": ("resolution_evidence",)}.get(self.doctype, ()):
            before = [dict(file=row.file, caption=row.get("caption")) for row in old.get(field, [])] if old else []
            after = [dict(file=row.file, caption=row.get("caption")) for row in self.get(field, [])]
            if before != after:
                frappe.throw("Decision evidence must be captured by the controlled service", frappe.PermissionError)


def _decimal(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        frappe.throw("Numeric value is invalid")
    if not result.is_finite():
        frappe.throw("Numeric values must be finite")
    return result


def _finite_quantities(doc):
    for row in (doc, *doc.get_all_children()):
        for df in row.meta.fields:
            if df.fieldtype in {"Float", "Currency", "Percent"} and row.get(df.fieldname) is not None:
                value = _decimal(row.get(df.fieldname))
                if value < 0 and df.fieldname not in {"variance", "cost_impact"}:
                    frappe.throw(f"{df.label} cannot be negative")
