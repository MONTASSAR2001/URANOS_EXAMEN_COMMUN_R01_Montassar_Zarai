"""Run using bench --site TEST_SITE run-tests --app uranos_project_os.

These tests intentionally import Frappe and fail to collect without a real bench.
They are not skipped or replaced by mocks in portable unit-test evidence.
"""
import uuid

import frappe
from frappe import client
from frappe.tests import IntegrationTestCase

from uranos_project_os.controllers import authorized_transition
from uranos_project_os.security import require_roles


class TestUranosSecurity(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        self.token = uuid.uuid4().hex[:10]
        self.project_a = self._project("A")
        self.project_b = self._project("B")
        self.actor = self._user("field", ["URANOS Site Controller", "URANOS Storekeeper"])
        self.executive = self._user("exec", ["URANOS Executive"])
        self.unscoped = self._user("unscoped", ["URANOS Executive"])
        for user in (self.actor, self.executive):
            frappe.get_doc({"doctype": "User Permission", "user": user, "allow": "Project",
                            "for_value": self.project_a, "apply_to_all_doctypes": 1}).insert()
        self.daily_a = self._daily(self.project_a)
        self.daily_b = self._daily(self.project_b)

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def _project(self, suffix):
        return frappe.get_doc({"doctype": "Project", "project_name": f"URANOS TEST {self.token} {suffix}",
                               "status": "Open"}).insert().name

    def _user(self, label, roles):
        email = f"uranos-{label}-{self.token}@example.invalid"
        user = frappe.get_doc({"doctype": "User", "email": email, "first_name": "Synthetic Test",
                               "send_welcome_email": 0, "enabled": 1,
                               "roles": [{"role": role} for role in roles]}).insert(ignore_permissions=True)
        return user.name

    def _daily(self, project):
        return frappe.get_doc({"doctype": "URANOS Daily Site Report", "project": project,
                               "site": "Synthetic Site", "posting_date": "2026-09-17", "status": "Draft"}).insert().name

    def test_direct_rest_read_and_list_are_project_scoped(self):
        frappe.set_user(self.actor)
        self.assertEqual(client.get("URANOS Daily Site Report", self.daily_a)["project"], self.project_a)
        with self.assertRaises(frappe.PermissionError):
            client.get("URANOS Daily Site Report", self.daily_b)
        rows = client.get_list("URANOS Daily Site Report", fields=["name", "project"])
        self.assertTrue(rows)
        self.assertEqual({row.project for row in rows}, {self.project_a})

    def test_share_does_not_override_project_boundary(self):
        with self.assertRaises(frappe.PermissionError):
            frappe.share.add("URANOS Daily Site Report", self.daily_b, user=self.actor, read=1)
        frappe.set_user(self.actor)
        with self.assertRaises(frappe.PermissionError):
            client.get("URANOS Daily Site Report", self.daily_b)

    def test_no_grants_is_no_access_even_for_executive(self):
        frappe.set_user(self.unscoped)
        self.assertEqual(client.get_list("URANOS Daily Site Report", fields=["name"]), [])
        with self.assertRaises(frappe.PermissionError):
            client.get("URANOS Daily Site Report", self.daily_a)

    def test_original_project_cannot_be_changed(self):
        doc = frappe.get_doc("URANOS Daily Site Report", self.daily_a)
        doc.project = self.project_b
        with self.assertRaises(frappe.ValidationError):
            doc.save()

    def test_direct_status_and_client_flag_cannot_approve(self):
        frappe.set_user(self.actor)
        doc = frappe.get_doc("URANOS Daily Site Report", self.daily_a)
        doc.status = "Approved"
        doc.flags.uranos_authorized_transition = True
        with self.assertRaises(frappe.PermissionError):
            doc.save()

    def test_technical_administrator_not_implicit_business_approver(self):
        with self.assertRaises(frappe.PermissionError):
            require_roles("Site Controller")

    def test_actor_provenance_not_client_supplied(self):
        frappe.set_user(self.actor)
        doc = frappe.get_doc({"doctype": "URANOS Daily Site Report", "project": self.project_a,
                              "site": "Synthetic Other", "posting_date": "2026-09-17", "status": "Draft",
                              "recorded_by": self.executive}).insert()
        self.assertEqual(doc.recorded_by, self.actor)

    def test_native_item_money_is_masked_in_get_and_list(self):
        uom = "URANOS TEST UOM " + self.token
        frappe.get_doc({"doctype": "UOM", "uom_name": uom}).insert()
        group = "URANOS TEST GROUP " + self.token
        frappe.get_doc({"doctype": "Item Group", "item_group_name": group,
                        "parent_item_group": "All Item Groups", "is_group": 0}).insert()
        item = frappe.get_doc({"doctype": "Item", "item_code": "URANOS-TEST-" + self.token,
                               "item_name": "Synthetic Item", "item_group": group, "stock_uom": uom,
                               "is_stock_item": 0, "valuation_rate": 73, "standard_rate": 91,
                               "last_purchase_rate": 82}).insert()
        frappe.set_user(self.actor)
        result = client.get("Item", item.name)
        for key in ("valuation_rate", "standard_rate", "last_purchase_rate"):
            self.assertIn(result.get(key), (None, "", 0))
        rows = client.get_list("Item", fields=["name", "last_purchase_rate"], filters={"name": item.name})
        self.assertTrue(rows)
        self.assertNotIn("last_purchase_rate", rows[0])
        frappe.set_user(self.executive)
        financial = client.get("Item", item.name)
        self.assertEqual(financial["standard_rate"], 91)

    def test_sync_actor_uuid_unique_on_real_database(self):
        payload = {"doctype": "URANOS Offline Sync Receipt", "project": self.project_a,
                   "sync_user": self.actor, "sync_uuid": str(uuid.uuid4()), "payload_hash": "a" * 64,
                   "status": "Accepted"}
        with authorized_transition():
            frappe.get_doc(payload).insert(ignore_permissions=True)
            with self.assertRaises(frappe.UniqueValidationError):
                frappe.get_doc(payload).insert(ignore_permissions=True)

    def test_scope_query_on_native_project(self):
        frappe.set_user(self.actor)
        projects = client.get_list("Project", fields=["name"])
        self.assertEqual({row.name for row in projects}, {self.project_a})
        with self.assertRaises(frappe.PermissionError):
            client.get("Project", self.project_b)
