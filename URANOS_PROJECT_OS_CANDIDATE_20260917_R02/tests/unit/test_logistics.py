"""Pure logistics tests with explicitly synthetic orders, shipments and quantities."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import unittest

from uranos_project_os.domain.stock import Actor, StockRuleError
from uranos_project_os.domain.logistics import (
    AvailableStock, Container, LogisticsRuleError, PendingSupply, PurchaseReceiptEvidence,
    Shipment, ShipmentEvent, ShipmentLine, apply_shipment_event, eta_delay_alert,
    evaluate_material_readiness, shipment_alerts,
)


PROJECT = "DEMO-PV-1MW"
NOW = datetime(2026, 9, 17, 10, tzinfo=timezone.utc)
ETA = NOW + timedelta(days=20)
ACTOR = Actor("demo-logistics", {PROJECT}, {"shipment_update"})


def shipment():
    return Shipment("DEMO-SHIPMENT", PROJECT, ETA,
                     (Container("DEMO-CONTAINER-1", "DEMO-SEAL-1", "DEMO-SHIPMENT", PROJECT),),
                     (ShipmentLine("DEMO-PO-1", "DEMO-PO-ROW-1", "DEMO-CONNECTOR", "100", "EA", "DEMO-CONTAINER-1"),))


def receipt(*, amount="100", row="PR-ROW-1", at=NOW):
    return PurchaseReceiptEvidence("DEMO-PR-1", row, PROJECT, "DEMO-SHIPMENT", "DEMO-PO-1",
                                    "DEMO-PO-ROW-1", "DEMO-CONNECTOR", amount, "EA", "DEMO-CONTAINER-1", at)


def event(*, event_id="EVENT-1", status="In Transit", at=NOW, eta=None, receipts=()):
    return ShipmentEvent(event_id, "DEMO-PROVIDER", "DEMO-SHIPMENT", PROJECT, status, "API", at, at,
                          "DEMO-source-reference", ACTOR, eta, receipts)


class ShipmentTests(unittest.TestCase):
    def test_tracking_provenance_and_timezone_required(self):
        for update in (dict(source_reference=""), dict(source_type="unknown"), dict(source_timestamp=NOW.replace(tzinfo=None)),
                       dict(source_timestamp=NOW + timedelta(minutes=1)), dict(status="Unknown")):
            with self.subTest(update=update), self.assertRaises(StockRuleError):
                replace(event(), **update)

    def test_source_receipts_and_containers_are_project_scoped(self):
        with self.assertRaises(StockRuleError):
            replace(event(), actor=Actor("outsider", {"OTHER"}, {"shipment_update"}))
        with self.assertRaises(StockRuleError):
            apply_shipment_event(shipment(), replace(event(), shipment_id="OTHER"))
        with self.assertRaises(StockRuleError):
            replace(shipment(), containers=(replace(shipment().containers[0], project="OTHER"),))

    def test_duplicate_container_seal_and_allocation_identity_rejected(self):
        for updates in (dict(containers=shipment().containers * 2), dict(items=shipment().items * 2),
                        dict(containers=(*shipment().containers, replace(shipment().containers[0], container_no="SECOND")))):
            with self.subTest(updates=updates), self.assertRaises(StockRuleError):
                replace(shipment(), **updates)

    def test_monotonic_stage_and_fresh_source_timestamp(self):
        first = apply_shipment_event(shipment(), event())
        with self.assertRaisesRegex(LogisticsRuleError, "regress"):
            apply_shipment_event(first, event(event_id="E2", status="Production", at=NOW + timedelta(minutes=1)))
        with self.assertRaisesRegex(LogisticsRuleError, "Stale"):
            apply_shipment_event(first, event(event_id="E3", status="Customs", at=NOW - timedelta(minutes=1)))
        advanced = apply_shipment_event(first, event(event_id="E4", status="Customs", at=NOW + timedelta(minutes=1)))
        self.assertEqual(advanced.status, "Customs")

    def test_exact_provider_retry_idempotent_but_payload_conflict_rejected(self):
        first = apply_shipment_event(shipment(), event())
        self.assertIs(apply_shipment_event(first, replace(event(), recorded_at=NOW + timedelta(minutes=5))), first)
        with self.assertRaisesRegex(LogisticsRuleError, "conflicts"):
            apply_shipment_event(first, event(status="Customs"))

    def test_carrier_site_received_claim_never_posts_stock(self):
        with self.assertRaisesRegex(LogisticsRuleError, "Purchase Receipt"):
            apply_shipment_event(shipment(), event(status="Site Received"))
        with self.assertRaises(StockRuleError):
            replace(receipt(), docstatus=0)
        with self.assertRaises(StockRuleError):
            replace(receipt(), docstatus=2)

    def test_partial_receipt_remains_partial_and_does_not_double_count(self):
        part = receipt(amount="60")
        first = apply_shipment_event(shipment(), event(status="Trucking", receipts=(part,)))
        self.assertEqual(next(iter(first.received_quantities.values())), 60)
        with self.assertRaises(LogisticsRuleError):
            apply_shipment_event(first, event(event_id="E2", status="Site Received", receipts=(part,)))
        received = apply_shipment_event(first, event(event_id="E3", status="Site Received", receipts=(part, receipt(amount="40", row="PR-ROW-2"))))
        self.assertEqual(received.status, "Site Received")
        self.assertEqual(len(received.receipts), 2)
        self.assertEqual(next(iter(received.received_quantities.values())), 100)
        closed = apply_shipment_event(received, event(event_id="E4", status="Closed"))
        self.assertEqual(closed.status, "Closed")
        with self.assertRaises(LogisticsRuleError):
            apply_shipment_event(closed, event(event_id="E5", status="Closed"))

    def test_receipt_must_match_project_order_item_container_uom_and_quantity(self):
        for changes in (dict(project="OTHER"), dict(shipment_id="OTHER"), dict(purchase_order="OTHER"),
                        dict(purchase_order_item="OTHER"), dict(container_no="OTHER"), dict(uom="BOX"),
                        dict(quantity="101"), dict(received_at=NOW + timedelta(days=1))):
            with self.subTest(changes=changes), self.assertRaises(StockRuleError):
                apply_shipment_event(shipment(), event(status="Site Received", receipts=(replace(receipt(), **changes),)))

    def test_duplicate_and_conflicting_receipt_row_rejected(self):
        with self.assertRaises(StockRuleError):
            event(receipts=(receipt(), receipt()))
        first = apply_shipment_event(shipment(), event(receipts=(receipt(amount="50"),)))
        with self.assertRaises(LogisticsRuleError):
            apply_shipment_event(first, event(event_id="E2", receipts=(receipt(amount="51"),)))

    def test_close_cannot_skip_receipt_stage(self):
        with self.assertRaisesRegex(LogisticsRuleError, "before closure"):
            apply_shipment_event(shipment(), event(status="Closed", receipts=(receipt(),)))

    def test_eta_threshold_is_configured_and_cumulative_from_original(self):
        with self.assertRaises(LogisticsRuleError):
            eta_delay_alert(shipment(), threshold=None)
        first = apply_shipment_event(shipment(), event(eta=ETA + timedelta(days=2)))
        self.assertIsNone(eta_delay_alert(first, threshold=timedelta(days=2)))
        second = apply_shipment_event(first, event(event_id="E2", eta=ETA + timedelta(days=3)))
        self.assertEqual(eta_delay_alert(second, threshold=timedelta(days=2)).rule, "eta_delay")
        self.assertEqual(second.original_eta, ETA)

    def test_missing_documents_overdue_and_need_date_risks_visible(self):
        late = apply_shipment_event(shipment(), event(eta=ETA + timedelta(days=3)))
        alerts = shipment_alerts(late, threshold=timedelta(days=2), as_of=(ETA + timedelta(days=5)).date(),
                                 required_documents=("BL", "packing_list"), available_documents=("BL",), need_date=ETA.date())
        self.assertEqual({x.rule for x in alerts}, {"eta_delay", "missing_documents", "after_need_date", "arrival_overdue"})


def stock(*, quantity="20", reserved="5", state="Available", warehouse="DEMO-SITE-AVAILABLE"):
    return AvailableStock(warehouse, PROJECT, "DEMO-CONNECTOR", "EA", quantity, reserved, state)


def supply(*, allocation="PO-ALLOC-1", amount="60", status="In Transit", expected=date(2026, 10, 1)):
    return PendingSupply(allocation, PROJECT, "DEMO-CONNECTOR", "EA", amount, status, expected)


def readiness(*, on_site=(), pending=(), required="100"):
    return evaluate_material_readiness(project=PROJECT, item_code="DEMO-CONNECTOR", uom="EA", required_qty=required,
                                       need_date=date(2026, 10, 2), on_site=on_site, supply=pending)


class ReadinessTests(unittest.TestCase):
    def test_in_transit_is_not_on_site_stock(self):
        result = readiness(pending=(supply(amount="100"),))
        self.assertEqual(result.on_site_available, 0)
        self.assertEqual(result.in_transit, 100)
        self.assertFalse(result.ready_now)
        self.assertEqual(result.risk, "awaiting_receipt")

    def test_reserved_quarantined_receiving_scrap_wip_and_returns_not_available(self):
        records = tuple(stock(state=state, warehouse="DEMO-" + state) for state in ("Available", "Quarantine", "Receiving", "WIP", "Returns", "Scrap"))
        self.assertEqual(readiness(on_site=records).on_site_available, 15)
        self.assertEqual(readiness(on_site=(stock(quantity="5", reserved="10"),)).on_site_available, 0)

    def test_outstanding_allocations_do_not_double_count_shipped_and_ordered(self):
        result = readiness(on_site=(stock(),), pending=(supply(), supply(allocation="P2", amount="20", status="Ordered", expected=None)))
        self.assertEqual(result.ordered_not_shipped, 20)
        self.assertEqual(result.not_ordered, 5)
        self.assertEqual(result.expected_before_need_date, 75)
        self.assertEqual(result.shortage_by_need_date, 25)
        self.assertEqual(result.risk, "shortage")
        with self.assertRaises(StockRuleError):
            readiness(pending=(supply(), supply(status="Ordered")))

    def test_unknown_or_late_eta_does_not_mask_need_date_shortage(self):
        for arrival in (None, date(2026, 10, 3)):
            with self.subTest(arrival=arrival):
                result = readiness(pending=(supply(amount="100", expected=arrival),))
                self.assertEqual(result.shortage_by_need_date, 100)
                self.assertEqual(result.not_ordered, 0)

    def test_cross_project_uom_and_duplicate_warehouse_rejected(self):
        for changes in (dict(project="OTHER"), dict(uom="BOX"), dict(item_code="OTHER")):
            with self.assertRaises(StockRuleError):
                readiness(on_site=(replace(stock(), **changes),))
        with self.assertRaises(StockRuleError):
            readiness(on_site=(stock(), stock()))

    def test_negative_nan_and_empty_identifiers_rejected(self):
        for bad in ("NaN", "Infinity", "-1", None, True):
            with self.subTest(bad=bad), self.assertRaises(StockRuleError):
                readiness(required=bad)
            with self.subTest(bad=bad), self.assertRaises(StockRuleError):
                supply(amount=bad)
        with self.assertRaises(StockRuleError):
            replace(supply(), allocation_id="")

    def test_zero_requirement_ready_without_division_by_zero(self):
        result = readiness(required="0")
        self.assertTrue(result.ready_now)
        self.assertEqual(result.risk, "ready")


if __name__ == "__main__":
    unittest.main()
