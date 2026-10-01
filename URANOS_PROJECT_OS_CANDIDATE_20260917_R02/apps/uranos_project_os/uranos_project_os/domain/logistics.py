"""Shipment provenance and readiness calculations, without a shadow stock ledger.

Receipt/PO/stock evidence must be derived from authorized submitted ERPNext
documents by the server. Tracking providers may update transit information;
only Purchase Receipt evidence can establish a physical receipt.
"""

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable, Protocol

from .stock import Actor, StockRuleError, _digest, _unique, identifier, quantity, timestamp


class LogisticsRuleError(StockRuleError):
    """Invalid provenance, receipt, transition or material allocation."""


SHIPMENT_STATES = (
    "Planned", "PO Confirmed", "Production", "Ready for Pickup", "At Origin Port",
    "Departed", "In Transit", "Destination Port", "Customs", "Released",
    "Trucking", "Site Received", "Closed",
)
SOURCE_TYPES = frozenset({"API", "forwarder email", "manual verified", "carrier portal"})


@dataclass(frozen=True)
class Container:
    container_no: str
    seal_no: str
    shipment_id: str
    project: str

    def __post_init__(self):
        for label in ("container_no", "seal_no", "shipment_id", "project"):
            identifier(getattr(self, label), label)


@dataclass(frozen=True)
class ShipmentLine:
    """Outstanding allocation from a submitted Purchase Order stock-UOM row."""

    purchase_order: str
    purchase_order_item: str
    item_code: str
    quantity: Decimal
    uom: str
    container_no: str

    def __post_init__(self):
        for label in ("purchase_order", "purchase_order_item", "item_code", "uom", "container_no"):
            identifier(getattr(self, label), label)
        object.__setattr__(self, "quantity", quantity(self.quantity, positive=True))

    @property
    def allocation_key(self) -> tuple[str, str, str, str, str]:
        return self.purchase_order, self.purchase_order_item, self.item_code, self.uom, self.container_no


@dataclass(frozen=True)
class PurchaseReceiptEvidence:
    reference: str
    row_id: str
    project: str
    shipment_id: str
    purchase_order: str
    purchase_order_item: str
    item_code: str
    quantity: Decimal
    uom: str
    container_no: str
    received_at: datetime
    docstatus: int = 1

    def __post_init__(self):
        for label in ("reference", "row_id", "project", "shipment_id", "purchase_order",
                      "purchase_order_item", "item_code", "uom", "container_no"):
            identifier(getattr(self, label), label)
        if type(self.docstatus) is not int or self.docstatus != 1:
            raise LogisticsRuleError("Only a submitted ERPNext Purchase Receipt establishes site receipt")
        object.__setattr__(self, "quantity", quantity(self.quantity, positive=True))
        timestamp(self.received_at)

    @property
    def allocation_key(self) -> tuple[str, str, str, str, str]:
        return self.purchase_order, self.purchase_order_item, self.item_code, self.uom, self.container_no

    @property
    def receipt_key(self) -> tuple[str, str]:
        return self.reference, self.row_id


@dataclass(frozen=True)
class ShipmentEvent:
    event_id: str
    provider: str
    shipment_id: str
    project: str
    status: str
    source_type: str
    source_timestamp: datetime
    recorded_at: datetime
    source_reference: str
    actor: Actor
    eta: datetime | None = None
    receipts: tuple[PurchaseReceiptEvidence, ...] = ()

    def __post_init__(self):
        for label in ("event_id", "provider", "shipment_id", "project", "source_reference"):
            identifier(getattr(self, label), label)
        if self.status not in SHIPMENT_STATES or self.source_type not in SOURCE_TYPES:
            raise LogisticsRuleError("Unknown shipment milestone or source provenance")
        timestamp(self.source_timestamp)
        timestamp(self.recorded_at)
        if self.source_timestamp > self.recorded_at:
            raise LogisticsRuleError("Source event cannot be timestamped after server reception")
        if self.eta is not None:
            timestamp(self.eta, "ETA")
        self.actor.require(self.project, "shipment_update")
        object.__setattr__(self, "receipts", tuple(self.receipts))
        _unique((x.receipt_key for x in self.receipts), "Purchase Receipt row in event")

    @property
    def event_key(self) -> tuple[str, str]:
        return self.provider, self.event_id

    @property
    def payload_digest(self) -> str:
        # recorded_at is server ingestion time, so a network retry may differ.
        # Effective permissions may also change; bind the durable actor identity.
        return _digest([self.event_id, self.provider, self.shipment_id, self.project,
                        self.status, self.source_type, self.source_timestamp.isoformat(),
                        self.source_reference, self.actor.user, self.eta,
                        [(x.receipt_key, x.project, x.shipment_id, x.allocation_key,
                          x.quantity, x.received_at.isoformat(), x.docstatus) for x in self.receipts]])


@dataclass(frozen=True)
class Shipment:
    shipment_id: str
    project: str
    original_eta: datetime
    containers: tuple[Container, ...]
    items: tuple[ShipmentLine, ...]
    events: tuple[ShipmentEvent, ...] = ()

    def __post_init__(self):
        identifier(self.shipment_id, "shipment")
        identifier(self.project, "project")
        timestamp(self.original_eta, "original ETA")
        object.__setattr__(self, "containers", tuple(self.containers))
        object.__setattr__(self, "items", tuple(self.items))
        object.__setattr__(self, "events", tuple(self.events))
        if not self.containers or not self.items:
            raise LogisticsRuleError("Shipment requires container and approved PO allocations")
        _unique((x.container_no for x in self.containers), "container identity")
        _unique((x.seal_no for x in self.containers), "container seal identity")
        _unique((x.allocation_key for x in self.items), "shipment PO allocation")
        _unique((x.event_key for x in self.events), "shipment provider event identity")
        for container in self.containers:
            if (container.project, container.shipment_id) != (self.project, self.shipment_id):
                raise LogisticsRuleError("Container is outside this shipment/project")
        containers = {x.container_no for x in self.containers}
        if any(line.container_no not in containers for line in self.items):
            raise LogisticsRuleError("PO allocation has an unknown container")
        allocations = {x.allocation_key: x.quantity for x in self.items}
        received = {key: Decimal(0) for key in allocations}
        seen_receipts = {}
        previous_status, previous_at = "Planned", None
        for event in self.events:
            if (event.project, event.shipment_id) != (self.project, self.shipment_id):
                raise LogisticsRuleError("Tracking event belongs to another shipment/project")
            if previous_status == "Closed":
                raise LogisticsRuleError("Closed shipment cannot receive new operational events")
            if SHIPMENT_STATES.index(event.status) < SHIPMENT_STATES.index(previous_status):
                raise LogisticsRuleError("Shipment status cannot regress")
            if previous_at is not None and event.source_timestamp < previous_at:
                raise LogisticsRuleError("Stale provider events cannot replace newer accepted state")
            for receipt in event.receipts:
                if (receipt.project, receipt.shipment_id) != (self.project, self.shipment_id):
                    raise LogisticsRuleError("Purchase Receipt is outside this shipment/project")
                if receipt.received_at > event.recorded_at:
                    raise LogisticsRuleError("A future Purchase Receipt cannot establish current stock")
                if receipt.allocation_key not in allocations:
                    raise LogisticsRuleError("Purchase Receipt does not match an allocated PO/item/container/UOM")
                if receipt.receipt_key in seen_receipts:
                    if seen_receipts[receipt.receipt_key] != receipt:
                        raise LogisticsRuleError("Reused Purchase Receipt row has conflicting content")
                    continue
                seen_receipts[receipt.receipt_key] = receipt
                received[receipt.allocation_key] += receipt.quantity
                if received[receipt.allocation_key] > allocations[receipt.allocation_key]:
                    raise LogisticsRuleError("Received quantity exceeds shipment packing allocation; reconcile discrepancy first")
            if event.status in {"Site Received", "Closed"} and received != allocations:
                raise LogisticsRuleError("Site Received requires full, submitted Purchase Receipt evidence")
            if event.status == "Closed" and previous_status != "Site Received":
                raise LogisticsRuleError("Shipment must be Site Received before closure")
            previous_status, previous_at = event.status, event.source_timestamp

    @property
    def status(self) -> str:
        return self.events[-1].status if self.events else "Planned"

    @property
    def current_eta(self) -> datetime:
        return next((event.eta for event in reversed(self.events) if event.eta is not None), self.original_eta)

    @property
    def receipts(self) -> tuple[PurchaseReceiptEvidence, ...]:
        return tuple({receipt.receipt_key: receipt for event in self.events for receipt in event.receipts}.values())

    @property
    def received_quantities(self) -> dict[tuple[str, str, str, str, str], Decimal]:
        result = {line.allocation_key: Decimal(0) for line in self.items}
        for receipt in self.receipts:
            result[receipt.allocation_key] += receipt.quantity
        return result


def apply_shipment_event(shipment: Shipment, event: ShipmentEvent) -> Shipment:
    """Retry-safe state transition; caller still needs a database lock + unique key.

    Stale and conflicting events raise and must be retained by the integration
    adapter's error/audit log. They must not be silently marked synchronized.
    """
    for previous in shipment.events:
        if previous.event_key == event.event_key:
            if previous.payload_digest != event.payload_digest:
                raise LogisticsRuleError("Provider event identity conflicts with its previously accepted payload")
            return shipment
    return replace(shipment, events=(*shipment.events, event))


class ShipmentProvider(Protocol):
    """Provider-neutral read adapter; implementations never post stock receipts."""

    def fetch_events(self, shipment_reference: str, cursor: str | None) -> tuple[tuple[ShipmentEvent, ...], str | None]: ...


@dataclass(frozen=True)
class LogisticsAlert:
    rule: str
    shipment_id: str
    project: str
    message: str


def eta_delay_alert(shipment: Shipment, *, threshold: timedelta | None) -> LogisticsAlert | None:
    if not isinstance(threshold, timedelta) or threshold < timedelta(0):
        raise LogisticsRuleError("A configured nonnegative ETA delay threshold is required")
    if shipment.current_eta - shipment.original_eta > threshold:
        return LogisticsAlert("eta_delay", shipment.shipment_id, shipment.project,
                              "Revised ETA exceeds the configured delay threshold against original ETA")
    return None


def shipment_alerts(shipment: Shipment, *, threshold: timedelta | None, as_of: date,
                    required_documents: Iterable[str], available_documents: Iterable[str],
                    need_date: date | None = None) -> tuple[LogisticsAlert, ...]:
    if type(as_of) is not date or (need_date is not None and type(need_date) is not date):
        raise LogisticsRuleError("Alert dates must be dates")
    required, available = set(required_documents), set(available_documents)
    for document in required | available:
        identifier(document, "shipment document requirement")
    alerts = []
    eta_alert = eta_delay_alert(shipment, threshold=threshold)
    if eta_alert:
        alerts.append(eta_alert)
    if required - available and shipment.status not in {"Site Received", "Closed"}:
        alerts.append(LogisticsAlert("missing_documents", shipment.shipment_id, shipment.project,
                                     "Missing required documents: " + ", ".join(sorted(required - available))))
    if need_date and shipment.current_eta.date() > need_date and shipment.status not in {"Site Received", "Closed"}:
        alerts.append(LogisticsAlert("after_need_date", shipment.shipment_id, shipment.project,
                                     "Material ETA is after its work package need date"))
    if shipment.current_eta.date() < as_of and shipment.status not in {"Site Received", "Closed"}:
        alerts.append(LogisticsAlert("arrival_overdue", shipment.shipment_id, shipment.project,
                                     "ETA has elapsed without complete Purchase Receipt confirmation"))
    return tuple(alerts)


@dataclass(frozen=True)
class AvailableStock:
    warehouse: str
    project: str
    item_code: str
    uom: str
    on_hand: Decimal
    reserved_elsewhere: Decimal
    warehouse_state: str

    def __post_init__(self):
        for label in ("warehouse", "project", "item_code", "uom"):
            identifier(getattr(self, label), label)
        object.__setattr__(self, "on_hand", quantity(self.on_hand, "on-hand quantity"))
        object.__setattr__(self, "reserved_elsewhere", quantity(self.reserved_elsewhere, "reserved quantity"))
        if self.warehouse_state not in {"Available", "Receiving", "Quarantine", "WIP", "Returns", "Scrap"}:
            raise LogisticsRuleError("Unknown warehouse availability state")

    @property
    def available(self) -> Decimal:
        return max(self.on_hand - self.reserved_elsewhere, Decimal(0)) if self.warehouse_state == "Available" else Decimal(0)


@dataclass(frozen=True)
class PendingSupply:
    """An exclusive outstanding PO allocation; shipped and ordered are disjoint."""

    allocation_id: str
    project: str
    item_code: str
    uom: str
    quantity: Decimal
    status: str
    expected_date: date | None

    def __post_init__(self):
        for label in ("allocation_id", "project", "item_code", "uom"):
            identifier(getattr(self, label), label)
        object.__setattr__(self, "quantity", quantity(self.quantity, positive=True))
        if self.status not in {"Ordered", "In Transit"}:
            raise LogisticsRuleError("Supply must be an exclusive ordered or in-transit outstanding quantity")
        if self.expected_date is not None and type(self.expected_date) is not date:
            raise LogisticsRuleError("Expected supply date must be a date or unknown")


@dataclass(frozen=True)
class MaterialReadiness:
    required_qty: Decimal
    on_site_available: Decimal
    in_transit: Decimal
    ordered_not_shipped: Decimal
    not_ordered: Decimal
    expected_before_need_date: Decimal
    shortage_by_need_date: Decimal
    ready_now: bool
    risk: str


def evaluate_material_readiness(*, project: str, item_code: str, uom: str, required_qty,
                                need_date: date, on_site: Iterable[AvailableStock] = (),
                                supply: Iterable[PendingSupply] = ()) -> MaterialReadiness:
    for value in (project, item_code, uom):
        identifier(value)
    required = quantity(required_qty, "required quantity")
    if type(need_date) is not date:
        raise LogisticsRuleError("Work package need date must be provided")
    on_site, supply = tuple(on_site), tuple(supply)
    _unique((x.warehouse for x in on_site), "available stock warehouse")
    _unique((x.allocation_id for x in supply), "pending PO allocation")
    for record in (*on_site, *supply):
        if (record.project, record.item_code, record.uom) != (project, item_code, uom):
            raise LogisticsRuleError("Material readiness cannot mix projects, items or UOMs")
    available = sum((x.available for x in on_site), Decimal(0))
    in_transit = sum((x.quantity for x in supply if x.status == "In Transit"), Decimal(0))
    ordered = sum((x.quantity for x in supply if x.status == "Ordered"), Decimal(0))
    timely = available + sum((x.quantity for x in supply if x.expected_date is not None and x.expected_date <= need_date), Decimal(0))
    unplaced, shortage = max(required - available - in_transit - ordered, Decimal(0)), max(required - timely, Decimal(0))
    ready = available >= required
    risk = "ready" if ready else "shortage" if shortage > 0 else "awaiting_receipt"
    return MaterialReadiness(required, available, in_transit, ordered, unplaced, timely, shortage, ready, risk)
