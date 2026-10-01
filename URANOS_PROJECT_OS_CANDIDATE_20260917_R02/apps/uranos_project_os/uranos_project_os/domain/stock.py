"""Deterministic stock controls; ERPNext documents, permissions and locks stay authoritative.

Every Actor and evidence object MUST be loaded/constructed by a trusted server
adapter. These objects are not bearer credentials and must never be deserialized
directly from an untrusted API request. Quantities are always in the stock UOM.
"""

from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Iterable


class StockRuleError(ValueError):
    """A stock invariant or required approval is missing."""


def identifier(value: str, label: str = "identifier") -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise StockRuleError(f"{label} must be a non-empty, trimmed string")
    return value


def quantity(value, label: str = "quantity", *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise StockRuleError(f"{label} must be finite numeric data")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise StockRuleError(f"{label} must be finite numeric data") from exc
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise StockRuleError(f"{label} must be finite and {'positive' if positive else 'nonnegative'}")
    return result


def timestamp(value: datetime, label: str = "timestamp") -> datetime:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise StockRuleError(f"{label} requires a timezone-aware datetime")
    return value


def _unique(values: Iterable[str], label: str) -> None:
    materialized = list(values)
    if len(materialized) != len(set(materialized)):
        raise StockRuleError(f"Duplicate {label}")


def _digest(payload) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class Actor:
    user: str
    projects: frozenset[str]
    capabilities: frozenset[str]

    def __post_init__(self):
        identifier(self.user, "user")
        object.__setattr__(self, "projects", frozenset(self.projects))
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        for project in self.projects:
            identifier(project, "project")

    def require(self, project: str, capability: str) -> None:
        identifier(project, "project")
        if project not in self.projects or capability not in self.capabilities:
            raise StockRuleError("Actor lacks project scope or required business capability")


@dataclass(frozen=True)
class Approval:
    actor: Actor
    payload_digest: str
    approved_at: datetime

    def __post_init__(self):
        identifier(self.payload_digest, "approval digest")
        timestamp(self.approved_at, "approval timestamp")


@dataclass(frozen=True)
class ApprovalPolicy:
    project: str
    currency: str
    dual_approval_threshold: Decimal

    def __post_init__(self):
        identifier(self.project, "policy project")
        identifier(self.currency, "policy currency")
        object.__setattr__(self, "dual_approval_threshold", quantity(self.dual_approval_threshold, "approval threshold"))


@dataclass(frozen=True)
class Disposition:
    """A quantity-specific approved scrap/variance or manual adjustment request."""

    reference: str
    project: str
    subject_id: str
    item_code: str
    kind: str
    quantity: Decimal
    value: Decimal
    currency: str
    reason: str
    requested_by: Actor
    requested_at: datetime
    approvals: tuple[Approval, ...] = ()

    def __post_init__(self):
        for label in ("reference", "project", "subject_id", "item_code", "currency", "reason"):
            identifier(getattr(self, label), label)
        if self.kind not in {"scrap", "variance", "adjustment_in", "adjustment_out"}:
            raise StockRuleError("Unknown disposition kind")
        object.__setattr__(self, "quantity", quantity(self.quantity, positive=True))
        object.__setattr__(self, "value", quantity(self.value, "value"))
        object.__setattr__(self, "approvals", tuple(self.approvals))
        timestamp(self.requested_at)

    @property
    def payload_digest(self) -> str:
        # The valuation must be server-derived; editing it invalidates approvals.
        return _digest([self.reference, self.project, self.subject_id, self.item_code,
                        self.kind, self.quantity, self.value, self.currency, self.reason,
                        self.requested_by.user, self.requested_at.isoformat()])


def validate_adjustment(request: Disposition, policy: ApprovalPolicy | None) -> int:
    """Require a configured threshold and independently attributable approvals.

    One approval is the minimum for every nonzero disposition; strictly ABOVE
    the configured money threshold requires two distinct authorized approvers.
    Thresholds and currency are never inferred or defaulted from demo data.
    """
    if policy is None or policy.project != request.project or policy.currency != request.currency:
        raise StockRuleError("An approved project/currency threshold policy is required")
    request.requested_by.require(request.project, "stock_request")
    required = 2 if request.value > policy.dual_approval_threshold else 1
    _unique((approval.actor.user for approval in request.approvals), "approver identity")
    for approval in request.approvals:
        approval.actor.require(request.project, "stock_approve")
        if approval.actor.user == request.requested_by.user:
            raise StockRuleError("Self approval is forbidden")
        if approval.payload_digest != request.payload_digest:
            raise StockRuleError("Approval does not bind to the current immutable request")
        if approval.approved_at < request.requested_at:
            raise StockRuleError("Approval predates its request")
    if len(request.approvals) < required:
        raise StockRuleError(f"{required} independent stock approvals required")
    return required


@dataclass(frozen=True)
class BOMLine:
    item_code: str
    qty_per_unit: Decimal
    uom: str
    risk_class: str
    tolerance_percent: Decimal
    returnable: bool = False

    def __post_init__(self):
        identifier(self.item_code, "item")
        identifier(self.uom, "UOM")
        if self.risk_class not in {"R1", "R2", "R3", "R4"}:
            raise StockRuleError("Unknown stock risk class")
        if not isinstance(self.returnable, bool):
            raise StockRuleError("Returnable must be boolean")
        object.__setattr__(self, "qty_per_unit", quantity(self.qty_per_unit, positive=True))
        tolerance = quantity(self.tolerance_percent, "per-item tolerance")
        if tolerance > 100:
            raise StockRuleError("Tolerance percent must not exceed 100")
        object.__setattr__(self, "tolerance_percent", tolerance)


@dataclass(frozen=True)
class KitVersion:
    project: str
    kit_code: str
    kit_version: str
    source_bom: str
    source_bom_version: str
    items: tuple[BOMLine, ...]
    requested_by: str
    approved_by: str
    approved_at: datetime

    def __post_init__(self):
        for label in ("project", "kit_code", "kit_version", "source_bom", "source_bom_version", "requested_by", "approved_by"):
            identifier(getattr(self, label), label)
        if self.requested_by == self.approved_by:
            raise StockRuleError("BOM author cannot approve their own kit version")
        object.__setattr__(self, "items", tuple(self.items))
        if not self.items:
            raise StockRuleError("Approved BOM must contain stock items")
        _unique((line.item_code for line in self.items), "BOM item; consolidate approved stock UOM rows first")
        timestamp(self.approved_at)

    @property
    def payload_digest(self) -> str:
        return _digest([self.project, self.kit_code, self.kit_version, self.source_bom,
                        self.source_bom_version, self.requested_by, self.approved_by,
                        self.approved_at.isoformat(), [(x.item_code, x.qty_per_unit, x.uom,
                        x.risk_class, x.tolerance_percent, x.returnable) for x in self.items]])


def approve_kit_version(*, project: str, kit_code: str, kit_version: str,
                        source_bom: str, source_bom_version: str, source_docstatus: int,
                        items: Iterable[BOMLine], requester: Actor, approver: Actor,
                        approved_at: datetime, existing: Iterable[KitVersion] = ()) -> KitVersion:
    requester.require(project, "kit_request")
    approver.require(project, "kit_approve")
    if type(source_docstatus) is not int or source_docstatus != 1:
        raise StockRuleError("Kits require a submitted, engineering-approved source BOM")
    kit = KitVersion(project, kit_code, kit_version, source_bom, source_bom_version,
                     tuple(items), requester.user, approver.user, approved_at)
    for previous in existing:
        if (previous.project, previous.kit_code, previous.kit_version) == (project, kit_code, kit_version):
            if previous != kit:
                raise StockRuleError("An approved kit version is immutable; create a new version")
            return previous
    return kit


@dataclass(frozen=True)
class StockLine:
    item_code: str
    quantity: Decimal
    uom: str
    source_warehouse: str
    target_warehouse: str
    identity: str | None = None

    def __post_init__(self):
        for label in ("item_code", "uom", "source_warehouse", "target_warehouse"):
            identifier(getattr(self, label), label)
        if self.source_warehouse == self.target_warehouse:
            raise StockRuleError("A stock transfer must change warehouse")
        if self.identity is not None:
            identifier(self.identity, "tracked identity")
        object.__setattr__(self, "quantity", quantity(self.quantity, positive=True))


@dataclass(frozen=True)
class StockEntryEvidence:
    reference: str
    project: str
    subject_id: str
    docstatus: int
    purpose: str
    items: tuple[StockLine, ...]

    def __post_init__(self):
        for label in ("reference", "project", "subject_id"):
            identifier(getattr(self, label), label)
        if type(self.docstatus) is not int or self.docstatus != 1 or self.purpose != "Material Transfer":
            raise StockRuleError("A submitted ERPNext Material Transfer Stock Entry is required")
        object.__setattr__(self, "items", tuple(self.items))
        if not self.items:
            raise StockRuleError("Stock Entry requires item rows")
        _unique(((line.item_code, line.identity) for line in self.items), "Stock Entry item/identity")


@dataclass(frozen=True)
class KitIssue:
    issue_id: str
    kit: KitVersion
    qty_kits: Decimal
    stock_entry: StockEntryEvidence
    issued_by: str
    received_by: str

    def __post_init__(self):
        for label in ("issue_id", "issued_by", "received_by"):
            identifier(getattr(self, label), label)
        object.__setattr__(self, "qty_kits", quantity(self.qty_kits, positive=True))
        if (self.stock_entry.project, self.stock_entry.subject_id) != (self.kit.project, self.issue_id):
            raise StockRuleError("Stock Entry belongs to another project or kit issue")
        expected = {x.item_code: (x.qty_per_unit * self.qty_kits, x.uom) for x in self.kit.items}
        actual = {}
        for row in self.stock_entry.items:
            if row.item_code not in expected or row.uom != expected[row.item_code][1]:
                raise StockRuleError("Issued item/UOM is outside the approved kit BOM")
            previous = actual.get(row.item_code, (Decimal(0), row.uom))[0]
            actual[row.item_code] = (previous + row.quantity, row.uom)
        if expected != actual:
            raise StockRuleError("Issued stock must match the exact approved kit BOM in stock UOM")


def build_kit_issue(*, issue_id: str, kit: KitVersion, qty_kits,
                    stock_entry: StockEntryEvidence, issuer: Actor, receiver: Actor) -> KitIssue:
    issuer.require(kit.project, "stock_issue")
    receiver.require(kit.project, "stock_receive")
    return KitIssue(issue_id, kit, qty_kits, stock_entry, issuer.user, receiver.user)


@dataclass(frozen=True)
class VerifiedConsumption:
    reference: str
    project: str
    subject_id: str
    item_code: str
    quantity: Decimal
    uom: str
    reporter: Actor
    verifier: Actor
    docstatus: int = 1

    def __post_init__(self):
        for label in ("reference", "project", "subject_id", "item_code", "uom"):
            identifier(getattr(self, label), label)
        object.__setattr__(self, "quantity", quantity(self.quantity, positive=True))
        if type(self.docstatus) is not int or self.docstatus != 1:
            raise StockRuleError("Installed consumption requires submitted verified progress evidence")
        self.reporter.require(self.project, "progress_report")
        self.verifier.require(self.project, "progress_verify")
        if self.reporter.user == self.verifier.user:
            raise StockRuleError("Reporter cannot verify their own installed consumption")


@dataclass(frozen=True)
class StockAlert:
    rule: str
    project: str
    subject_id: str
    item_code: str
    quantity: Decimal
    due_on: date
    resolved: bool


@dataclass(frozen=True)
class ReconciliationLine:
    item_code: str
    issued: Decimal
    verified_installed: Decimal
    returned: Decimal
    approved_scrap: Decimal
    variance: Decimal
    approved_variance: Decimal
    unexplained: Decimal
    over_tolerance: bool


@dataclass(frozen=True)
class ReconciliationResult:
    lines: tuple[ReconciliationLine, ...]
    can_close: bool
    alerts: tuple[StockAlert, ...]


def reconcile_kit(issue: KitIssue, *, installed: Iterable[VerifiedConsumption] = (),
                  returns: Iterable[StockEntryEvidence] = (), dispositions: Iterable[Disposition] = (),
                  policy: ApprovalPolicy | None = None, as_of: date) -> ReconciliationResult:
    installed, returns, dispositions = tuple(installed), tuple(returns), tuple(dispositions)
    if type(as_of) is not date:
        raise StockRuleError("Reconciliation date is required")
    _unique((x.reference for x in installed), "verified consumption evidence")
    _unique((x.reference for x in returns), "return stock evidence")
    _unique((x.reference for x in dispositions), "disposition reference")
    bom = {x.item_code: x for x in issue.kit.items}
    totals = {item: {kind: Decimal(0) for kind in ("installed", "returned", "scrap", "variance")} for item in bom}
    issued_rows = {(x.item_code, x.identity): x for x in issue.stock_entry.items}
    returned_by_identity = {key: Decimal(0) for key in issued_rows}
    for proof in installed:
        if (proof.project, proof.subject_id) != (issue.kit.project, issue.issue_id) or proof.item_code not in bom:
            raise StockRuleError("Verified installation is outside this issue/project/BOM")
        if proof.uom != bom[proof.item_code].uom:
            raise StockRuleError("Installed consumption must be converted to approved stock UOM")
        totals[proof.item_code]["installed"] += proof.quantity
    for entry in returns:
        if entry.reference == issue.stock_entry.reference or (entry.project, entry.subject_id) != (issue.kit.project, issue.issue_id):
            raise StockRuleError("Return must be a distinct submitted transfer for this kit issue")
        for row in entry.items:
            if row.item_code not in bom or row.uom != bom[row.item_code].uom:
                raise StockRuleError("Return item/UOM is outside the approved kit")
            key = row.item_code, row.identity
            if key not in issued_rows:
                raise StockRuleError("Return must preserve the issued tracked item identity")
            if row.source_warehouse != issued_rows[key].target_warehouse:
                raise StockRuleError("Return must leave the warehouse to which the kit was issued")
            returned_by_identity[key] += row.quantity
            if returned_by_identity[key] > issued_rows[key].quantity:
                raise StockRuleError("Return exceeds quantity issued under this tracked identity")
            totals[row.item_code]["returned"] += row.quantity
    for request in dispositions:
        if (request.project, request.subject_id) != (issue.kit.project, issue.issue_id) or request.item_code not in bom:
            raise StockRuleError("Disposition is outside this issue/project/BOM")
        if request.kind not in {"scrap", "variance"}:
            raise StockRuleError("Kit reconciliation accepts only scrap or variance dispositions")
        validate_adjustment(request, policy)
        totals[request.item_code][request.kind] += request.quantity
    lines, alerts = [], []
    for item, line in bom.items():
        amount, values = line.qty_per_unit * issue.qty_kits, totals[item]
        variance = amount - values["installed"] - values["returned"] - values["scrap"]
        unexplained = variance - values["variance"]
        if variance < 0 or unexplained < 0:
            raise StockRuleError("Installed/returned/disposed quantity exceeds issued stock")
        over_tolerance = variance > amount * line.tolerance_percent / Decimal(100)
        lines.append(ReconciliationLine(item, amount, values["installed"], values["returned"],
                                         values["scrap"], variance, values["variance"], unexplained, over_tolerance))
        if variance and (line.risk_class in {"R3", "R4"} or over_tolerance):
            alerts.append(StockAlert("high_risk_variance" if line.risk_class in {"R3", "R4"} else "stock_variance",
                                     issue.kit.project, issue.issue_id, item, variance, as_of, unexplained == 0))
    return ReconciliationResult(tuple(lines), all(x.unexplained == 0 for x in lines), tuple(alerts))


@dataclass(frozen=True)
class ReelMovement:
    movement_id: str
    reel_id: str
    project: str
    kind: str
    length: Decimal
    destination_circuit: str
    stock_entry: StockEntryEvidence
    actor: Actor
    occurred_at: datetime
    issue_movement_id: str | None = None

    def __post_init__(self):
        for label in ("movement_id", "reel_id", "project", "destination_circuit"):
            identifier(getattr(self, label), label)
        if self.kind not in {"Issue", "Return"}:
            raise StockRuleError("Unsupported reel movement kind")
        object.__setattr__(self, "length", quantity(self.length, positive=True))
        timestamp(self.occurred_at)
        self.actor.require(self.project, "stock_issue" if self.kind == "Issue" else "stock_return")
        if self.kind == "Return":
            identifier(self.issue_movement_id, "original issue movement")
        elif self.issue_movement_id is not None:
            raise StockRuleError("Issue cannot refer to a prior issue as a return")


@dataclass(frozen=True)
class CableReel:
    reel_id: str
    project: str
    item_code: str
    uom: str
    original_length: Decimal
    warehouse: str
    purchase_receipt: str
    movements: tuple[ReelMovement, ...] = ()

    def __post_init__(self):
        for label in ("reel_id", "project", "item_code", "uom", "warehouse", "purchase_receipt"):
            identifier(getattr(self, label), label)
        object.__setattr__(self, "original_length", quantity(self.original_length, positive=True))
        object.__setattr__(self, "movements", tuple(self.movements))
        _unique((x.movement_id for x in self.movements), "reel movement")
        _unique((x.stock_entry.reference for x in self.movements), "reel stock entry")
        balance = self.original_length
        issues, returned = {}, {}
        last_at = None
        for movement in self.movements:
            entry = movement.stock_entry
            if (movement.reel_id, movement.project) != (self.reel_id, self.project):
                raise StockRuleError("Reel identity/project cannot change during a movement")
            if (entry.project, entry.subject_id) != (self.project, self.reel_id):
                raise StockRuleError("Reel Stock Entry belongs to a different project or identity")
            rows = [x for x in entry.items if x.identity == self.reel_id]
            if len(rows) != 1 or (rows[0].item_code, rows[0].quantity, rows[0].uom) != (self.item_code, movement.length, self.uom):
                raise StockRuleError("Reel movement requires matching identity, item, length and stock UOM evidence")
            row = rows[0]
            if last_at is not None and movement.occurred_at < last_at:
                raise StockRuleError("Reel movements must preserve chronological history")
            last_at = movement.occurred_at
            if movement.kind == "Issue":
                if row.source_warehouse != self.warehouse:
                    raise StockRuleError("Reel must be issued from its actual warehouse")
                balance -= movement.length
                issues[movement.movement_id] = movement
                returned[movement.movement_id] = Decimal(0)
            else:
                original = issues.get(movement.issue_movement_id)
                if original is None or original.destination_circuit != movement.destination_circuit:
                    raise StockRuleError("Return must preserve the original circuit and issue identity")
                origin_row = next(x for x in original.stock_entry.items if x.identity == self.reel_id)
                if row.target_warehouse != self.warehouse or row.source_warehouse != origin_row.target_warehouse:
                    raise StockRuleError("Reel return must reverse its original warehouse route")
                returned[original.movement_id] += movement.length
                if returned[original.movement_id] > original.length:
                    raise StockRuleError("Cannot return more cable than the identified issue")
                balance += movement.length
            if balance < 0 or balance > self.original_length:
                raise StockRuleError("Reel residual length cannot be negative or exceed original length")

    @property
    def current_expected_length(self) -> Decimal:
        return self.original_length + sum((x.length if x.kind == "Return" else -x.length for x in self.movements), Decimal(0))


def apply_reel_movement(reel: CableReel, movement: ReelMovement) -> CableReel:
    for previous in reel.movements:
        if previous.movement_id == movement.movement_id:
            if previous != movement:
                raise StockRuleError("Replayed reel movement identity has conflicting content")
            return reel
    return replace(reel, movements=(*reel.movements, movement))


@dataclass(frozen=True)
class ReelReconciliation:
    expected_residual: Decimal
    measured_residual: Decimal
    issued_net: Decimal
    verified_installed: Decimal
    approved_scrap: Decimal
    approved_variance: Decimal
    unexplained: Decimal
    can_close: bool
    alerts: tuple[StockAlert, ...]


def reconcile_reel(reel: CableReel, *, measured_residual, installed: Iterable[VerifiedConsumption] = (),
                   dispositions: Iterable[Disposition] = (), policy: ApprovalPolicy | None = None,
                   as_of: date) -> ReelReconciliation:
    if type(as_of) is not date:
        raise StockRuleError("Reel reconciliation date is required")
    measured = quantity(measured_residual, "measured residual")
    if measured > reel.original_length:
        raise StockRuleError("Measured reel residual cannot exceed its original length")
    installed, dispositions = tuple(installed), tuple(dispositions)
    _unique((x.reference for x in installed), "verified reel consumption")
    _unique((x.reference for x in dispositions), "reel disposition")
    issued_net = reel.original_length - reel.current_expected_length
    installed_total, scrap, variance = Decimal(0), Decimal(0), Decimal(0)
    for proof in installed:
        if (proof.project, proof.subject_id, proof.item_code, proof.uom) != (reel.project, reel.reel_id, reel.item_code, reel.uom):
            raise StockRuleError("Installed cable evidence must retain reel/project/item/UOM identity")
        installed_total += proof.quantity
    for request in dispositions:
        if (request.project, request.subject_id, request.item_code) != (reel.project, reel.reel_id, reel.item_code):
            raise StockRuleError("Cable disposition must retain reel/project/item identity")
        validate_adjustment(request, policy)
        if request.kind == "scrap":
            scrap += request.quantity
        elif request.kind == "variance":
            variance += request.quantity
        else:
            raise StockRuleError("Reel closure only accepts scrap/variance dispositions")
    unexplained = issued_net - installed_total - scrap - variance
    if unexplained < 0:
        raise StockRuleError("Cable disposition/installation exceeds net issued length")
    alerts = []
    if unexplained + variance:
        alerts.append(StockAlert("high_risk_variance", reel.project, reel.reel_id, reel.item_code,
                                 unexplained + variance, as_of, unexplained == 0))
    if measured != reel.current_expected_length:
        alerts.append(StockAlert("reel_residual_mismatch", reel.project, reel.reel_id, reel.item_code,
                                 abs(measured - reel.current_expected_length), as_of, False))
    # A reel residual discrepancy is a separate stock adjustment; never silently
    # net it against field losses. Apply the approved ERP correction then retry.
    return ReelReconciliation(reel.current_expected_length, measured, issued_net, installed_total,
                              scrap, variance, unexplained,
                              unexplained == 0 and measured == reel.current_expected_length, tuple(alerts))
