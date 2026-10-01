"""Project-locked shipment services with ERP purchase/receipt provenance.

Tracking never creates stock. External provider workers may call the private
ingestion adapter after authenticating their provider; the public endpoint is
explicitly a named, manual-verified update, not a fabricated carrier API event.
"""
from __future__ import annotations

from datetime import timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json

import frappe

from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain import logistics, stock
from uranos_project_os.services.common import require_post, scoped_doc
from uranos_project_os.services.materials import _alert, _aware, _erp_doc, _historical_actor, _locked, _result, _save


SOURCE_NAMES = {"Manual Verified": "manual verified", "API": "API", "Forwarder Email": "forwarder email", "Carrier Portal": "carrier portal"}


def _list_json(value, label):
    try:
        result = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError) as exc:
        frappe.throw(f"{label} must be valid JSON")
        raise exc  # never reached under Frappe; retains safe behavior in test stubs
    if not isinstance(result, list) or not result or len(result) > 1000:
        frappe.throw(f"{label} requires 1–1000 rows")
    return result


def _containers(doc):
    names = frappe.get_all("URANOS Container", filters={"project": doc.project, "shipment": doc.name}, fields=["name"], limit_page_length=0)
    if not names:
        frappe.throw("Configure the shipment's identified containers first")
    result = {}
    for row in names:
        container = scoped_doc("URANOS Container", row.name)
        if container.project != doc.project or container.shipment != doc.name:
            frappe.throw("Container has a conflicting shipment/project")
        result[container.name] = container
    return result


def _po_allocations(doc, raw):
    containers = _containers(doc)
    allowed_po = {row.purchase_order for row in doc.purchase_orders}
    result = []
    for value in _list_json(raw, "Packing allocations"):
        if not isinstance(value, dict) or set(value) != {"purchase_order_item", "container", "quantity"}:
            frappe.throw("Each allocation accepts only purchase_order_item, container and quantity")
        row = frappe.get_doc("Purchase Order Item", stock.identifier(value["purchase_order_item"]))
        if row.parent not in allowed_po or row.parenttype != "Purchase Order":
            frappe.throw("Packing allocation is outside the shipment's declared Purchase Orders")
        po = _erp_doc("Purchase Order", row.parent, doc.project)
        if po.docstatus != 1 or po.supplier != doc.supplier:
            frappe.throw("Shipment requires submitted Purchase Orders from its named supplier")
        if row.get("project") and row.project != doc.project:
            frappe.throw("Purchase Order item belongs to another project")
        if value["container"] not in containers:
            frappe.throw("Packing allocation container is outside this shipment")
        item = frappe.get_doc("Item", row.item_code)
        if not item.is_stock_item or item.disabled or row.stock_uom != item.stock_uom:
            frappe.throw("Packing allocation requires an active stock item in its stock UOM")
        amount = stock.quantity(value["quantity"], positive=True)
        result.append({"purchase_order": po.name, "purchase_order_item": row.name, "item_code": row.item_code,
            "quantity": str(amount), "uom": row.stock_uom, "container": value["container"],
            "container_no": containers[value["container"]].container_number})
    keys = [(line["purchase_order_item"], line["container"]) for line in result]
    if len(keys) != len(set(keys)):
        frappe.throw("Duplicate PO row/container allocation")
    return result


@frappe.whitelist(methods=["POST"])
def configure_shipment(name, allocations):
    require_post()
    security.require_roles("Procurement Logistics")
    doc = _locked("URANOS Shipment", name)
    if doc.status != "Planned" or frappe.db.exists("URANOS Shipment Milestone", {"shipment": doc.name}):
        frappe.throw("Packing allocations are frozen after the first accepted milestone")
    if not doc.eta_initial or doc.delay_alert_days is None or int(doc.delay_alert_days) < 0:
        frappe.throw("Configure original ETA and the approved nonnegative ETA alert threshold")
    normalized = _po_allocations(doc, allocations)
    allocated = {}
    others = frappe.get_all("URANOS Shipment", filters={"project": doc.project, "name": ["!=", doc.name]},
        fields=["packing_allocations"], limit_page_length=0)
    for other in others:
        if other.packing_allocations:
            for line in _list_json(other.packing_allocations, "Persisted packing allocations"):
                key = line["purchase_order_item"]
                allocated[key] = allocated.get(key, Decimal(0)) + stock.quantity(line["quantity"], positive=True)
    for line in normalized:
        key = line["purchase_order_item"]
        allocated[key] = allocated.get(key, Decimal(0)) + stock.quantity(line["quantity"], positive=True)
        ordered = stock.quantity(frappe.db.get_value("Purchase Order Item", key, "stock_qty"), positive=True)
        if allocated[key] > ordered:
            frappe.throw("All shipments together exceed the submitted Purchase Order item's stock quantity")
    doc.packing_allocations = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    # Constructing the snapshot catches duplicate container/seal identities too.
    _shipment(doc, include_events=False)
    return _save(doc)


def _receipt_evidence(doc, receipt_name):
    if not receipt_name:
        return ()
    receipt = _erp_doc("Purchase Receipt", receipt_name, doc.project)
    if receipt.docstatus != 1 or receipt.is_return:
        frappe.throw("Shipment site receipt requires a submitted positive Purchase Receipt")
    containers = _containers(doc)
    proof = []
    received_at = _aware(str(receipt.posting_date) + " " + str(receipt.posting_time or "00:00:00"))
    for row in receipt.items:
        if row.get("uranos_shipment") != doc.name:
            continue
        if row.get("project") and row.project != doc.project:
            frappe.throw("Purchase Receipt row project differs from shipment")
        container = containers.get(row.get("uranos_container"))
        if not container:
            frappe.throw("Received shipment item lacks an exact matching container")
        proof.append(logistics.PurchaseReceiptEvidence(receipt.name, row.name, doc.project, doc.name,
            row.purchase_order, row.purchase_order_item, row.item_code, row.stock_qty, row.stock_uom,
            container.container_number, received_at, int(receipt.docstatus)))
    if not proof:
        frappe.throw("Purchase Receipt contains no rows explicitly allocated to this shipment")
    return tuple(proof)


def _event_actor(project, user):
    security.require_project(project, user=user)
    security.require_roles("Procurement Logistics", user=user)
    return stock.Actor(user, {project}, {"shipment_update"})


def _shipment(doc, *, include_events=True):
    containers = _containers(doc)
    allocations = _list_json(doc.packing_allocations, "Approved packing allocation snapshot")
    state = logistics.Shipment(doc.name, doc.project, _aware(doc.eta_initial),
        tuple(logistics.Container(x.container_number, x.seal_number, doc.name, doc.project) for x in containers.values()),
        tuple(logistics.ShipmentLine(x["purchase_order"], x["purchase_order_item"], x["item_code"], x["quantity"],
                                    x["uom"], x["container_no"]) for x in allocations))
    if not include_events:
        return state
    milestones = frappe.get_all("URANOS Shipment Milestone", filters={"project": doc.project, "shipment": doc.name},
        fields=["name"], order_by="creation asc, name asc", limit_page_length=0)
    for row in milestones:
        persisted = frappe.get_doc("URANOS Shipment Milestone", row.name)
        try:
            payload = json.loads(persisted.event_payload)
        except (TypeError, ValueError):
            frappe.throw("Shipment event lacks a valid immutable payload")
        event = logistics.ShipmentEvent(payload["event_id"], persisted.provider, doc.name, doc.project,
            persisted.milestone_type, SOURCE_NAMES[persisted.source_type], _aware(persisted.source_timestamp),
            _aware(persisted.creation), persisted.source_reference,
            _historical_actor(doc.project, persisted.recorded_by, "shipment_update"), _aware(persisted.eta) if persisted.eta else None,
            _receipt_evidence(doc, persisted.purchase_receipt))
        if event.payload_digest != persisted.payload_hash:
            frappe.throw("Persisted tracking/receipt evidence differs from the accepted event payload")
        state = logistics.apply_shipment_event(state, event)
    if doc.status != state.status:
        frappe.throw("Shipment status differs from its accepted milestone history")
    return state


def _ingest_event(doc, *, event_id, provider, status, source_type, source_timestamp,
                  source_reference, user, eta=None, purchase_receipt=None):
    current = _shipment(doc)
    if source_type not in SOURCE_NAMES:
        frappe.throw("Unsupported tracking source type")
    # Frappe persists local naive DATETIME values. Normalize before hashing so
    # an ISO-8601 offset is not lost between first acceptance and replay.
    from zoneinfo import ZoneInfo
    zone = frappe.utils.get_system_timezone()
    local_tz = timezone.utc if zone == "UTC" else ZoneInfo(zone)
    source_timestamp = _aware(source_timestamp).astimezone(local_tz).replace(tzinfo=None)
    eta = _aware(eta).astimezone(local_tz).replace(tzinfo=None) if eta else None
    event = logistics.ShipmentEvent(stock.identifier(event_id), stock.identifier(provider), doc.name, doc.project,
        status, SOURCE_NAMES[source_type], _aware(source_timestamp), _aware(frappe.utils.now_datetime()),
        source_reference, _event_actor(doc.project, user), _aware(eta) if eta else None,
        _receipt_evidence(doc, purchase_receipt))
    updated = logistics.apply_shipment_event(current, event)
    if updated is current:
        return _result(doc)
    nonce = sha256(json.dumps([doc.project, doc.name, provider, event_id], separators=(",", ":")).encode()).hexdigest()
    with authorized_transition():
        frappe.get_doc({"doctype": "URANOS Shipment Milestone", "project": doc.project, "shipment": doc.name,
            "milestone_type": status, "actual_at": source_timestamp, "source_type": source_type,
            "source_timestamp": source_timestamp, "provider": provider, "source_reference": source_reference,
            "provider_event_id": nonce, "payload_hash": event.payload_digest, "recorded_by": user,
            "eta": eta, "purchase_receipt": purchase_receipt,
            "event_payload": json.dumps({"event_id": event_id}, sort_keys=True)}).insert(ignore_permissions=True)
    doc.status = updated.status
    if eta:
        doc.eta_revised = eta
    if purchase_receipt:
        doc.purchase_receipt = purchase_receipt
    missing = []
    available = []
    for requirement in doc.required_documents:
        if not requirement.mandatory:
            continue
        missing.append(requirement.document_code)
        registered = frappe.get_all("URANOS Document Register", filters={"project": doc.project,
            "document_code": requirement.document_code, "status": ["in", ["Approved", "IFC", "As-built"]]},
            fields=["name", "file"], limit_page_length=0)
        if any(row.file for row in registered):
            available.append(requirement.document_code)
    alerts = logistics.shipment_alerts(updated, threshold=timedelta(days=int(doc.delay_alert_days)),
        as_of=frappe.utils.getdate(), required_documents=missing, available_documents=available,
        need_date=frappe.utils.getdate(doc.need_by) if doc.need_by else None)
    for alert in alerts:
        _alert(doc.project, doc.doctype, doc.name, alert.rule, alert.message)
    if doc.status in {"Site Received", "Closed"}:
        for container in _containers(doc).values():
            container.status = "Received" if doc.status == "Site Received" else "Closed"
            _save(container, trusted=True)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def record_shipment_milestone(name, event_id, status, source_timestamp, source_reference, eta=None, purchase_receipt=None):
    require_post()
    user = security.require_roles("Procurement Logistics")
    doc = _locked("URANOS Shipment", name)
    # The adapter contract is available to authenticated background provider
    # workers, but this public endpoint never claims a user's entry is carrier API evidence.
    return _ingest_event(doc, event_id=event_id, provider="manual:" + user, status=status,
        source_type="Manual Verified", source_timestamp=source_timestamp, source_reference=source_reference,
        user=user, eta=eta, purchase_receipt=purchase_receipt)


@frappe.whitelist()
def material_readiness(project, item_code, required_qty, need_date):
    """Finance-free snapshot; stock in transit never counts as available stock."""
    security.require_roles("Storekeeper", "Site Controller", "Project Manager", "Procurement Logistics", "Executive", "Engineering Director")
    security.require_project(project)
    item = frappe.get_doc("Item", item_code)
    stock.quantity(required_qty)
    on_site = []
    for warehouse in frappe.get_all("Warehouse", filters={"uranos_project": project, "is_group": 0, "disabled": 0},
        fields=["name", "uranos_stock_state"], limit_page_length=0):
        row = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse.name},
                                  ["actual_qty", "reserved_qty", "reserved_qty_for_production", "reserved_qty_for_sub_contract"], as_dict=True)
        if not row:
            continue
        if not warehouse.uranos_stock_state:
            frappe.throw("All project warehouses require an approved stock state before readiness calculation")
        reserved = sum((stock.quantity(row.get(field) or 0) for field in
                        ("reserved_qty", "reserved_qty_for_production", "reserved_qty_for_sub_contract")), Decimal(0))
        on_site.append(logistics.AvailableStock(warehouse.name, project, item_code, item.stock_uom,
                                               row.actual_qty, reserved, warehouse.uranos_stock_state))
    pending = []
    allocated_by_po = {}
    records = frappe.get_all("URANOS Shipment", filters={"project": project}, fields=["name"], limit_page_length=0)
    for record in records:
        doc = scoped_doc("URANOS Shipment", record.name)
        if not doc.packing_allocations:
            continue
        state = _shipment(doc)
        quantities = state.received_quantities
        for line in state.items:
            if line.item_code != item_code:
                continue
            outstanding = line.quantity - quantities[line.allocation_key]
            allocated_by_po[line.purchase_order_item] = allocated_by_po.get(line.purchase_order_item, Decimal(0)) + outstanding
            if outstanding:
                pending.append(logistics.PendingSupply(doc.name + ":" + line.purchase_order_item + ":" + line.container_no,
                    project, item_code, item.stock_uom, outstanding,
                    "In Transit" if logistics.SHIPMENT_STATES.index(state.status) >= logistics.SHIPMENT_STATES.index("Departed") else "Ordered",
                    state.current_eta.date()))
    for po in frappe.get_all("Purchase Order", filters={"project": project, "docstatus": 1, "status": ["not in", ["Closed", "Cancelled"]]},
                             fields=["name"], limit_page_length=0):
        doc = _erp_doc("Purchase Order", po.name, project)
        for row in doc.items:
            if row.item_code != item_code:
                continue
            # ERP received_qty is purchase UOM; conversion_factor gives stock UOM.
            remaining = stock.quantity(row.stock_qty) - stock.quantity(row.received_qty or 0) * stock.quantity(row.conversion_factor, positive=True)
            unallocated = remaining - allocated_by_po.get(row.name, Decimal(0))
            if unallocated < 0:
                frappe.throw("Shipment allocations/receipts disagree with outstanding Purchase Order stock quantity")
            if unallocated:
                pending.append(logistics.PendingSupply("PO:" + row.name, project, item_code, item.stock_uom,
                    unallocated, "Ordered", frappe.utils.getdate(row.schedule_date) if row.schedule_date else None))
    result = logistics.evaluate_material_readiness(project=project, item_code=item_code, uom=item.stock_uom,
        required_qty=required_qty, need_date=frappe.utils.getdate(need_date), on_site=on_site, supply=pending)
    return {key: str(value) if isinstance(value, Decimal) else value for key, value in result.__dict__.items()}
