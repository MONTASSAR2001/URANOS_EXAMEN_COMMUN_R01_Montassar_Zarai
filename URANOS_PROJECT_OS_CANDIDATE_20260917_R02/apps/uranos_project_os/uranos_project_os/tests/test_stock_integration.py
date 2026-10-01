"""Native Stock Entry / Bin acceptance tests; NOT RUN on the Windows host.

Run on a disposable, migrated ERPNext v16 test site only:
bench --site TEST_SITE run-tests --app uranos_project_os --module uranos_project_os.tests.test_stock_integration

All names, quantities and values below are synthetic. Approved master-data and
verified-progress fixtures use the private transition context explicitly; this
test proves native stock workflows, not independent engineering/QA approval.
There are no Frappe mocks, external calls, commits or production credentials.
"""
import uuid
from decimal import Decimal

import frappe
from frappe.tests import IntegrationTestCase

from uranos_project_os.controllers import authorized_transition
from uranos_project_os.services import materials


class TestNativeStockIntegration(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        self.token = uuid.uuid4().hex[:10]
        self.company = frappe.get_doc({"doctype": "Company", "company_name": "Synthetic URANOS Stock " + self.token,
            "abbr": "U" + self.token[:4], "default_currency": "USD", "country": "Tunisia",
            "chart_of_accounts": "Standard", "enable_perpetual_inventory": 0}).insert(ignore_permissions=True).name
        self.project = frappe.get_doc({"doctype": "Project", "project_name": "Synthetic Stock " + self.token,
            "company": self.company, "status": "Open"}).insert().name
        self.uom = "Synthetic Unit " + self.token
        frappe.get_doc({"doctype": "UOM", "uom_name": self.uom}).insert()
        group = frappe.get_doc({"doctype": "Item Group", "item_group_name": "Synthetic Stock " + self.token,
            "parent_item_group": "All Item Groups", "is_group": 0}).insert().name
        self.item = self._item("RAW", group)
        finished = self._item("OUTPUT", group)
        self.available = self._warehouse("Available")
        self.wip = self._warehouse("WIP")
        self.storekeeper = self._user("store", "Storekeeper")
        self.reporter = self._user("team", "Team Lead")
        self.controller = self._user("verify", "Site Controller")
        self.engineer = self._user("engineer", "Engineering Director")
        with authorized_transition():
            bom = frappe.get_doc({"doctype": "BOM", "item": finished, "quantity": 1, "uom": self.uom,
                "company": self.company, "currency": "USD", "uranos_project": self.project,
                "items": [{"item_code": self.item, "qty": 2, "uom": self.uom, "stock_uom": self.uom,
                           "conversion_factor": 1, "rate": 10}]}).insert(ignore_permissions=True)
            bom.flags.ignore_permissions = True
            bom.submit()
            self.wp = frappe.get_doc({"doctype": "URANOS Work Package", "project": self.project,
                "code": "WP-SYNTHETIC", "title": "Synthetic units", "uom": self.uom, "discipline": "Electrical",
                "qty_planned": 3, "weight": 100, "baseline_version": "SYNTHETIC-V1", "baseline_approved": 1,
                "status": "Planned"}).insert(ignore_permissions=True).name
            template = frappe.get_doc({"doctype": "URANOS Material Kit Template", "project": self.project,
                "kit_code": "SYNTHETIC-KIT", "kit_version": "1", "activity": "Synthetic Installation", "source_bom": bom.name,
                "output_uom": self.uom, "bom_output_qty": 1, "status": "Approved", "approved_by": self.engineer,
                "approved_at": frappe.utils.now(), "items": [{"item_code": self.item, "qty_per_unit": 2,
                "uom": self.uom, "risk_class": "R3", "tolerance_percent": 0}]}).insert(ignore_permissions=True)
            self.issue = frappe.get_doc({"doctype": "URANOS Kit Issue", "project": self.project,
                "work_package": self.wp, "crew": "SYNTHETIC-CREW", "activity": "Synthetic Installation", "zone": "SYNTHETIC-Z1",
                "kit_template": template.name, "kit_version": "1", "qty_kits": 3, "from_warehouse": self.available,
                "to_warehouse": self.wip, "received_by": self.reporter, "status": "Approved"}).insert(ignore_permissions=True).name
        materials._post_stock(self.project, [{"item_code": self.item, "qty": 10, "uom": self.uom,
            "stock_uom": self.uom, "conversion_factor": 1, "t_warehouse": self.available,
            "project": self.project, "basic_rate": 10}], purpose="Material Receipt")

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def _item(self, suffix, group):
        return frappe.get_doc({"doctype": "Item", "item_code": "SYNTHETIC-" + suffix + "-" + self.token,
            "item_name": "Synthetic material", "item_group": group, "stock_uom": self.uom, "is_stock_item": 1,
            "uranos_risk_class": "R3"}).insert().name

    def _warehouse(self, state):
        return frappe.get_doc({"doctype": "Warehouse", "warehouse_name": "Synthetic " + state + " " + self.token,
            "company": self.company, "uranos_project": self.project, "uranos_stock_state": state,
            "is_group": 0}).insert().name

    def _user(self, label, role):
        user = frappe.get_doc({"doctype": "User", "email": f"stock-{label}-{self.token}@example.invalid",
            "first_name": "Synthetic", "send_welcome_email": 0, "roles": [{"role": "URANOS " + role}]}).insert()
        frappe.get_doc({"doctype": "User Permission", "user": user.name, "allow": "Project", "for_value": self.project,
            "apply_to_all_doctypes": 1}).insert()
        return user.name

    def _balance(self, warehouse):
        return Decimal(str(frappe.db.get_value("Bin", {"item_code": self.item, "warehouse": warehouse}, "actual_qty") or 0))

    def _issued_with_return_and_verified_fixture(self):
        frappe.set_user(self.storekeeper)
        materials.issue_kit(self.issue)
        self.assertEqual(self._balance(self.available), 4)
        self.assertEqual(self._balance(self.wip), 6)
        returned = frappe.get_doc({"doctype": "URANOS Kit Return", "project": self.project, "kit_issue": self.issue,
            "item_code": self.item, "returned_qty": 2, "to_warehouse": self.available, "status": "Draft"}).insert()
        materials.return_kit(returned.name)
        self.assertEqual(self._balance(self.available), 6)
        self.assertEqual(self._balance(self.wip), 4)
        frappe.set_user("Administrator")
        with authorized_transition():
            frappe.get_doc({"doctype": "URANOS Field Progress Entry", "project": self.project, "work_package": self.wp,
                "kit_issue": self.issue, "baseline_version": "SYNTHETIC-V1", "activity": "Synthetic Installation",
                "zone": "SYNTHETIC-Z1", "crew": "SYNTHETIC-CREW", "posting_date": frappe.utils.today(),
                "qty_reported": 2, "qty_verified": 2, "reported_by": self.reporter, "verifier": self.controller,
                "verified_at": frappe.utils.now(), "status": "Verified"}).insert(ignore_permissions=True)
        frappe.set_user(self.storekeeper)
        return frappe.get_doc({"doctype": "URANOS Kit Reconciliation", "project": self.project,
            "kit_issue": self.issue, "status": "Draft"}).insert()

    def test_native_return_and_prepared_consumption_conserve_stock_and_retry(self):
        reconciliation = self._issued_with_return_and_verified_fixture()
        frappe.set_user("Administrator")
        with authorized_transition():
            prepared = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Issue",
                "purpose": "Material Issue", "company": self.company, "project": self.project,
                "items": [{"item_code": self.item, "qty": 4, "uom": self.uom, "stock_uom": self.uom,
                    "conversion_factor": 1, "s_warehouse": self.wip, "project": self.project,
                    "uranos_kit_issue": self.issue}]}).insert(ignore_permissions=True)
        frappe.set_user(self.storekeeper)
        first = materials.reconcile_kit_issue(reconciliation.name, prepared_stock_entry=prepared.name)
        second = materials.reconcile_kit_issue(reconciliation.name, prepared_stock_entry=prepared.name)
        self.assertEqual(first["name"], second["name"])
        self.assertEqual(first["status"], "Closed")
        self.assertEqual(frappe.db.get_value("Stock Entry", prepared.name, "docstatus"), 1)
        self.assertEqual(self._balance(self.available), 6)
        self.assertEqual(self._balance(self.wip), 0)
        self.assertEqual(frappe.db.get_value("URANOS Kit Reconciliation", reconciliation.name, "consumption_stock_entry"), prepared.name)
        self.assertEqual(frappe.db.count("Stock Entry", {"name": prepared.name, "docstatus": 1}), 1)

    def test_prepared_wrong_quantity_is_rejected_before_native_submission(self):
        reconciliation = self._issued_with_return_and_verified_fixture()
        frappe.set_user("Administrator")
        with authorized_transition():
            prepared = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Issue", "purpose": "Material Issue",
                "company": self.company, "project": self.project, "items": [{"item_code": self.item, "qty": 3,
                    "uom": self.uom, "stock_uom": self.uom, "conversion_factor": 1, "s_warehouse": self.wip,
                    "project": self.project, "uranos_kit_issue": self.issue}]}).insert(ignore_permissions=True)
        frappe.set_user(self.storekeeper)
        with self.assertRaises((ValueError, frappe.ValidationError)):
            materials.reconcile_kit_issue(reconciliation.name, prepared_stock_entry=prepared.name)
        self.assertEqual(frappe.db.get_value("Stock Entry", prepared.name, "docstatus"), 0)
        self.assertEqual(self._balance(self.wip), 4)
