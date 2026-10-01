"""Atomic, actor-bound synchronization of field drafts and private evidence.

All mutation endpoints are POST-only and retain Frappe's session/CSRF checks.
Receipt + draft + file records commit together at the normal request boundary.
Nothing in this service submits an ERP stock transaction or verifies progress.
"""
from __future__ import annotations

import io
import json
import base64
import hashlib
import secrets

import frappe
from PIL import Image, UnidentifiedImageError
from frappe.utils.file_manager import save_file

from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain.offline import OfflineConflict, OfflineValidationError, check_retry, receipt_identity, validate_envelope
from uranos_project_os.services.common import actor, require_post, scoped_doc

DOCTYPE = {
    "progress": "URANOS Field Progress Entry", "daily_report": "URANOS Daily Site Report",
    "kit_request": "URANOS Kit Issue", "kit_return": "URANOS Kit Return", "inspection": "URANOS Field Inspection",
}
ROLES = {
    "progress": ("Team Lead", "Site Controller", "Civil Director", "Electrical Execution Manager", "Project Manager"),
    "daily_report": ("Team Lead", "Site Controller", "Project Manager"),
    "kit_request": ("Team Lead", "Storekeeper", "Project Manager"),
    "kit_return": ("Team Lead", "Storekeeper", "Project Manager"),
    "inspection": ("Team Lead", "Site Controller", "QA QC", "Project Manager"),
}
RECEIPT = "URANOS Offline Sync Receipt"


def _expected_actor():
    user = actor()
    if frappe.get_request_header("X-URANOS-User") != user:
        frappe.throw("Session identity changed; sign in again before synchronizing", frappe.PermissionError)
    return user


@frappe.whitelist(methods=["POST"])
def encryption_key():
    """Return only this authenticated user's persistent offline wrapping key.

    Stable server encryption permits recovery after a browser crash/relogin.
    The browser keeps the imported key in memory; only ciphertext persists.
    Loss of the site's Frappe encryption key is a disaster-recovery failure.
    """
    from frappe.utils.password import get_decrypted_password
    require_post()
    user = _expected_actor()
    from uranos_project_os.services.api import FIELD_ROLES
    security.require_roles(*FIELD_ROLES)
    if not frappe.db.get_value("User", user, "enabled"):
        frappe.throw("Account is disabled", frappe.PermissionError)
    frappe.local.response_headers["Cache-Control"] = "no-store, private"
    # User exists before the first key request, so its row also serializes the
    # initial creation; no concurrent caller can receive a discarded key.
    frappe.db.sql("SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE", (user,))
    doctype = "URANOS Offline Identity Key"
    name = hashlib.sha256(user.encode()).hexdigest()
    if not frappe.db.exists(doctype, name):
        key = base64.b64encode(secrets.token_bytes(32)).decode()
        with authorized_transition():
            # Frappe's Password field lifecycle stores this in encrypted __Auth,
            # not plaintext in the DocType row. Supply it before mandatory checks.
            frappe.get_doc({"doctype": doctype, "name": name, "user": user,
                            "encryption_key": key}).insert(ignore_permissions=True, set_name=name)
    else:
        if frappe.db.get_value(doctype, name, "user") != user:
            frappe.throw("Offline identity mismatch", frappe.PermissionError)
        key = get_decrypted_password(doctype, name, fieldname="encryption_key")
    return {"key_base64": key}


def _assert_source(envelope):
    payload = envelope.payload
    if payload.get("kit_issue") and payload.get("cable_reel"):
        raise OfflineValidationError("Progress cannot consume a kit and reel simultaneously")
    for field, doctype in {"work_package": "URANOS Work Package", "kit_template": "URANOS Material Kit Template",
                           "kit_issue": "URANOS Kit Issue", "cable_reel": "URANOS Cable Reel", "from_warehouse": "Warehouse", "to_warehouse": "Warehouse"}.items():
        if payload.get(field):
            linked = scoped_doc(doctype, payload[field], lock=True)
            if security.project_for(linked) != envelope.project:
                frappe.throw("Offline draft references another project", frappe.PermissionError)
            if field == "work_package":
                if payload.get("baseline_version") and linked.baseline_version != payload["baseline_version"]:
                    raise OfflineConflict("Work package baseline changed; review this draft before resending")
                if envelope.base_modified and str(linked.modified) != envelope.base_modified:
                    raise OfflineConflict("Work package changed after offline capture; review the draft")
                if envelope.operation == "progress":
                    baseline_name = frappe.db.get_value("URANOS Project Profile", {"project": envelope.project}, "current_baseline")
                    version = frappe.db.get_value("URANOS Baseline", baseline_name, "version") if baseline_name else None
                    if version != payload.get("baseline_version") or not linked.baseline_approved:
                        raise OfflineConflict("The current approved baseline changed; review this offline draft")
            if field == "kit_template" and linked.status != "Approved":
                raise OfflineConflict("Kit BOM version is not approved")
            if field in {"kit_issue", "cable_reel"} and linked.status in {"Closed", "Cancelled"}:
                raise OfflineConflict("Referenced material allocation is closed")
            if field in {"from_warehouse", "to_warehouse"} and linked.get("is_group"):
                raise OfflineValidationError("A leaf warehouse is required")


def _private_evidence(envelope):
    result = []
    for attachment in envelope.attachments:
        try:
            with Image.open(io.BytesIO(attachment.content)) as img:
                if img.width * img.height > 25_000_000 or img.format not in {"PNG", "JPEG"}:
                    raise OfflineValidationError("Evidence image is too large or unsupported")
                img.verify()
        except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
            raise OfflineValidationError("Evidence is not a valid image") from exc
        file = save_file(attachment.filename, attachment.content, None, None, is_private=1)
        result.append(file)
    return result


def _drafts(envelope):
    data = dict(envelope.payload)
    base = {"doctype": DOCTYPE[envelope.operation], "project": envelope.project,
            "status": "Draft Request" if envelope.operation == "kit_request" else "Draft"}
    if envelope.operation == "daily_report":
        if "equipment" in data:
            data["equipment_summary"] = data.pop("equipment")
    elif envelope.operation == "inspection":
        data["checklist"] = [{"code": row["check"], "description": row.get("notes", row["check"]),
                              "result": row["result"], "completed": 0} for row in data.pop("checks")]
    elif envelope.operation == "kit_return":
        rows = data.pop("returns")
        results = []
        issue = frappe.get_doc("URANOS Kit Issue", data["kit_issue"])
        template = frappe.get_doc("URANOS Material Kit Template", issue.kit_template)
        expected_units = {row.item_code: row.uom for row in template.items}
        for row in rows:
            if expected_units.get(row["item_code"]) != row["uom"]:
                raise OfflineValidationError("Return item/unit does not match the issued kit BOM")
            results.append(frappe.get_doc(base | data | {"item_code": row["item_code"], "returned_qty": row["qty"], "uom": row["uom"]}))
        return results
    return [frappe.get_doc(base | data)]


@frappe.whitelist(methods=["POST"])
def synchronize(envelope):
    require_post()
    user = _expected_actor()
    if isinstance(envelope, str):
        try:
            envelope = json.loads(envelope)
        except (ValueError, TypeError) as exc:
            raise OfflineValidationError("Invalid JSON envelope") from exc
    draft = validate_envelope(envelope)
    security.require_roles(*ROLES[draft.operation])
    security.require_project(draft.project, doctype=DOCTYPE[draft.operation])
    name = receipt_identity(user, draft.uuid)
    # A locking current read is required after a racing request commits, even
    # under MariaDB's repeatable-read isolation.
    existing = frappe.db.sql("SELECT * FROM `tabURANOS Offline Sync Receipt` WHERE name=%s FOR UPDATE", (name,), as_dict=True)
    if existing:
        response = check_retry(existing[0], user, draft)
        response["records"] = json.loads(existing[0].get("result_json") or "[]")
        return response
    frappe.db.savepoint("uranos_offline_sync")
    try:
        with authorized_transition():
            receipt = frappe.get_doc({"doctype": RECEIPT, "name": name, "project": draft.project,
                "sync_user": user, "sync_uuid": draft.uuid, "payload_hash": draft.payload_hash, "status": "Pending"})
            receipt.insert(ignore_permissions=True, set_name=name)
    except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
        frappe.db.rollback(save_point="uranos_offline_sync")
        existing = frappe.db.sql("SELECT * FROM `tabURANOS Offline Sync Receipt` WHERE name=%s FOR UPDATE", (name,), as_dict=True)
        if not existing:
            raise OfflineConflict("Synchronization is busy; retry this same draft")
        response = check_retry(existing[0], user, draft)
        response["records"] = json.loads(existing[0].get("result_json") or "[]")
        return response
    # Errors are propagated: Frappe rolls back the entire POST transaction.
    _assert_source(draft)
    docs = _drafts(draft)
    files = _private_evidence(draft)
    records = []
    for index, doc in enumerate(docs):
        doc.check_permission("create")
        for file in files:
            doc.append("evidence", {"file": file.name, "captured_by": user})
        with authorized_transition():
            # One UUID corresponds to one receipt; multi-item return child drafts
            # carry unique derived provenance, but are still all-or-nothing.
            doc.sync_uuid = draft.uuid if len(docs) == 1 else f"{draft.uuid}:{index}"
            doc.insert()
        records.append({"doctype": doc.doctype, "name": doc.name, "docstatus": doc.docstatus})
    for file in files:
        file = frappe.get_doc("File", file.name)  # drop transient content before attachment-only update
        file.attached_to_doctype = docs[0].doctype
        file.attached_to_name = docs[0].name
        file.save(ignore_permissions=True)
    with authorized_transition():
        receipt.reference_doctype = docs[0].doctype
        receipt.reference_name = docs[0].name
        receipt.status = "Accepted"
        receipt.result_json = json.dumps(records)
        receipt.save(ignore_permissions=True)
    return {"status": "synced", "uuid": draft.uuid, "doctype": docs[0].doctype, "name": docs[0].name,
            "records": records, "duplicate": False, "docstatus": 0}
