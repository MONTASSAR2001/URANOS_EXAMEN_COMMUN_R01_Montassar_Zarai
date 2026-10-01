"""Boundary tests using explicit Frappe stubs, NOT live ERP integration evidence."""

import importlib.util
import sys
import unittest
from contextlib import nullcontext
from datetime import date, datetime, timezone as _tz

UTC = _tz.utc
from decimal import Decimal
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import uranos_project_os
from uranos_project_os.domain import logistics, stock

ROOT = Path(__file__).resolve().parents[2]
SERVICE_PATH = ROOT / "apps" / "uranos_project_os" / "uranos_project_os" / "services"


class Record(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)


def throw(message, *args):
    raise ValueError(message)


def load_services():
    fake = ModuleType("frappe")
    fake.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    fake.throw = throw
    fake.PermissionError = PermissionError
    fake.get_doc = Mock()
    fake.db = Mock()
    fake.get_all = Mock(return_value=[])
    fake.utils = Record(get_system_timezone=lambda: "UTC", now_datetime=lambda: datetime(2026, 9, 17, 12, tzinfo=UTC),
                        get_datetime=lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(value),
                        getdate=lambda value=None: date(2026, 9, 17) if value is None else
                        value.date() if isinstance(value, datetime) else value if isinstance(value, date) else date.fromisoformat(str(value)[:10]))
    security = ModuleType("uranos_project_os.security")
    security.require_roles = Mock(return_value="demo-storekeeper")
    security.require_project = Mock()
    security.project_for = lambda doc: doc.get("project", doc.get("uranos_project"))
    controller = ModuleType("uranos_project_os.controllers")
    controller.authorized_transition = nullcontext
    common = ModuleType("uranos_project_os.services.common")
    common.require_post = Mock()
    common.scoped_doc = Mock()
    modules = {"frappe": fake, "uranos_project_os.security": security,
               "uranos_project_os.controllers": controller, "uranos_project_os.services.common": common}
    with patch.dict(sys.modules, modules), patch.object(uranos_project_os, "security", security, create=True):
        spec = importlib.util.spec_from_file_location("uranos_project_os.services.materials", SERVICE_PATH / "materials.py")
        materials = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(materials)
        with patch.dict(sys.modules, {"uranos_project_os.services.materials": materials}):
            spec = importlib.util.spec_from_file_location("uranos_project_os.services.shipments", SERVICE_PATH / "shipments.py")
            shipments = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(shipments)
    return materials, shipments, fake, security, common


class MaterialsAdapterBoundaries(unittest.TestCase):
    def setUp(self):
        self.materials, self.shipments, self.frappe, self.security, self.common = load_services()

    def test_unauthorized_issue_stops_before_any_document_or_ledger_access(self):
        self.security.require_roles.side_effect = PermissionError("denied")
        with self.assertRaises(PermissionError):
            self.materials.issue_kit("OTHER-PROJECT-ISSUE")
        self.common.scoped_doc.assert_not_called()
        self.frappe.get_doc.assert_not_called()
        self.common.require_post.assert_called_once()

    def test_unapproved_disposition_never_reaches_stock_post(self):
        doc = Record(status="Pending Approval")
        with patch.object(self.materials, "_locked", return_value=doc), patch.object(self.materials, "_post_stock") as post:
            with self.assertRaisesRegex(ValueError, "must be approved"):
                self.materials.post_stock_disposition("DISPOSITION")
            post.assert_not_called()

    def test_erp_document_cross_project_read_fails_before_financial_output(self):
        self.frappe.get_doc.return_value = Record(project="OTHER")
        with self.assertRaisesRegex(ValueError, "another project"):
            self.materials._erp_doc("Stock Entry", "SE-PRIVATE", "DEMO")

    def test_trusted_internal_read_has_fixed_doctype_allowlist(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            self.materials._erp_doc("User", "Administrator", "DEMO")
        self.frappe.get_doc.assert_not_called()

    def test_native_serial_bundle_is_required_before_auto_posting(self):
        self.common.scoped_doc.return_value = Record(company="DEMO-CO")
        tracked_item = Record(has_serial_no=1, has_batch_no=0, stock_uom="EA")
        with patch.object(self.materials, "_item", return_value=tracked_item), \
             self.assertRaisesRegex(ValueError, "native serial/batch bundle"):
            self.materials._post_stock("DEMO", [{"item_code": "SERIAL-ITEM", "stock_uom": "EA"}])
        self.frappe.get_doc.assert_not_called()

    def test_generated_stock_cannot_cross_company_warehouse_boundary(self):
        project = Record(company="DEMO-CO")
        warehouse = Record(uranos_project="DEMO", company="OTHER-CO")
        self.common.scoped_doc.side_effect = [project, warehouse]
        item = Record(has_serial_no=0, has_batch_no=0, stock_uom="EA")
        with patch.object(self.materials, "_item", return_value=item), self.assertRaisesRegex(ValueError, "company/project"):
            self.materials._post_stock("DEMO", [{"item_code": "ITEM", "stock_uom": "EA", "s_warehouse": "WH"}])
        self.frappe.get_doc.assert_not_called()

    def test_client_data_cannot_enable_arbitrary_stock_purpose(self):
        with self.assertRaisesRegex(ValueError, "Unsupported controlled"):
            self.materials._post_stock("DEMO", [], purpose="Manufacture")
        self.frappe.get_doc.assert_not_called()

    def test_public_stock_result_has_no_financial_fields(self):
        result = self.materials._result(Record(doctype="URANOS Stock Disposition", name="D", status="Pending Approval",
            modified="2026-09-17", amount=100000, valuation_rate=500, currency="PRIVATE"))
        self.assertEqual(set(result), {"doctype", "name", "status", "modified"})

    def test_packing_input_cannot_inject_item_price_or_owner(self):
        shipment = Record(name="S", project="DEMO")
        with patch.object(self.shipments, "_containers", return_value={}):
            shipment.purchase_orders = []
            with self.assertRaisesRegex(ValueError, "only purchase_order_item"):
                self.shipments._po_allocations(shipment, [{"purchase_order_item": "ROW", "container": "C", "quantity": 1, "owner": "Administrator"}])
        self.frappe.get_doc.assert_not_called()

    def test_carrier_delivered_without_receipt_cannot_persist_milestone(self):
        now = datetime(2026, 9, 17, 10, tzinfo=UTC)
        doc = Record(name="S", project="DEMO", status="Planned", modified="now")
        state = logistics.Shipment("S", "DEMO", now, (logistics.Container("C", "SEAL", "S", "DEMO"),),
            (logistics.ShipmentLine("PO", "ROW", "ITEM", 10, "EA", "C"),))
        actor = stock.Actor("demo-logistics", {"DEMO"}, {"shipment_update"})
        with patch.object(self.shipments, "_shipment", return_value=state), patch.object(self.shipments, "_event_actor", return_value=actor), \
             patch.object(self.shipments, "_receipt_evidence", return_value=()), self.assertRaisesRegex(ValueError, "Purchase Receipt"):
            self.shipments._ingest_event(doc, event_id="E", provider="test", status="Site Received", source_type="API",
                source_timestamp=now, source_reference="source", user="demo-logistics")
        self.frappe.get_doc.assert_not_called()

    def test_public_milestone_marks_human_entry_manual_not_carrier_api(self):
        with patch.object(self.shipments, "_locked", return_value=Record(name="S")), patch.object(self.shipments, "_ingest_event", return_value={}) as ingest:
            self.shipments.record_shipment_milestone("S", "E", "Departed", "2026-09-17 10:00:00", "forwarder-reference")
            self.assertEqual(ingest.call_args.kwargs["source_type"], "Manual Verified")
            self.assertEqual(ingest.call_args.kwargs["provider"], "manual:demo-storekeeper")

    def _prepared(self, *, tracked=True):
        row = Record(name="ROW-1", item_code="ITEM", stock_uom="EA", uom="EA", conversion_factor=1,
            qty=2, transfer_qty=2, s_warehouse="WIP", t_warehouse=None, project="DEMO",
            uranos_kit_issue="KIT-1", uranos_reel=None, serial_and_batch_bundle="BUNDLE-1" if tracked else None)
        entry = Record(name="STE-1", project="DEMO", company="DEMO-CO", purpose="Material Issue",
            docstatus=0, posting_date="2026-09-17", items=[row], flags=Record())
        bundle = Record(docstatus=0, voucher_type="Stock Entry", voucher_no="STE-1", voucher_detail_no="ROW-1",
            item_code="ITEM", company="DEMO-CO", warehouse="WIP", type_of_transaction="Outward",
            entries=[Record(serial_no="SERIAL-1", batch_no=None, qty=-1), Record(serial_no="SERIAL-2", batch_no=None, qty=-1)])
        item = Record(has_serial_no=int(tracked), has_batch_no=0, stock_uom="EA")
        entry.reload = Mock()
        def submit():
            entry.docstatus = 1
            bundle.docstatus = 1
        entry.submit = Mock(side_effect=submit)
        self.common.scoped_doc.side_effect = lambda kind, name: Record(company="DEMO-CO") if kind == "Project" else Record(
            company="DEMO-CO", uranos_project="DEMO", is_group=0)
        self.frappe.get_doc.return_value = bundle
        expected = [{"item_code": "ITEM", "stock_uom": "EA", "qty": "2", "s_warehouse": "WIP", "uranos_kit_issue": "KIT-1"}]
        return entry, row, bundle, item, expected

    def test_prepared_serial_consumption_submits_real_bundle_once_after_validation(self):
        entry, _row, bundle, item, expected = self._prepared()
        allowed = {("ITEM", "SERIAL:SERIAL-1"): Decimal(1), ("ITEM", "SERIAL:SERIAL-2"): Decimal(1)}
        with patch.object(self.materials, "_erp_doc", return_value=entry), patch.object(self.materials, "_item", return_value=item):
            result = self.materials._prepared_consumption(entry.name, "DEMO", expected, allowed_identities=allowed)
        self.assertIs(result, entry)
        entry.submit.assert_called_once()
        self.assertTrue(entry.flags.for_update)
        self.assertEqual(bundle.docstatus, 1)
        self.frappe.get_doc.assert_called_with("Serial and Batch Bundle", "BUNDLE-1")

    def test_prepared_quantity_route_uom_and_subject_tampering_prevent_submission(self):
        cases = (("qty", 3), ("transfer_qty", 3), ("s_warehouse", "OTHER"), ("t_warehouse", "OTHER"),
                 ("uom", "BOX"), ("stock_uom", "BOX"), ("conversion_factor", 2), ("project", "OTHER"),
                 ("uranos_kit_issue", "KIT-2"), ("uranos_reel", "REEL-1"), ("qty", "NaN"))
        for field, value in cases:
            with self.subTest(field=field, value=value):
                entry, row, _, item, expected = self._prepared()
                setattr(row, field, value)
                with patch.object(self.materials, "_erp_doc", return_value=entry), patch.object(self.materials, "_item", return_value=item), \
                     self.assertRaises((ValueError, stock.StockRuleError)):
                    self.materials._prepared_consumption(entry.name, "DEMO", expected)
                entry.submit.assert_not_called()

    def test_native_bundle_exact_voucher_row_scope_and_direction_required(self):
        for field, value in (("voucher_no", "OTHER"), ("voucher_detail_no", "OTHER"), ("warehouse", "OTHER"),
                             ("company", "OTHER"), ("item_code", "OTHER"), ("type_of_transaction", "Inward"), ("docstatus", 1)):
            with self.subTest(field=field):
                entry, _, bundle, item, expected = self._prepared()
                setattr(bundle, field, value)
                with patch.object(self.materials, "_erp_doc", return_value=entry), patch.object(self.materials, "_item", return_value=item), \
                     self.assertRaisesRegex(ValueError, "bundle must match"):
                    self.materials._prepared_consumption(entry.name, "DEMO", expected)
                entry.submit.assert_not_called()

    def test_native_missing_bundle_wrong_remaining_serial_and_duplicate_rejected(self):
        for kind in ("missing", "not-issued", "duplicate"):
            with self.subTest(kind=kind):
                entry, row, bundle, item, expected = self._prepared()
                if kind == "missing":
                    row.serial_and_batch_bundle = None
                if kind == "duplicate":
                    bundle.entries[1].serial_no = "SERIAL-1"
                allowed = {("ITEM", "SERIAL:SERIAL-1"): Decimal(1)}
                with patch.object(self.materials, "_erp_doc", return_value=entry), patch.object(self.materials, "_item", return_value=item), \
                     self.assertRaises(ValueError):
                    self.materials._prepared_consumption(entry.name, "DEMO", expected, allowed_identities=allowed)
                entry.submit.assert_not_called()

    def test_prepared_disposition_cannot_reuse_submitted_voucher(self):
        entry, _, _, item, expected = self._prepared()
        entry.docstatus = 1
        with patch.object(self.materials, "_erp_doc", return_value=entry), patch.object(self.materials, "_item", return_value=item), \
             self.assertRaisesRegex(ValueError, "unsubmitted draft"):
            self.materials._prepared_consumption(entry.name, "DEMO", expected)
        entry.submit.assert_not_called()

    def test_prepared_native_batch_quantity_and_identity_are_preserved(self):
        entry, _, bundle, item, expected = self._prepared()
        item.has_serial_no, item.has_batch_no = 0, 1
        bundle.entries = [Record(serial_no=None, batch_no="BATCH-1", qty=-2)]
        with patch.object(self.materials, "_erp_doc", return_value=entry), patch.object(self.materials, "_item", return_value=item):
            self.materials._prepared_consumption(entry.name, "DEMO", expected,
                allowed_identities={("ITEM", "BATCH:BATCH-1"): Decimal(2)})
        entry.submit.assert_called_once()

    def test_prepared_native_postcondition_failure_propagates_for_transaction_rollback(self):
        entry, row, bundle, item, expected = self._prepared()
        def mutate_after_submit():
            entry.docstatus, bundle.docstatus, row.qty = 1, 1, 999
        entry.submit.side_effect = mutate_after_submit
        with patch.object(self.materials, "_erp_doc", return_value=entry), patch.object(self.materials, "_item", return_value=item), \
             self.assertRaises(ValueError):
            self.materials._prepared_consumption(entry.name, "DEMO", expected)
        entry.submit.assert_called_once()
        # This is an exception propagation test, NOT proof of a database rollback.

    def test_expired_retired_policy_valid_at_posting_preserves_history(self):
        policy = Record(status="Retired", enabled=0, approved_by="historical-finance", action="Stock Adjustment",
            valid_from="2026-09-01", valid_to="2026-09-10", first_role="URANOS Project Manager",
            second_role="URANOS Finance Controller", currency="DEMO", threshold=50)
        with patch.object(self.materials, "_erp_doc", return_value=policy):
            self.assertEqual(self.materials._policy("POLICY", "DEMO", historical_at="2026-09-09")[1].dual_approval_threshold, 50)
            with self.assertRaises(ValueError):
                self.materials._policy("POLICY", "DEMO")
            with self.assertRaises(ValueError):
                self.materials._policy("POLICY", "DEMO", historical_at="2026-09-11")

    def test_historical_approval_roles_are_stored_snapshots_not_current_membership(self):
        policy = Record(valid_from="2026-09-01", valid_to="2026-09-10", first_role="URANOS Project Manager", second_role="URANOS Finance Controller")
        when = datetime(2026, 9, 9, 10, tzinfo=UTC)
        request = stock.Disposition("D", "DEMO", "KIT", "ITEM", "variance", 1, 100, "DEMO", "Synthetic",
            stock.Actor("requester", {"DEMO"}, {"stock_request"}), when)
        from dataclasses import replace
        request = replace(request, approvals=tuple(stock.Approval(stock.Actor(user, {"DEMO"}, {"stock_approve"}), request.payload_digest, when)
            for user in ("revoked-manager", "revoked-finance")))
        doc = Record(project="DEMO", doctype="URANOS Stock Disposition", name="D", policy="P")
        self.frappe.get_roles = Mock(side_effect=AssertionError("Historical approval must not use today's role membership"))
        self.frappe.get_all.return_value = [Record(approver="revoked-manager", approved_roles='["URANOS Project Manager"]'),
                                         Record(approver="revoked-finance", approved_roles='["URANOS Finance Controller"]')]
        self.materials._validate_policy_approvals(doc, request, policy, stock.ApprovalPolicy("DEMO", "DEMO", 50))
        self.frappe.get_roles.assert_not_called()
        policy.valid_to = "2026-09-08"
        with self.assertRaisesRegex(ValueError, "original policy validity"):
            self.materials._validate_policy_approvals(doc, request, policy, stock.ApprovalPolicy("DEMO", "DEMO", 50))

    def test_receipt_release_requires_native_accepted_exact_inspection(self):
        receipt_row = Record(item_code="CABLE", quality_inspection="QI-1")
        receipt = Record(name="PR-1", items=[receipt_row])
        good = {"name": "QI-1", "docstatus": 1, "status": "Accepted", "inspection_type": "Incoming", "uranos_project": "DEMO",
                "item_code": "CABLE", "reference_type": "Purchase Receipt", "reference_name": "PR-1"}
        self.frappe.get_doc.return_value = Record(**good)
        self.assertEqual(self.materials._accepted_receipt_inspection("DEMO", receipt, receipt_row, "QI-1").name, "QI-1")
        for key, value in (("docstatus", 0), ("status", "Rejected"), ("inspection_type", "Outgoing"),
                           ("uranos_project", "OTHER"), ("item_code", "OTHER"), ("reference_name", "OTHER")):
            with self.subTest(key=key):
                self.frappe.get_doc.return_value = Record(**(good | {key: value}))
                with self.assertRaisesRegex(ValueError, "exact project/receipt/item row"):
                    self.materials._accepted_receipt_inspection("DEMO", receipt, receipt_row, "QI-1")
        self.frappe.get_doc.return_value = Record(**good)
        receipt.items.append(Record(item_code="CABLE", quality_inspection="QI-1"))
        with self.assertRaisesRegex(ValueError, "ambiguously"):
            self.materials._accepted_receipt_inspection("DEMO", receipt, receipt_row, "QI-1")

    def test_receiving_release_posts_exact_receipt_length_and_records_retry_safe_evidence(self):
        doc = Record(name="REEL", project="DEMO", item_code="CABLE", status="Draft", warehouse="Receiving")
        source = Record(item_code="CABLE", warehouse="Receiving", quality_inspection="QI", stock_uom="M")
        receipt = Record(name="PR", company="CO", items=[source], docstatus=1, is_return=0)
        inspection = Record(name="QI", docstatus=1, status="Accepted", inspection_type="Incoming", uranos_project="DEMO",
            item_code="CABLE", reference_type="Purchase Receipt", reference_name="PR")
        self.frappe.get_doc.return_value = inspection
        with patch.object(self.materials, "_locked", return_value=doc), \
             patch.object(self.materials, "_receipt_reel_source", return_value=(Record(stock_uom="M"), receipt, source, Decimal(20))), \
             patch.object(self.materials, "_warehouse", return_value=Record(name="Available", company="CO")), \
             patch.object(self.materials, "_post_stock", return_value=Record(name="STE-RELEASE")) as post, \
             patch.object(self.materials, "_release_evidence"), patch.object(self.materials, "_save", side_effect=lambda record: {"status": record.status}):
            result = self.materials.release_received_reel("REEL", "Available", "QI")
            self.assertEqual(result["status"], "Available")
            row = post.call_args.args[1][0]
            self.assertEqual((row["qty"], row["s_warehouse"], row["t_warehouse"], row["uranos_reel"]), ("20", "Receiving", "Available", "REEL"))
            self.assertEqual(doc.receipt_release_stock_entry, "STE-RELEASE")
            self.assertEqual(doc.receipt_release_inspection, "QI")
            with self.assertRaisesRegex(ValueError, "retry conflicts"):
                self.materials.release_received_reel("REEL", "OtherWarehouse", "QI")
            post.assert_called_once()

    def test_posted_disposition_rechecks_original_date_and_accepts_multiple_native_rows(self):
        disposition = Record(name="D", policy="P", modified="2026-09-09 12:00:00", item_code="ITEM", stock_entry="STE",
            kit_issue="KIT", cable_reel=None, warehouse="WIP")
        row = Record(item_code="ITEM", transfer_qty=1, s_warehouse="WIP", t_warehouse=None,
            stock_uom="EA", uranos_kit_issue="KIT", uranos_reel=None)
        entry = Record(docstatus=1, purpose="Material Issue", items=[row, row])
        request = Record(quantity=Decimal(2))
        policy = stock.ApprovalPolicy("DEMO", "DEMO", 50)
        self.frappe.get_all.return_value = [Record(name="D")]
        with patch.object(self.materials, "_erp_doc", side_effect=[disposition, entry]), \
             patch.object(self.materials, "_policy", return_value=(Record(), policy)) as load_policy, \
             patch.object(self.materials, "_disposition", return_value=request), \
             patch.object(self.materials, "_validate_policy_approvals"), patch.object(self.materials, "_item", return_value=Record(stock_uom="EA")):
            requests, selected_policy = self.materials._posted_dispositions("DEMO", "kit_issue", "KIT")
        load_policy.assert_called_once_with("P", "DEMO", historical_at="2026-09-09 12:00:00")
        self.assertEqual(requests, (request,))
        self.assertEqual(selected_policy, policy)

    def test_revised_baseline_work_package_keeps_kit_business_identity(self):
        issue = Record(name="KIT", project="DEMO", kit_template="T", work_package="WP-OLD", activity="STRUCTURE", zone="Z1", crew="CREW")
        template = Record(output_uom="Table")
        old = Record(project="DEMO", code="WP-040", uom="Table", baseline_approved=1)
        current = Record(project="DEMO", code="WP-040", uom="Table", baseline_approved=1)
        progress = Record(name="PROGRESS", work_package="WP-NEW", activity="STRUCTURE", zone="Z1", crew="CREW",
            qty_verified=2, reported_by="historical-reporter", verifier="historical-verifier")
        self.common.scoped_doc.side_effect = lambda kind, name: {"T": template, "WP-OLD": old, "WP-NEW": current}[name]
        snapshot = Record(items=[stock.BOMLine("ITEM", 3, "EA", "R3", 0)])
        with patch.object(self.materials, "_effective_progress", return_value=[progress]):
            self.assertEqual(self.materials._kit_installed(issue, snapshot)[0].quantity, 6)
            current.uom = "Meter"
            with self.assertRaisesRegex(ValueError, "code, project and UOM"):
                self.materials._kit_installed(issue, snapshot)

    def test_kit_request_without_explicit_zone_is_rejected_before_approval(self):
        issue = Record(status="Draft Request", recorded_by="another-user", project="DEMO", kit_template="T", activity="A", work_package="WP", zone="")
        self.common.scoped_doc.return_value = Record(project="DEMO", status="Approved", activity="A")
        with patch.object(self.materials, "_locked", return_value=issue), patch.object(self.materials, "_save") as save:
            with self.assertRaisesRegex(ValueError, "zone"):
                self.materials.approve_kit_request("KIT")
            save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
