"""Narrow ERPNext stock workflows; no caller-supplied actors, rates or approvals.

Each public mutation locks Project first. Standard Stock Entry submission runs
inside the authenticated transaction; any later failed validation rolls it back.
Never call commit here. Live ERPNext v16 integration tests remain mandatory.
"""
from __future__ import annotations

import json
from datetime import timezone as _tz
UTC = _tz.utc
from decimal import Decimal
from zoneinfo import ZoneInfo

import frappe

from uranos_project_os import security
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain import stock
from uranos_project_os.services.common import require_post, scoped_doc

CAPABILITY_ROLES = {
    "kit_request": ("Engineering Director", "Project Manager"),
    "kit_approve": ("Engineering Director",),
    "stock_issue": ("Storekeeper",),
    "stock_return": ("Storekeeper",),
    "stock_receive": ("Team Lead", "Site Controller", "Storekeeper"),
    "stock_request": ("Storekeeper", "Project Manager", "Site Controller"),
    "stock_approve": ("Executive", "Finance Controller", "Project Manager", "Engineering Director"),
    "progress_report": ("Team Lead", "Site Controller", "Civil Director", "Electrical Execution Manager", "Project Manager"),
    "progress_verify": ("Site Controller",),
}


def _aware(value):
    result = frappe.utils.get_datetime(value)
    zone = frappe.utils.get_system_timezone()
    local_tz = UTC if zone == "UTC" else ZoneInfo(zone)  # noqa: E501
    return result if result.utcoffset() is not None else result.replace(tzinfo=local_tz)


def _actor(project, user, capability):
    security.require_project(project, user=user)
    security.require_roles(*CAPABILITY_ROLES[capability], user=user)
    return stock.Actor(user, {project}, {capability})


def _historical_actor(project, user, capability):
    """Reconstitute the authority already accepted by a controlled transition.

    Only call for persisted immutable Posted/Verified/Approval records. Current
    callers and newly selected receivers still pass _actor live authorization.
    Revocation stops future actions; it does not invalidate historical work.
    """
    return stock.Actor(stock.identifier(user), {stock.identifier(project)}, {capability})


def _locked(doctype, name):
    # Each public caller has a narrow role check before here. Approval services
    # need read scope, not broad native write permission on financial documents.
    initial = scoped_doc(doctype, name)
    scoped_doc("Project", initial.project, lock=True)
    return scoped_doc(doctype, name, lock=True)


def _erp_doc(doctype, name, project):
    """Internal finance-bearing read after caller's explicit business role check."""
    if doctype not in {"BOM", "Stock Entry", "Purchase Receipt", "Purchase Order", "URANOS Approval Policy", "URANOS Stock Disposition"}:
        frappe.throw("Unsupported trusted document")
    security.require_project(project)
    doc = frappe.get_doc(doctype, name)
    if security.project_for(doc) != project:
        frappe.throw("ERP document belongs to another project", frappe.PermissionError)
    return doc


def _warehouse(name, project, allowed_states):
    doc = scoped_doc("Warehouse", name)
    if doc.uranos_project != project or doc.is_group or doc.get("disabled") or doc.get("uranos_stock_state") not in allowed_states:
        frappe.throw("Warehouse scope or approved stock state is invalid")
    return doc


def _item(name):
    doc = frappe.get_doc("Item", name)
    if doc.disabled or not doc.is_stock_item:
        frappe.throw("Only active stock items are supported")
    return doc


def _result(doc):
    # Do not return ERP amounts/rates or approval financial fields to field roles.
    return {"doctype": doc.doctype, "name": doc.name, "status": doc.status, "modified": str(doc.modified)}


def _save(doc, *, trusted=True):
    with authorized_transition():
        doc.save(ignore_permissions=trusted)
    return _result(doc)


def _post_stock(project, rows, *, purpose="Material Transfer"):
    if purpose not in {"Material Transfer", "Material Issue", "Material Receipt"}:
        frappe.throw("Unsupported controlled stock purpose")
    project_doc = scoped_doc("Project", project)
    if not project_doc.company:
        frappe.throw("Project company must be configured")
    for row in rows:
        item = _item(row["item_code"])
        if item.has_serial_no or item.has_batch_no:
            frappe.throw("Tracked items require a prepared ERPNext Stock Entry with its native serial/batch bundle")
        if row["stock_uom"] != item.stock_uom:
            frappe.throw("Stock UOM differs from the authoritative Item")
        for warehouse in (row.get("s_warehouse"), row.get("t_warehouse")):
            if warehouse:
                linked = scoped_doc("Warehouse", warehouse)
                if linked.uranos_project != project or linked.company != project_doc.company:
                    frappe.throw("Stock warehouse company/project mismatch")
    doc = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": purpose, "purpose": purpose,
                          "company": project_doc.company, "project": project, "items": rows})
    with authorized_transition():
        doc.insert(ignore_permissions=True)
        doc.flags.ignore_permissions = True
        doc.submit()
    return doc


def _prepared_transfer(name, project, subject, *, reel=False):
    entry = _erp_doc("Stock Entry", name, project)
    entry.flags.for_update = True
    entry.reload()  # Frappe v16 locks and reloads parent AND children.
    if entry.project != project:
        frappe.throw("Prepared stock transfer belongs to another project", frappe.PermissionError)
    if entry.purpose != "Material Transfer" or entry.docstatus not in {0, 1}:
        frappe.throw("Prepared stock document must be a draft/submitted Material Transfer")
    field = "uranos_reel" if reel else "uranos_kit_issue"
    if not entry.items or any(row.get(field) != subject for row in entry.items):
        frappe.throw("Prepared stock rows must reference the exact material allocation")
    if entry.docstatus == 0:
        # Subsequent exact domain validation is in the SAME request transaction;
        # any route/item/quantity mismatch rolls back the native ledger too.
        with authorized_transition():
            entry.flags.ignore_permissions = True
            entry.submit()
    return entry


def _native_identities(entry, row, *, docstatus, receipt=False):
    """Read native identities, never synthesize a serial/batch bundle."""
    item = _item(row.item_code)
    if not item.has_serial_no and not item.has_batch_no:
        if row.get("serial_and_batch_bundle") or row.get("serial_no") or row.get("batch_no"):
            frappe.throw("Unexpected tracking identities on an untracked stock item")
        return {(row.item_code, None): stock.quantity(row.stock_qty if receipt else row.transfer_qty, positive=True)}
    if not row.get("serial_and_batch_bundle"):
        frappe.throw("A native serial/batch bundle is required for prepared tracked consumption")
    bundle = frappe.get_doc("Serial and Batch Bundle", row.serial_and_batch_bundle)
    warehouse = row.warehouse if receipt else row.s_warehouse or row.t_warehouse
    direction = "Inward" if receipt else "Outward" if row.s_warehouse else "Inward"
    if (bundle.docstatus != docstatus or bundle.voucher_type != ("Purchase Receipt" if receipt else "Stock Entry") or bundle.voucher_no != entry.name
            or bundle.voucher_detail_no != row.name or bundle.item_code != row.item_code
            or bundle.company != entry.company or bundle.warehouse != warehouse or bundle.type_of_transaction != direction):
        frappe.throw("Native bundle must match this exact stock voucher row, item, company, warehouse and direction")
    result, serials = {}, set()
    for allocation in bundle.entries:
        if item.has_serial_no:
            serial = stock.identifier(allocation.serial_no, "serial identity")
            if serial in serials:
                frappe.throw("Duplicate serial identity inside native bundle")
            serials.add(serial)
            identity = "SERIAL:" + serial
        else:
            identity = "BATCH:" + stock.identifier(allocation.batch_no, "batch identity")
        if item.has_batch_no:
            stock.identifier(allocation.batch_no, "required native batch")
        raw = Decimal(str(allocation.qty))
        amount = stock.quantity(abs(raw), "native bundle quantity", positive=True)
        if (direction == "Outward" and raw > 0) or (direction == "Inward" and raw < 0):
            frappe.throw("Native bundle quantity sign does not match its stock direction")
        if item.has_serial_no and amount != 1:
            frappe.throw("Each serialized identity must represent exactly one stock unit")
        key = row.item_code, identity
        result[key] = result.get(key, Decimal(0)) + amount
    if sum(result.values(), Decimal(0)) != stock.quantity(row.stock_qty if receipt else row.transfer_qty, positive=True):
        frappe.throw("Native bundle identity quantities differ from the stock row quantity")
    return result


def _identity_balance(project, subject, *, reel=False):
    """Only identities previously issued to this allocation may leave its WIP."""
    balance = {}
    entries = []
    if reel:
        rows = frappe.get_all("URANOS Cable Reel Movement", filters={"project": project, "reel": subject, "status": "Posted"},
            fields=["stock_entry", "movement_type"], limit_page_length=0)
        entries.extend((row.stock_entry, 1 if row.movement_type == "Issue" else -1) for row in rows
                       if row.movement_type in {"Issue", "Return"})
    else:
        issue = scoped_doc("URANOS Kit Issue", subject)
        if issue.project != project:
            frappe.throw("Identity allocation project differs from issue")
        entries.append((issue.stock_entry, 1))
        returns = frappe.get_all("URANOS Kit Return", filters={"project": project, "kit_issue": subject, "status": "Posted"},
                                 fields=["stock_entry"], limit_page_length=0)
        entries.extend((row.stock_entry, -1) for row in returns)
    field = "cable_reel" if reel else "kit_issue"
    dispositions = frappe.get_all("URANOS Stock Disposition", filters={"project": project, field: subject, "status": "Posted"},
        fields=["stock_entry", "kind"], limit_page_length=0)
    entries.extend((row.stock_entry, 1 if row.kind == "Adjustment In" else -1) for row in dispositions)
    seen = set()
    for name, direction in entries:
        if not name or name in seen:
            frappe.throw("Stock identity evidence is missing or reused within this allocation")
        seen.add(name)
        entry = _erp_doc("Stock Entry", name, project)
        if entry.docstatus != 1:
            frappe.throw("Identity allocation requires submitted, uncancelled stock evidence")
        for row in entry.items:
            if row.get("uranos_reel" if reel else "uranos_kit_issue") != subject:
                frappe.throw("Stock identity evidence belongs to another allocation")
            for key, amount in _native_identities(entry, row, docstatus=1).items():
                balance[key] = balance.get(key, Decimal(0)) + amount * direction
    if any(amount < 0 for amount in balance.values()):
        frappe.throw("Stock identity history consumes more than was issued to this allocation")
    return balance


def _prepared_consumption(name, project, rows, *, purpose="Material Issue", allowed_identities=None):
    """Validate a real saved draft, submit it natively and revalidate atomically."""
    entry = _erp_doc("Stock Entry", name, project)
    frappe.db.sql("SELECT name FROM `tabStock Entry` WHERE name=%s FOR UPDATE", (name,))
    entry.flags.for_update = True  # child lines must use the current locked read too
    entry.reload()
    if entry.project != project or entry.docstatus != 0 or entry.purpose != purpose:
        frappe.throw("Prepared consumption/disposition must be an unsubmitted draft with the exact project and purpose")
    if purpose not in {"Material Issue", "Material Receipt", "Material Transfer"}:
        frappe.throw("Unsupported prepared stock purpose")
    company = scoped_doc("Project", project).company
    if not company or entry.company != company:
        frappe.throw("Prepared stock entry company differs from project")
    if entry.get("additional_costs") or entry.get("is_opening") == "Yes" or entry.get("add_to_transit") or entry.get("is_return"):
        frappe.throw("Prepared stock may not add unapproved costs, opening, transit or return semantics")
    if frappe.utils.getdate(entry.posting_date) != frappe.utils.getdate():
        frappe.throw("Prepared stock must post today; backdated/future adjustments require a separate workflow")

    def row_key(row):
        return (row.get("item_code"), row.get("stock_uom"), row.get("s_warehouse") or None,
                row.get("t_warehouse") or None, row.get("uranos_kit_issue") or None, row.get("uranos_reel") or None)

    expected = {}
    expected_rates = {}
    for row in rows:
        key = row_key(row)
        expected[key] = expected.get(key, Decimal(0)) + stock.quantity(row["qty"], positive=True)
        if row.get("basic_rate") is not None:
            expected_rates[key] = stock.quantity(row["basic_rate"], positive=True)

    def validate(submitted):
        totals, identities = {}, {}
        seen_bundles = set()
        for row in entry.items:
            key = row_key(row)
            if key not in expected or row.get("project") != project:
                frappe.throw("Prepared stock row does not match exact item, stock UOM, route, project and subject")
            item = _item(row.item_code)
            if row.uom != item.stock_uom or row.stock_uom != item.stock_uom or stock.quantity(row.conversion_factor, positive=True) != 1:
                frappe.throw("Prepared stock must use the exact approved stock UOM; implicit conversion is forbidden")
            amount = stock.quantity(row.qty, positive=True)
            if row.get("allow_zero_valuation_rate"):
                frappe.throw("Prepared stock may not bypass valuation")
            if key in expected_rates and stock.quantity(row.basic_rate, positive=True) != expected_rates[key]:
                frappe.throw("Incoming stock valuation must match the independently approved request")
            if purpose == "Material Issue" and row.get("set_basic_rate_manually"):
                frappe.throw("Outgoing prepared stock must use native valuation")
            if stock.quantity(row.transfer_qty, positive=True) != amount:
                frappe.throw("Prepared transfer quantity differs from its stock-UOM quantity")
            for warehouse in (row.s_warehouse, row.t_warehouse):
                if warehouse:
                    target = scoped_doc("Warehouse", warehouse)
                    if target.uranos_project != project or target.company != company or target.is_group or target.get("disabled"):
                        frappe.throw("Prepared stock warehouse is outside this company/project")
            bundle = row.get("serial_and_batch_bundle")
            if bundle and bundle in seen_bundles:
                frappe.throw("Native bundle cannot be reused by another prepared row")
            if bundle:
                seen_bundles.add(bundle)
            for identity, count in _native_identities(entry, row, docstatus=1 if submitted else 0).items():
                identities[identity] = identities.get(identity, Decimal(0)) + count
            totals[key] = totals.get(key, Decimal(0)) + amount
        if totals != expected:
            frappe.throw("Prepared stock quantities must exactly equal the server-calculated consumption/disposition")
        if any(identity and identity.startswith("SERIAL:") and amount != 1 for (_, identity), amount in identities.items()):
            frappe.throw("Serialized identity is reused across prepared stock rows")
        if allowed_identities is not None and any(
                amount > allowed_identities.get(identity, Decimal(0)) for identity, amount in identities.items()):
            frappe.throw("Prepared consumption uses identities or quantities not remaining in this allocation")

    validate(False)
    with authorized_transition():
        entry.flags.ignore_permissions = True
        entry.submit()
    validate(True)
    return entry


def _transfer_evidence(entry, project, subject, *, reel=False):
    if entry.project != project or entry.docstatus != 1 or entry.purpose != "Material Transfer":
        frappe.throw("A submitted same-project ERP Material Transfer is required")
    rows = []
    for row in entry.items:
        if row.get("project") and row.project != project:
            frappe.throw("Stock Entry row project differs from its parent")
        if row.get("uranos_reel" if reel else "uranos_kit_issue") != subject:
            frappe.throw("Stock Entry row is not bound to this exact issue/reel")
        for warehouse in (row.s_warehouse, row.t_warehouse):
            if not warehouse or scoped_doc("Warehouse", warehouse).uranos_project != project:
                frappe.throw("Stock transfer route is outside this project")
        if row.get("uranos_reel"):
            identities = [(row.uranos_reel, stock.quantity(row.transfer_qty, positive=True))]
        elif row.get("serial_and_batch_bundle"):
            bundle = frappe.get_doc("Serial and Batch Bundle", row.serial_and_batch_bundle)
            if bundle.voucher_type != "Stock Entry" or bundle.voucher_no != entry.name or bundle.item_code != row.item_code or bundle.docstatus != 1:
                frappe.throw("Serial/batch evidence does not belong to this submitted stock row")
            identities = [("SERIAL:" + item.serial_no if item.serial_no else "BATCH:" + stock.identifier(item.batch_no),
                           stock.quantity(abs(Decimal(str(item.qty))), positive=True)) for item in bundle.entries]
            if sum((amount for _, amount in identities), Decimal(0)) != stock.quantity(row.transfer_qty, positive=True):
                frappe.throw("Serial/batch bundle quantity differs from stock transfer quantity")
        elif row.get("serial_no"):
            serials = [value.strip() for value in row.serial_no.splitlines() if value.strip()]
            identities = [("SERIAL:" + serial, Decimal(1)) for serial in serials]
            if Decimal(len(serials)) != stock.quantity(row.transfer_qty, positive=True):
                frappe.throw("Legacy serial evidence differs from stock transfer quantity")
        else:
            identities = [("BATCH:" + row.batch_no if row.get("batch_no") else None,
                           stock.quantity(row.transfer_qty, positive=True))]
        rows.extend(stock.StockLine(row.item_code, amount, row.stock_uom, row.s_warehouse,
                                     row.t_warehouse, identity) for identity, amount in identities)
    return stock.StockEntryEvidence(entry.name, project, subject, int(entry.docstatus), entry.purpose, tuple(rows))


def _kit_snapshot(doc):
    if doc.status not in {"Approved", "Superseded"}:
        frappe.throw("An engineering-approved kit version is required")
    return stock.KitVersion(doc.project, doc.kit_code, doc.kit_version, doc.source_bom,
                            doc.source_bom, tuple(stock.BOMLine(x.item_code, x.qty_per_unit, x.uom,
                            x.risk_class, x.tolerance_percent, bool(x.returnable)) for x in doc.items),
                            doc.owner, doc.approved_by, _aware(doc.approved_at))


@frappe.whitelist(methods=["POST"])
def approve_kit_template(name):
    require_post()
    user = security.require_roles("Engineering Director")
    doc = _locked("URANOS Material Kit Template", name)
    if doc.status not in {"Draft", "Pending Approval"}:
        frappe.throw("Only an unapproved kit version can be approved")
    bom = _erp_doc("BOM", doc.source_bom, doc.project)
    if bom.docstatus != 1 or not bom.is_active:
        frappe.throw("Source BOM must be submitted and active")
    output = stock.quantity(bom.quantity, "BOM output quantity", positive=True)
    output_uom = stock.identifier(bom.uom, "BOM output UOM")
    configured = {x.item_code: x for x in doc.items}
    if len(configured) != len(doc.items):
        frappe.throw("Kit items must be unique")
    calculated = {}
    for row in bom.items:
        item = _item(row.item_code)
        if row.stock_uom != item.stock_uom:
            frappe.throw("Approved BOM stock UOM differs from Item")
        calculated[row.item_code] = calculated.get(row.item_code, Decimal(0)) + stock.quantity(row.stock_qty, positive=True) / output
    if set(calculated) != set(configured):
        frappe.throw("Kit item set must match the approved BOM; populate its draft controls before approval")
    lines = []
    for item_code, amount in calculated.items():
        config, item = configured[item_code], _item(item_code)
        if stock.quantity(config.qty_per_unit, positive=True) != amount or config.uom != item.stock_uom:
            frappe.throw("Kit quantity must match submitted BOM stock quantity / BOM output")
        if not item.uranos_risk_class or config.risk_class != item.uranos_risk_class:
            frappe.throw("Kit risk classification must match the configured Item")
        lines.append(stock.BOMLine(item_code, amount, item.stock_uom, config.risk_class,
                                    config.tolerance_percent, bool(config.returnable)))
    stock.approve_kit_version(project=doc.project, kit_code=doc.kit_code, kit_version=doc.kit_version,
                              source_bom=bom.name, source_bom_version=bom.name, source_docstatus=bom.docstatus,
                              items=lines, requester=_actor(doc.project, doc.owner, "kit_request"),
                              approver=_actor(doc.project, user, "kit_approve"), approved_at=_aware(frappe.utils.now_datetime()))
    doc.bom_output_qty, doc.approved_by, doc.approved_at, doc.status = str(output), user, frappe.utils.now(), "Approved"
    doc.output_uom = output_uom
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def approve_kit_request(name):
    require_post()
    user = security.require_roles("Project Manager", "Site Controller")
    doc = _locked("URANOS Kit Issue", name)
    if doc.status != "Draft Request" or doc.recorded_by == user:
        frappe.throw("Kit request requires an independent supervisor approval")
    template = scoped_doc("URANOS Material Kit Template", doc.kit_template)
    if template.project != doc.project or template.status != "Approved":
        frappe.throw("Use an active approved kit version for this project")
    if doc.activity != template.activity or not doc.work_package:
        frappe.throw("Kit request must use its approved activity and an explicit work package")
    stock.identifier(doc.zone, "explicit kit issue zone")
    package = scoped_doc("URANOS Work Package", doc.work_package)
    if package.project != doc.project or not package.baseline_approved:
        frappe.throw("Kit request requires an approved same-project work package baseline")
    if not template.output_uom or package.uom != template.output_uom:
        frappe.throw("Work quantity UOM must equal the engineering-approved BOM output UOM; implicit conversion is forbidden")
    _kit_snapshot(template)
    stock.quantity(doc.qty_kits, positive=True)
    _warehouse(doc.from_warehouse, doc.project, {"Available"})
    _warehouse(doc.to_warehouse, doc.project, {"WIP"})
    doc.kit_version, doc.status = template.kit_version, "Approved"
    return _save(doc)


def _issued(doc):
    if doc.status not in {"Issued", "Partially Used", "Variance Review", "Reconciled", "Closed"} or not doc.stock_entry:
        frappe.throw("Kit has not been issued")
    template = scoped_doc("URANOS Material Kit Template", doc.kit_template)
    snapshot = _kit_snapshot(template)
    if doc.project != template.project or doc.kit_version != template.kit_version:
        frappe.throw("Issued kit snapshot no longer matches its approved version")
    entry = _erp_doc("Stock Entry", doc.stock_entry, doc.project)
    return stock.KitIssue(doc.name, snapshot, doc.qty_kits, _transfer_evidence(entry, doc.project, doc.name), doc.issued_by, doc.received_by)


@frappe.whitelist(methods=["POST"])
def issue_kit(name, prepared_stock_entry=None):
    require_post()
    user = security.require_roles("Storekeeper")
    doc = _locked("URANOS Kit Issue", name)
    if doc.status in {"Issued", "Partially Used", "Variance Review", "Reconciled", "Closed"}:
        _issued(doc)
        if prepared_stock_entry and prepared_stock_entry != doc.stock_entry:
            frappe.throw("Kit issue retry conflicts with its posted Stock Entry")
        return _result(doc)
    if doc.status != "Approved":
        frappe.throw("Kit request must be approved before stock issue")
    template = scoped_doc("URANOS Material Kit Template", doc.kit_template)
    if template.status != "Approved" or doc.kit_version != template.kit_version:
        frappe.throw("Kit version is no longer approved for new issues")
    snapshot = _kit_snapshot(template)
    count = stock.quantity(doc.qty_kits, positive=True)
    if any(_item(line.item_code).get("uranos_reel_tracking") for line in snapshot.items):
        frappe.throw("Cable reels require the dedicated reel movement workflow; do not duplicate reel stock in a kit")
    _warehouse(doc.from_warehouse, doc.project, {"Available"})
    _warehouse(doc.to_warehouse, doc.project, {"WIP"})
    receiver = _actor(doc.project, doc.received_by, "stock_receive")
    issuer = _actor(doc.project, user, "stock_issue")
    if prepared_stock_entry:
        entry = _prepared_transfer(prepared_stock_entry, doc.project, doc.name)
        if frappe.db.exists("URANOS Kit Issue", {"stock_entry": entry.name, "name": ["!=", doc.name]}):
            frappe.throw("Stock Entry is already allocated to another kit issue")
    else:
        rows = [{"item_code": line.item_code, "qty": str(line.qty_per_unit * count), "uom": line.uom,
                 "stock_uom": line.uom, "conversion_factor": 1, "s_warehouse": doc.from_warehouse,
                 "t_warehouse": doc.to_warehouse, "project": doc.project, "uranos_kit_issue": doc.name}
                for line in snapshot.items]
        entry = _post_stock(doc.project, rows)
    evidence = _transfer_evidence(entry, doc.project, doc.name)
    if any(x.source_warehouse != doc.from_warehouse or x.target_warehouse != doc.to_warehouse for x in evidence.items):
        frappe.throw("Stock Entry does not match the approved issue route")
    stock.build_kit_issue(issue_id=doc.name, kit=snapshot, qty_kits=count, stock_entry=evidence, issuer=issuer, receiver=receiver)
    doc.issued_by, doc.stock_entry, doc.status = user, entry.name, "Issued"
    return _save(doc)


def _effective_progress(project, field, subject):
    if field not in {"kit_issue", "cable_reel"}:
        frappe.throw("Unsupported progress allocation")
    rows = frappe.get_all("URANOS Field Progress Entry", filters={"project": project, field: subject, "status": "Verified"}, fields=["name"], limit_page_length=0)
    entries = [frappe.get_doc("URANOS Field Progress Entry", row.name) for row in rows]
    superseded = {entry.correction_of for entry in entries if entry.correction_of}
    names = {entry.name for entry in entries}
    if not superseded <= names:
        frappe.throw("Verified correction is not bound to the same material allocation")
    if len([entry.correction_of for entry in entries if entry.correction_of]) != len(superseded):
        frappe.throw("Multiple verified corrections reuse the same material contribution")
    return [entry for entry in entries if entry.name not in superseded]


def _kit_installed(doc, snapshot):
    result = []
    template = scoped_doc("URANOS Material Kit Template", doc.kit_template)
    package = scoped_doc("URANOS Work Package", doc.work_package)
    if not template.output_uom or package.uom != template.output_uom:
        frappe.throw("Kit consumption requires the approved work/BOM output unit identity")
    for entry in _effective_progress(doc.project, "kit_issue", doc.name):
        current_package = scoped_doc("URANOS Work Package", entry.work_package)
        if (current_package.project != doc.project or current_package.code != package.code
                or current_package.uom != package.uom or not current_package.baseline_approved):
            frappe.throw("Verified kit progress must retain the approved work package code, project and UOM")
        if (entry.activity, entry.zone, entry.crew) != (doc.activity, doc.zone, doc.crew):
            frappe.throw("Verified progress scope does not match the issued kit activity")
        for line in snapshot.items:
            amount = stock.quantity(entry.qty_verified) * line.qty_per_unit
            if amount:
                result.append(stock.VerifiedConsumption(entry.name + ":" + line.item_code, doc.project, doc.name,
                    line.item_code, amount, line.uom, _historical_actor(doc.project, entry.reported_by, "progress_report"),
                    _historical_actor(doc.project, entry.verifier, "progress_verify")))
    return tuple(result)


def _kit_returns(doc):
    rows = frappe.get_all("URANOS Kit Return", filters={"project": doc.project, "kit_issue": doc.name, "status": "Posted"}, fields=["name", "stock_entry"], limit_page_length=0)
    return tuple(_transfer_evidence(_erp_doc("Stock Entry", row.stock_entry, doc.project), doc.project, doc.name) for row in rows)


@frappe.whitelist(methods=["POST"])
def return_kit(name, prepared_stock_entry=None):
    require_post()
    security.require_roles("Storekeeper")
    doc = _locked("URANOS Kit Return", name)
    issue = scoped_doc("URANOS Kit Issue", doc.kit_issue, lock=True)
    if issue.project != doc.project or issue.status == "Closed":
        frappe.throw("Return must belong to an open issued kit")
    issued = _issued(issue)
    if doc.status == "Posted":
        if prepared_stock_entry and prepared_stock_entry != doc.stock_entry:
            frappe.throw("Return retry conflicts with posted Stock Entry")
        return _result(doc)
    if doc.status not in {"Draft", "Pending Approval"}:
        frappe.throw("Return is not available for posting")
    _warehouse(doc.to_warehouse, doc.project, {"Available", "Returns"})
    line = next((line for line in issued.kit.items if line.item_code == doc.item_code), None)
    if not line:
        frappe.throw("Returned item is not in this kit BOM")
    amount = stock.quantity(doc.returned_qty, positive=True)
    entry = _prepared_transfer(prepared_stock_entry, doc.project, issue.name) if prepared_stock_entry else _post_stock(doc.project, [{
        "item_code": line.item_code, "qty": str(amount), "uom": line.uom, "stock_uom": line.uom, "conversion_factor": 1,
        "s_warehouse": issue.to_warehouse, "t_warehouse": doc.to_warehouse, "project": doc.project, "uranos_kit_issue": issue.name}])
    if frappe.db.exists("URANOS Kit Return", {"stock_entry": entry.name, "name": ["!=", doc.name]}):
        frappe.throw("Return stock evidence is already used")
    evidence = _transfer_evidence(entry, doc.project, issue.name)
    if any(row.item_code != line.item_code or row.target_warehouse != doc.to_warehouse for row in evidence.items) or sum((row.quantity for row in evidence.items), Decimal(0)) != amount:
        frappe.throw("Return Stock Entry does not match this requested return")
    stock.reconcile_kit(issued, installed=_kit_installed(issue, issued.kit), returns=(*_kit_returns(issue), evidence), as_of=frappe.utils.getdate())
    doc.stock_entry, doc.status = entry.name, "Posted"
    return _save(doc)


def _policy(name, project, *, historical_at=None):
    doc = _erp_doc("URANOS Approval Policy", name, project)
    applicable_date = frappe.utils.getdate(historical_at) if historical_at is not None else frappe.utils.getdate()
    historical = historical_at is not None
    if ((not historical and (doc.status != "Approved" or not doc.enabled))
            or (historical and (doc.status not in {"Approved", "Retired"} or not doc.approved_by))
            or doc.action != "Stock Adjustment"):
        frappe.throw("An enabled approved stock policy is required")
    if not doc.valid_from or frappe.utils.getdate(doc.valid_from) > applicable_date or (doc.valid_to and frappe.utils.getdate(doc.valid_to) < applicable_date):
        frappe.throw("Stock approval policy is outside its validity dates")
    allowed = {"URANOS " + role for role in CAPABILITY_ROLES["stock_approve"]}
    if doc.first_role not in allowed or doc.second_role not in allowed:
        frappe.throw("Policy must designate explicit business approval roles")
    return doc, stock.ApprovalPolicy(project, doc.currency, doc.threshold)


@frappe.whitelist(methods=["POST"])
def approve_stock_policy(name):
    require_post()
    user = security.require_roles("Executive", "Finance Controller")
    doc = _locked("URANOS Approval Policy", name)
    if doc.owner == user or doc.status != "Draft":
        frappe.throw("Stock policy requires independent approval of a draft")
    stock.ApprovalPolicy(doc.project, doc.currency, doc.threshold)
    allowed = {"URANOS " + role for role in CAPABILITY_ROLES["stock_approve"]}
    if doc.action != "Stock Adjustment" or doc.first_role not in allowed or doc.second_role not in allowed:
        frappe.throw("Policy must identify approved stock business roles")
    if doc.valid_to and frappe.utils.getdate(doc.valid_to) < frappe.utils.getdate(doc.valid_from):
        frappe.throw("Policy date interval is invalid")
    doc.status, doc.approved_by = "Approved", user
    return _save(doc)


KINDS = {"Scrap": "scrap", "Variance": "variance", "Adjustment In": "adjustment_in", "Adjustment Out": "adjustment_out"}


def _disposition(doc, *, with_approvals=True):
    subject = doc.kit_issue or doc.cable_reel
    request = stock.Disposition(doc.name, doc.project, subject, doc.item_code, KINDS.get(doc.kind, "invalid"),
        doc.quantity, doc.amount, doc.currency, doc.reason,
        _historical_actor(doc.project, doc.requester, "stock_request"), _aware(doc.requested_at))
    if doc.payload_hash and doc.payload_hash != request.payload_digest:
        frappe.throw("Stock disposition changed after its approval payload was frozen")
    approvals = []
    if with_approvals:
        rows = frappe.get_all("URANOS Approval", filters={"project": doc.project,
            "reference_doctype": doc.doctype, "reference_name": doc.name, "action": "Stock Adjustment"},
            fields=["name"], limit_page_length=0)
        for row in rows:
            approval = frappe.get_doc("URANOS Approval", row.name)
            if approval.policy != doc.policy or approval.requester != doc.requester:
                frappe.throw("Approval policy/requester differs from the frozen stock request")
            approvals.append(stock.Approval(_historical_actor(doc.project, approval.approver, "stock_approve"),
                                           approval.payload_hash, _aware(approval.approved_at)))
    from dataclasses import replace
    return replace(request, approvals=tuple(approvals))


def _validate_policy_approvals(doc, request, policy_doc, policy):
    stock.validate_adjustment(request, policy)
    for instant in (request.requested_at, *(approval.approved_at for approval in request.approvals)):
        day = instant.date()
        if day < frappe.utils.getdate(policy_doc.valid_from) or (policy_doc.valid_to and day > frappe.utils.getdate(policy_doc.valid_to)):
            frappe.throw("Request/signature timestamp is outside the original policy validity interval")
    signatures = frappe.get_all("URANOS Approval", filters={"project": doc.project,
        "reference_doctype": doc.doctype, "reference_name": doc.name, "policy": doc.policy,
        "action": "Stock Adjustment", "payload_hash": request.payload_digest}, fields=["approver", "approved_roles"], limit_page_length=0)
    roles = {}
    for row in signatures:
        try:
            snapshot = json.loads(row.approved_roles or "[]")
        except (TypeError, ValueError):
            frappe.throw("Approval role snapshot is invalid")
        if not isinstance(snapshot, list) or not all(isinstance(role, str) for role in snapshot) or row.approver in roles:
            frappe.throw("Approval role snapshot is invalid or duplicated")
        roles[row.approver] = snapshot
    first = {x.actor.user for x in request.approvals if policy_doc.first_role in roles.get(x.actor.user, [])}
    second = {x.actor.user for x in request.approvals if policy_doc.second_role in roles.get(x.actor.user, [])}
    if not first or (request.value > policy.dual_approval_threshold and not any(a != b for a in first for b in second)):
        frappe.throw("Required first/second policy role signatures are missing")


def _subject_for_disposition(doc):
    if bool(doc.kit_issue) == bool(doc.cable_reel):
        frappe.throw("Stock disposition must target exactly one kit issue or cable reel")
    if doc.kit_issue:
        issue = scoped_doc("URANOS Kit Issue", doc.kit_issue, lock=True)
        snapshot = _issued(issue)
        if issue.project != doc.project or issue.status == "Closed" or doc.item_code not in {x.item_code for x in snapshot.kit.items}:
            frappe.throw("Disposition is outside the open issue/BOM")
        if doc.warehouse != issue.to_warehouse:
            frappe.throw("Kit disposition must use its WIP warehouse")
        return issue
    reel = scoped_doc("URANOS Cable Reel", doc.cable_reel, lock=True)
    if reel.project != doc.project or reel.status in {"Draft", "Closed"} or reel.item_code != doc.item_code:
        frappe.throw("Disposition is outside the open reel identity")
    _warehouse(doc.warehouse, doc.project, {"WIP", "Available"})
    return reel


@frappe.whitelist(methods=["POST"])
def request_stock_disposition(name):
    require_post()
    user = security.require_roles(*CAPABILITY_ROLES["stock_request"])
    doc = _locked("URANOS Stock Disposition", name)
    if doc.status != "Draft" or doc.requester != user:
        frappe.throw("Only the named requester can submit their draft disposition")
    _subject_for_disposition(doc)
    if doc.kind not in KINDS:
        frappe.throw("Invalid stock disposition kind")
    _warehouse(doc.warehouse, doc.project, {"WIP", "Available"})
    item = _item(doc.item_code)
    amount = stock.quantity(doc.quantity, positive=True)
    rates = frappe.db.sql("SELECT valuation_rate FROM `tabBin` WHERE item_code=%s AND warehouse=%s FOR UPDATE",
                          (item.name, doc.warehouse), as_dict=True)
    if len(rates) != 1:
        frappe.throw("Existing authoritative warehouse valuation is required")
    rate = stock.quantity(rates[0].valuation_rate, "warehouse valuation rate", positive=True)
    company = scoped_doc("Project", doc.project).company
    currency = frappe.db.get_value("Company", company, "default_currency")
    _policy_doc, policy = _policy(doc.policy, doc.project)
    if currency != policy.currency:
        frappe.throw("Approval threshold currency must match company stock valuation currency")
    doc.currency, doc.valuation_rate, doc.amount = currency, str(rate), str(amount * rate)
    doc.requested_at, doc.status = frappe.utils.now(), "Pending Approval"
    doc.payload_hash = None
    # Freeze the database-normalized currency/quantity representation, not an
    # in-memory Decimal that a Float/Currency field might normalize on save.
    _save(doc, trusted=True)
    doc.reload()
    doc.payload_hash = _disposition(doc, with_approvals=False).payload_digest
    return _save(doc, trusted=True)


@frappe.whitelist(methods=["POST"])
def approve_stock_disposition(name):
    require_post()
    user = security.require_roles(*CAPABILITY_ROLES["stock_approve"])
    doc = _locked("URANOS Stock Disposition", name)
    if doc.status not in {"Pending Approval", "Approved"} or user == doc.requester:
        frappe.throw("An independent business approver must approve a pending request")
    policy_doc, policy = _policy(doc.policy, doc.project)
    if not {policy_doc.first_role, policy_doc.second_role}.intersection(frappe.get_roles(user)):
        frappe.throw("Current user does not hold this policy's approval roles")
    request = _disposition(doc)
    if user not in {approval.actor.user for approval in request.approvals}:
        with authorized_transition():
            frappe.get_doc({"doctype": "URANOS Approval", "project": doc.project, "policy": doc.policy,
                "reference_doctype": doc.doctype, "reference_name": doc.name, "action": "Stock Adjustment",
                "payload_hash": request.payload_digest, "requester": doc.requester, "approver": user,
                "approved_roles": json.dumps(sorted(set(frappe.get_roles(user)) & {policy_doc.first_role, policy_doc.second_role})),
                "approved_at": frappe.utils.now(), "reason": doc.reason}).insert(ignore_permissions=True)
    request = _disposition(doc)
    required = 2 if request.value > policy.dual_approval_threshold else 1
    if len(request.approvals) >= required:
        _validate_policy_approvals(doc, request, policy_doc, policy)
        doc.status = "Approved"
        return _save(doc)
    return _result(doc)


@frappe.whitelist(methods=["POST"])
def post_stock_disposition(name, prepared_stock_entry=None):
    require_post()
    security.require_roles("Storekeeper", "Finance Controller")
    doc = _locked("URANOS Stock Disposition", name)
    if doc.status == "Posted":
        if prepared_stock_entry and prepared_stock_entry != doc.stock_entry:
            frappe.throw("Disposition retry conflicts with its posted stock entry")
        entry = _erp_doc("Stock Entry", doc.stock_entry, doc.project)
        if entry.docstatus != 1:
            frappe.throw("Posted stock disposition lost its submitted stock evidence")
        return _result(doc)
    if doc.status != "Approved":
        frappe.throw("Disposition must be approved before posting")
    _subject_for_disposition(doc)
    policy_doc, policy = _policy(doc.policy, doc.project)
    candidate = _disposition(doc)
    _validate_policy_approvals(doc, candidate, policy_doc, policy)
    item = _item(doc.item_code)
    valuations = frappe.db.sql("SELECT valuation_rate FROM `tabBin` WHERE item_code=%s AND warehouse=%s FOR UPDATE",
                               (item.name, doc.warehouse), as_dict=True)
    current_rate = valuations[0].valuation_rate if len(valuations) == 1 else None
    if stock.quantity(current_rate, "current valuation", positive=True) != stock.quantity(doc.valuation_rate, positive=True):
        frappe.throw("Warehouse valuation changed; obtain approvals for a fresh disposition before posting")
    if doc.kind in {"Scrap", "Variance"}:
        field, subject = ("kit_issue", doc.kit_issue) if doc.kit_issue else ("cable_reel", doc.cable_reel)
        posted, posted_policy = _posted_dispositions(doc.project, field, subject)
        combined_policy = max((p for p in (policy, posted_policy) if p is not None), key=lambda p: p.dual_approval_threshold)
        if doc.kit_issue:
            issue = scoped_doc("URANOS Kit Issue", doc.kit_issue, lock=True)
            issued = _issued(issue)
            stock.reconcile_kit(issued, installed=_kit_installed(issue, issued.kit), returns=_kit_returns(issue),
                dispositions=(*posted, candidate), policy=combined_policy, as_of=frappe.utils.getdate())
        else:
            reel_doc = scoped_doc("URANOS Cable Reel", doc.cable_reel, lock=True)
            reel = _reel(reel_doc)
            net = reel.original_length - reel.current_expected_length
            consumed = sum((stock.quantity(p.qty_verified) for p in _effective_progress(doc.project, "cable_reel", doc.cable_reel)), Decimal(0))
            if consumed + sum((p.quantity for p in (*posted, candidate)), Decimal(0)) > net:
                frappe.throw("Cable disposition exceeds unresolved dispatched length")
    incoming = doc.kind == "Adjustment In"
    row = {"item_code": item.name, "qty": str(stock.quantity(doc.quantity, positive=True)), "uom": item.stock_uom,
        "stock_uom": item.stock_uom, "conversion_factor": 1, "project": doc.project,
        "t_warehouse" if incoming else "s_warehouse": doc.warehouse,
        "uranos_kit_issue": doc.kit_issue, "uranos_reel": doc.cable_reel}
    if incoming:
        row["basic_rate"] = str(stock.quantity(doc.valuation_rate, positive=True))
    purpose = "Material Receipt" if incoming else "Material Issue"
    entry = _prepared_consumption(prepared_stock_entry, doc.project, [row], purpose=purpose,
        allowed_identities=None if incoming else _identity_balance(doc.project, doc.kit_issue or doc.cable_reel, reel=bool(doc.cable_reel))) \
        if prepared_stock_entry else _post_stock(doc.project, [row], purpose=purpose)
    doc.stock_entry, doc.status = entry.name, "Posted"
    return _save(doc)


def _posted_dispositions(project, field, subject):
    rows = frappe.get_all("URANOS Stock Disposition", filters={"project": project, field: subject,
        "status": "Posted", "kind": ["in", ["Scrap", "Variance"]]}, fields=["name"], limit_page_length=0)
    requests, policies = [], []
    for row in rows:
        doc = _erp_doc("URANOS Stock Disposition", row.name, project)
        policy_doc, policy = _policy(doc.policy, project, historical_at=doc.modified)
        request = _disposition(doc)
        _validate_policy_approvals(doc, request, policy_doc, policy)
        entry = _erp_doc("Stock Entry", doc.stock_entry, project)
        if entry.docstatus != 1 or entry.purpose != "Material Issue" or not entry.items:
            frappe.throw("Disposition no longer has matching submitted stock evidence")
        item_master = _item(doc.item_code)
        if (sum((stock.quantity(row.transfer_qty, positive=True) for row in entry.items), Decimal(0)) != request.quantity
                or any(row.item_code != doc.item_code or row.s_warehouse != doc.warehouse or row.t_warehouse
                       or row.stock_uom != item_master.stock_uom or (row.get("uranos_kit_issue") or None) != (doc.kit_issue or None)
                       or (row.get("uranos_reel") or None) != (doc.cable_reel or None) for row in entry.items)):
            frappe.throw("Disposition stock evidence differs from its approved quantity")
        requests.append(request)
        policies.append(policy)
    # Each request has passed its own frozen policy above. The aggregate domain
    # recheck must not invent a stricter threshold for another policy's request.
    currencies = {policy.currency for policy in policies}
    if len(currencies) > 1:
        frappe.throw("Reconciliation dispositions cannot mix valuation currencies")
    policy = max(policies, key=lambda p: p.dual_approval_threshold) if policies else None
    return tuple(requests), policy


def _alert(project, reference_doctype, reference_name, rule, message, *, resolved=False):
    found = frappe.db.exists("URANOS Executive Alert", {"project": project, "reference_doctype": reference_doctype,
        "reference_name": reference_name, "rule": rule, "status": ["!=", "Resolved"]})
    with authorized_transition():
        if found:
            doc = frappe.get_doc("URANOS Executive Alert", found)
            doc.message = message
            if resolved:
                doc.status = "Resolved"
            doc.save(ignore_permissions=True)
        else:
            frappe.get_doc({"doctype": "URANOS Executive Alert", "project": project, "rule": rule,
                "severity": "High", "message": message, "generated_at": frappe.utils.now(),
                "reference_doctype": reference_doctype, "reference_name": reference_name,
                "status": "Resolved" if resolved else "Open"}).insert(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def reconcile_kit_issue(name, prepared_stock_entry=None):
    require_post()
    user = security.require_roles("Storekeeper", "Site Controller", "Project Manager")
    doc = _locked("URANOS Kit Reconciliation", name)
    issue = scoped_doc("URANOS Kit Issue", doc.kit_issue, lock=True)
    if issue.project != doc.project:
        frappe.throw("Reconciliation project differs from its issue")
    if doc.status == "Closed":
        if prepared_stock_entry and prepared_stock_entry != doc.consumption_stock_entry:
            frappe.throw("Kit closure retry conflicts with its posted consumption entry")
        return _result(doc)
    if issue.status == "Closed" or doc.status not in {"Draft", "Variance Review"}:
        frappe.throw("Only an open kit may be reconciled")
    issued = _issued(issue)
    dispositions, policy = _posted_dispositions(doc.project, "kit_issue", issue.name)
    result = stock.reconcile_kit(issued, installed=_kit_installed(issue, issued.kit), returns=_kit_returns(issue),
                                 dispositions=dispositions, policy=policy, as_of=frappe.utils.getdate())
    doc.set("items", [{"item_code": line.item_code, "issued_qty": str(line.issued), "installed_qty": str(line.verified_installed),
        "returned_qty": str(line.returned), "approved_scrap_qty": str(line.approved_scrap), "variance": str(line.variance),
        "approved_variance_qty": str(line.approved_variance)} for line in result.lines])
    for alert in result.alerts:
        _alert(doc.project, "URANOS Kit Issue", issue.name, alert.rule + ":" + alert.item_code,
               f"{alert.item_code}: {alert.quantity} variance; reconcile on {alert.due_on}", resolved=alert.resolved)
    if not result.can_close:
        doc.status, issue.status = "Variance Review", "Variance Review"
        _save(issue, trusted=True)
        return _save(doc)
    if frappe.db.exists("URANOS Kit Reconciliation", {"kit_issue": issue.name, "status": "Closed", "name": ["!=", doc.name]}):
        frappe.throw("This issue has already been closed by another reconciliation")
    rows = []
    for line in result.lines:
        if line.verified_installed:
            uom = next(item.uom for item in issued.kit.items if item.item_code == line.item_code)
            rows.append({"item_code": line.item_code, "qty": str(line.verified_installed), "uom": uom, "stock_uom": uom,
                "conversion_factor": 1, "s_warehouse": issue.to_warehouse, "project": issue.project, "uranos_kit_issue": issue.name})
    if rows:
        doc.consumption_stock_entry = (_prepared_consumption(prepared_stock_entry, doc.project, rows,
            allowed_identities=_identity_balance(doc.project, issue.name)) if prepared_stock_entry
            else _post_stock(doc.project, rows, purpose="Material Issue")).name
    elif prepared_stock_entry:
        frappe.throw("No verified consumption is due; a prepared stock entry must not be posted")
    doc.status, doc.approved_by, issue.status = "Closed", user, "Closed"
    _save(issue, trusted=True)
    return _save(doc)


@frappe.whitelist(methods=["POST"])
def register_cable_reel(name):
    require_post()
    security.require_roles("Storekeeper")
    doc = _locked("URANOS Cable Reel", name)
    if doc.status != "Draft":
        frappe.throw("Only a draft reel can be registered")
    _receipt_reel_source(doc, {"Available"})
    original = stock.quantity(doc.original_length, positive=True)
    doc.current_expected_length, doc.status = str(original), "Available"
    return _save(doc)


def _receipt_reel_source(doc, allowed_states):
    item = _item(doc.item_code)
    if not item.get("uranos_reel_tracking"):
        frappe.throw("Item must be explicitly configured for cable reel tracking")
    _warehouse(doc.warehouse, doc.project, allowed_states)
    receipt = _erp_doc("Purchase Receipt", doc.purchase_receipt, doc.project)
    if receipt.docstatus != 1 or receipt.is_return:
        frappe.throw("Reel registration requires a submitted positive Purchase Receipt")
    row = next((row for row in receipt.items if row.name == doc.purchase_receipt_item), None)
    if not row or row.item_code != doc.item_code or row.warehouse != doc.warehouse or row.stock_uom != item.stock_uom:
        frappe.throw("Reel must identify its exact received item row, warehouse and stock UOM")
    original = stock.quantity(doc.original_length, positive=True)
    other = frappe.get_all("URANOS Cable Reel", filters={"project": doc.project, "purchase_receipt": receipt.name,
        "purchase_receipt_item": row.name, "status": ["!=", "Draft"], "name": ["!=", doc.name]}, fields=["original_length"], limit_page_length=0)
    if original + sum((stock.quantity(x.original_length, positive=True) for x in other), Decimal(0)) > stock.quantity(row.stock_qty, positive=True):
        frappe.throw("Reel registrations exceed the exact received cable row quantity")
    if frappe.db.exists("URANOS Cable Reel", {"reel_id": doc.reel_id, "name": ["!=", doc.name]}):
        frappe.throw("Physical reel identity is already registered")
    return item, receipt, row, original


def _accepted_receipt_inspection(project, receipt, row, inspection_name):
    inspection = frappe.get_doc("Quality Inspection", stock.identifier(inspection_name, "incoming inspection"))
    if (inspection.docstatus != 1 or inspection.status != "Accepted" or inspection.inspection_type != "Incoming"
            or inspection.get("uranos_project") != project or inspection.item_code != row.item_code
            or inspection.reference_type != "Purchase Receipt" or inspection.reference_name != receipt.name
            or row.get("quality_inspection") != inspection.name):
        frappe.throw("Release requires a submitted Accepted Incoming inspection linked to this exact project/receipt/item row")
    if sum(1 for item in receipt.items if item.get("quality_inspection") == inspection.name) != 1:
        frappe.throw("Incoming inspection cannot ambiguously authorize multiple receipt rows")
    return inspection


def _release_evidence(doc, receipt):
    source = next((row for row in receipt.items if row.name == doc.purchase_receipt_item), None)
    if not source or source.item_code != doc.item_code:
        frappe.throw("Released reel no longer matches its original Purchase Receipt item")
    _accepted_receipt_inspection(doc.project, receipt, source, doc.receipt_release_inspection)
    entry = _erp_doc("Stock Entry", doc.receipt_release_stock_entry, doc.project)
    evidence = _transfer_evidence(entry, doc.project, doc.name, reel=True)
    if (sum((row.quantity for row in evidence.items), Decimal(0)) != stock.quantity(doc.original_length, positive=True)
            or any(row.item_code != doc.item_code or row.uom != source.stock_uom or row.source_warehouse != source.warehouse
                   or row.target_warehouse != doc.warehouse for row in evidence.items)):
        frappe.throw("Reel release ledger no longer matches its receipt quantity and warehouse route")


@frappe.whitelist(methods=["POST"])
def release_received_reel(name, to_warehouse, inspection, prepared_stock_entry=None):
    require_post()
    security.require_roles("Storekeeper")
    doc = _locked("URANOS Cable Reel", name)
    if doc.get("receipt_release_stock_entry"):
        if (doc.warehouse != to_warehouse or doc.receipt_release_inspection != inspection
                or (prepared_stock_entry and doc.receipt_release_stock_entry != prepared_stock_entry)):
            frappe.throw("Reel release retry conflicts with its accepted receipt release")
        receipt = _erp_doc("Purchase Receipt", doc.purchase_receipt, doc.project)
        if receipt.docstatus != 1 or receipt.is_return:
            frappe.throw("Released reel has lost its submitted source receipt")
        _release_evidence(doc, receipt)
        return _result(doc)
    if doc.status != "Draft":
        frappe.throw("Receiving release must register a draft reel exactly once")
    item, receipt, row, original = _receipt_reel_source(doc, {"Receiving"})
    _accepted_receipt_inspection(doc.project, receipt, row, inspection)
    destination = _warehouse(to_warehouse, doc.project, {"Available"})
    if destination.company != receipt.company:
        frappe.throw("Release destination company differs from the received stock")
    rows = [{"item_code": doc.item_code, "qty": str(original), "uom": item.stock_uom, "stock_uom": item.stock_uom,
        "conversion_factor": 1, "s_warehouse": row.warehouse, "t_warehouse": destination.name,
        "project": doc.project, "uranos_reel": doc.name}]
    entry = (_prepared_consumption(prepared_stock_entry, doc.project, rows, purpose="Material Transfer",
        allowed_identities=_native_identities(receipt, row, docstatus=1, receipt=True)) if prepared_stock_entry
        else _post_stock(doc.project, rows))
    doc.warehouse, doc.current_expected_length, doc.status = destination.name, str(original), "Available"
    doc.receipt_release_stock_entry, doc.receipt_release_inspection = entry.name, inspection
    _release_evidence(doc, receipt)
    return _save(doc)


def _reel(doc):
    item = _item(doc.item_code)
    receipt = _erp_doc("Purchase Receipt", doc.purchase_receipt, doc.project)
    if receipt.docstatus != 1 or receipt.is_return:
        frappe.throw("Reel source Purchase Receipt is no longer valid")
    if doc.get("receipt_release_stock_entry"):
        _release_evidence(doc, receipt)
    result = stock.CableReel(doc.name, doc.project, doc.item_code, item.stock_uom, doc.original_length,
                             doc.warehouse, doc.purchase_receipt)
    rows = frappe.get_all("URANOS Cable Reel Movement", filters={"project": doc.project, "reel": doc.name, "status": "Posted"},
        fields=["name"], order_by="modified asc, name asc", limit_page_length=0)
    for row in rows:
        move = frappe.get_doc("URANOS Cable Reel Movement", row.name)
        if move.movement_type not in {"Issue", "Return"}:
            frappe.throw("Unsupported reel movement requires a separate approved reconciliation")
        entry = _erp_doc("Stock Entry", move.stock_entry, doc.project)
        movement = stock.ReelMovement(move.name, doc.name, doc.project, move.movement_type,
            move.issued_length if move.movement_type == "Issue" else move.returned_length,
            move.destination_circuit, _transfer_evidence(entry, doc.project, doc.name, reel=True),
            _historical_actor(doc.project, move.performed_by, "stock_issue" if move.movement_type == "Issue" else "stock_return"),
            _aware(move.modified), move.issue_movement or None)
        result = stock.apply_reel_movement(result, movement)
    if result.current_expected_length != stock.quantity(doc.current_expected_length):
        frappe.throw("Stored reel residual differs from its authoritative movement history")
    return result


@frappe.whitelist(methods=["POST"])
def post_reel_movement(name, prepared_stock_entry=None):
    require_post()
    user = security.require_roles("Storekeeper")
    doc = _locked("URANOS Cable Reel Movement", name)
    reel = scoped_doc("URANOS Cable Reel", doc.reel, lock=True)
    if reel.project != doc.project or reel.status in {"Draft", "Closed"}:
        frappe.throw("Movement requires a registered open reel in this project")
    if doc.status == "Posted":
        if prepared_stock_entry and doc.stock_entry != prepared_stock_entry:
            frappe.throw("Reel retry conflicts with its posted Stock Entry")
        _reel(reel)
        return _result(doc)
    if doc.status != "Draft" or doc.movement_type not in {"Issue", "Return"}:
        frappe.throw("Only draft issue/return movements may post through this service")
    current = _reel(reel)
    issue = doc.movement_type == "Issue"
    amount = stock.quantity(doc.issued_length if issue else doc.returned_length, positive=True)
    if stock.quantity(doc.returned_length or 0) and issue or stock.quantity(doc.issued_length or 0) and not issue:
        frappe.throw("Movement must have only one direction quantity")
    if stock.quantity(doc.scrap_length or 0) or stock.quantity(doc.installed_length or 0):
        frappe.throw("Scrap needs independent approval; installed cable comes only from verified progress")
    _warehouse(doc.from_warehouse, doc.project, {"Available"} if issue else {"WIP"})
    _warehouse(doc.to_warehouse, doc.project, {"WIP"} if issue else {"Available"})
    item = _item(reel.item_code)
    entry = _prepared_transfer(prepared_stock_entry, doc.project, doc.reel, reel=True) if prepared_stock_entry else _post_stock(doc.project, [{
        "item_code": reel.item_code, "qty": str(amount), "uom": item.stock_uom, "stock_uom": item.stock_uom,
        "conversion_factor": 1, "s_warehouse": doc.from_warehouse, "t_warehouse": doc.to_warehouse,
        "project": doc.project, "uranos_reel": reel.name}])
    movement = stock.ReelMovement(doc.name, reel.name, doc.project, doc.movement_type, amount,
        doc.destination_circuit, _transfer_evidence(entry, doc.project, reel.name, reel=True),
        _actor(doc.project, user, "stock_issue" if issue else "stock_return"), _aware(frappe.utils.now_datetime()), doc.issue_movement or None)
    revised = stock.apply_reel_movement(current, movement)
    doc.performed_by, doc.stock_entry, doc.status = user, entry.name, "Posted"
    _save(doc)
    reel.current_expected_length, reel.status = str(revised.current_expected_length), "In Use"
    _save(reel, trusted=True)
    return _result(doc)


@frappe.whitelist(methods=["POST"])
def reconcile_cable_reel(name, measured_residual, prepared_stock_entry=None):
    require_post()
    security.require_roles("Site Controller", "Project Manager")
    doc = _locked("URANOS Cable Reel", name)
    if doc.status == "Closed":
        if prepared_stock_entry and prepared_stock_entry != doc.consumption_stock_entry:
            frappe.throw("Reel closure retry conflicts with its posted consumption entry")
        if stock.quantity(measured_residual) != stock.quantity(doc.measured_length):
            frappe.throw("Closed reel retry conflicts with its final measured length")
        return _result(doc)
    if doc.status not in {"Available", "In Use", "Reconciliation"}:
        frappe.throw("Only a registered open reel may be reconciled")
    reel = _reel(doc)
    installed = []
    for progress in _effective_progress(doc.project, "cable_reel", doc.name):
        wp = scoped_doc("URANOS Work Package", progress.work_package)
        if wp.uom != reel.uom:
            frappe.throw("Cable progress must be verified in the reel stock length UOM")
        amount = stock.quantity(progress.qty_verified)
        if amount:
            installed.append(stock.VerifiedConsumption(progress.name, doc.project, doc.name, doc.item_code, amount,
                reel.uom, _historical_actor(doc.project, progress.reported_by, "progress_report"), _historical_actor(doc.project, progress.verifier, "progress_verify")))
    dispositions, policy = _posted_dispositions(doc.project, "cable_reel", doc.name)
    result = stock.reconcile_reel(reel, measured_residual=measured_residual, installed=installed,
                                  dispositions=dispositions, policy=policy, as_of=frappe.utils.getdate())
    for alert in result.alerts:
        _alert(doc.project, doc.doctype, doc.name, alert.rule, f"Reel {doc.reel_id}: {alert.quantity}; reconcile on {alert.due_on}", resolved=alert.resolved)
    doc.measured_length, doc.status = str(result.measured_residual), "Closed" if result.can_close else "Reconciliation"
    if result.can_close and result.verified_installed:
        # Consumption must be allocated to the actual WIP warehouse(s). Avoid
        # guessing which circuit warehouse supplied a verified length.
        warehouses = {line.target_warehouse for move in reel.movements if move.kind == "Issue" for line in move.stock_entry.items}
        if len(warehouses) != 1:
            frappe.throw("Multi-warehouse reel consumption needs explicit circuit allocation before closure")
        rows = [{"item_code": doc.item_code, "qty": str(result.verified_installed), "uom": reel.uom,
            "stock_uom": reel.uom, "conversion_factor": 1, "s_warehouse": next(iter(warehouses)),
            "project": doc.project, "uranos_reel": doc.name}]
        doc.consumption_stock_entry = (_prepared_consumption(prepared_stock_entry, doc.project, rows,
            allowed_identities=_identity_balance(doc.project, doc.name, reel=True)) if prepared_stock_entry
            else _post_stock(doc.project, rows, purpose="Material Issue")).name
    elif prepared_stock_entry:
        frappe.throw("No complete verified reel consumption is due; prepared entry cannot post")
    return _save(doc)
