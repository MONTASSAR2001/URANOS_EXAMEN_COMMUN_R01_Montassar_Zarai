import base64
import copy
import hashlib
import unittest
from uuid import uuid4

from uranos_project_os.domain.offline import OfflineConflict, OfflineValidationError, check_retry, receipt_identity, validate_envelope


class OfflineTests(unittest.TestCase):
    def draft(self):
        return {"uuid": str(uuid4()), "operation": "progress", "project": "DEMO-A", "payload": {
            "work_package": "DEMO-A-WP", "baseline_version": "DEMO-A-B1", "crew": "DEMO-CREW",
            "posting_date": "2026-09-17", "qty_reported": "3.5", "activity": "Piling", "zone": "A"}}

    def test_trusted_values_never_accepted(self):
        for field in ["qty_verified", "verifier", "reported_by", "status", "docstatus", "owner", "project"]:
            draft = self.draft()
            draft["payload"][field] = "malicious"
            with self.subTest(field=field), self.assertRaises(OfflineValidationError):
                validate_envelope(draft)

    def test_invalid_quantities(self):
        for quantity in ["NaN", "Infinity", "-1", "0", True, [], 1e100, "0.00000000001"]:
            draft = self.draft()
            draft["payload"]["qty_reported"] = quantity
            with self.subTest(quantity=quantity), self.assertRaises(OfflineValidationError):
                validate_envelope(draft)

    def test_retry_unchanged_is_idempotent_but_changed_conflicts(self):
        draft = self.draft()
        envelope = validate_envelope(draft)
        receipt = {"sync_user": "demo@example.invalid", "project": envelope.project, "payload_hash": envelope.payload_hash,
                   "status": "Accepted", "reference_doctype": "URANOS Field Progress Entry", "reference_name": "DEMO-1"}
        self.assertTrue(check_retry(receipt, "demo@example.invalid", envelope)["duplicate"])
        draft["payload"]["qty_reported"] = "4"
        with self.assertRaises(OfflineConflict):
            check_retry(receipt, "demo@example.invalid", validate_envelope(draft))
        with self.assertRaises(OfflineConflict):
            check_retry(receipt, "other@example.invalid", envelope)

    def test_actor_scopes_identity(self):
        identity = str(uuid4())
        self.assertNotEqual(receipt_identity("a@example.invalid", identity), receipt_identity("b@example.invalid", identity))

    def test_attachment_checksum_and_type(self):
        draft = self.draft()
        content = b"\x89PNG\r\n\x1a\nsynthetic-test-fixture-not-a-real-photo"
        item = {"filename": "demo.png", "mime_type": "image/png", "sha256": hashlib.sha256(content).hexdigest(),
                "content_base64": base64.b64encode(content).decode()}
        draft["attachments"] = [item]
        self.assertEqual(validate_envelope(draft).attachments[0].content, content)
        for mutation in [{"filename": "../secret.png"}, {"sha256": "0"*64}, {"mime_type": "text/html"}, {"content_base64": "@invalid"}]:
            bad = copy.deepcopy(draft)
            bad["attachments"][0].update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(OfflineValidationError):
                validate_envelope(bad)

    def test_uuid_and_date_validation(self):
        for identity in ["", "not-uuid", str(uuid4()).upper(), "00000000-0000-0000-0000-000000000000"]:
            draft = self.draft()
            draft["uuid"] = identity
            with self.assertRaises(OfflineValidationError):
                validate_envelope(draft)
        draft = self.draft()
        draft["payload"]["posting_date"] = "2026-02-30"
        with self.assertRaises(OfflineValidationError):
            validate_envelope(draft)

    def test_missing_fields_unknown_operation_and_empty_rows(self):
        for operation in ["stock_post", "approve", "delete"]:
            draft = self.draft()
            draft["operation"] = operation
            with self.assertRaises(OfflineValidationError):
                validate_envelope(draft)
        draft = self.draft()
        draft["operation"] = "kit_return"
        draft["payload"] = {"kit_issue": "DEMO-ISSUE", "to_warehouse": "DEMO-RETURNS", "returns": []}
        with self.assertRaises(OfflineValidationError):
            validate_envelope(draft)

    def test_return_rows_have_exact_units_and_no_duplicates(self):
        draft = self.draft()
        draft["operation"] = "kit_return"
        draft["payload"] = {"kit_issue": "DEMO-ISSUE", "to_warehouse": "DEMO-RETURNS", "returns": [{"item_code": "DEMO-ITEM", "qty": "2", "uom": "Nos"}]}
        self.assertEqual(validate_envelope(draft).payload["returns"][0]["qty"], "2")
        draft["payload"]["returns"].append(draft["payload"]["returns"][0])
        with self.assertRaises(OfflineValidationError):
            validate_envelope(draft)


if __name__ == "__main__":
    unittest.main()
