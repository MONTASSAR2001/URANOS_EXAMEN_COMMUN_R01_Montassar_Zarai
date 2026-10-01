"""Unit tests for the 7-Day Verified Progress Reader.

Strictly verifies the 7 criteria specified in JALON_ENTRETIEN.md (Points 2, 3, and 4):
1. Draft/Reported lines strictly excluded from verified progress.
2. Receipts and stock movements excluded from physical progress.
3. Corrections resolved without double-counting (successor replaces predecessor).
4. Period boundaries strictly enforced over an explicit 7-calendar-day window.
5. Distinct units (UOMs) separated (never sums meters with pieces; no labour conversion).
6. Unauthorized project access or cross-project contributions strictly rejected.
7. Insufficient data explicitly flagged (absent data reported as None/unknown, not 0).
"""
import unittest
from datetime import date
from decimal import Decimal

from uranos_project_os.domain.controls import (
    RuleViolation,
    read_verified_progress_window,
    validate_baseline,
)


def sample_baseline(project="DEMO-PV-01", version="B1"):
    return validate_baseline(
        project,
        version,
        [
            {
                "name": f"{project}-WP030",
                "project": project,
                "baseline_version": version,
                "code": "WP-030",
                "title": "Battage et forage",
                "uom": "pieux",
                "qty_planned": "1000",
                "weight": "40",
            },
            {
                "name": f"{project}-WP050",
                "project": project,
                "baseline_version": version,
                "code": "WP-050",
                "title": "Pose des modules",
                "uom": "modules",
                "qty_planned": "2000",
                "weight": "40",
            },
            {
                "name": f"{project}-WP070",
                "project": project,
                "baseline_version": version,
                "code": "WP-070",
                "title": "Câblage DC",
                "uom": "m",
                "qty_planned": "5000",
                "weight": "20",
            },
        ],
    )


def verified_entry(
    name,
    wp="DEMO-PV-01-WP030",
    posting_date="2026-09-12",
    qty_reported="100",
    qty_verified="100",
    project="DEMO-PV-01",
    version="B1",
    **overrides,
):
    entry = {
        "name": name,
        "project": project,
        "work_package": wp,
        "baseline_version": version,
        "posting_date": posting_date,
        "qty_reported": str(qty_reported),
        "qty_verified": str(qty_verified),
        "reported_by": "engineer@uranos.local",
        "verifier": "controller@uranos.local",
        "status": "Verified",
        "evidence": ["/private/files/proof.jpg"],
        "activity": "INSTALL",
        "zone": "Z01",
    }
    entry.update(overrides)
    return entry


class TestSevenDayVerifiedProgress(unittest.TestCase):
    def setUp(self):
        self.project = "DEMO-PV-01"
        self.baseline = sample_baseline(self.project)
        self.start_date = "2026-09-10"
        self.end_date = "2026-09-16"  # Exactly 7 calendar days

    def test_1_draft_and_reported_lines_excluded(self):
        """Scenario 1: Draft, Reported, and Pending Verification entries are excluded from verified progress."""
        entries = [
            # Verified entry within window -> should be counted
            verified_entry("E-VERIFIED", posting_date="2026-09-12", qty_reported="150", qty_verified="120"),
            # Draft entry -> excluded
            {
                "name": "E-DRAFT",
                "project": self.project,
                "work_package": f"{self.project}-WP030",
                "baseline_version": "B1",
                "posting_date": "2026-09-12",
                "qty_reported": "200",
                "qty_verified": "0",
                "reported_by": "engineer@uranos.local",
                "status": "Draft",
            },
            # Reported / Pending Verification entry -> excluded
            {
                "name": "E-PENDING",
                "project": self.project,
                "work_package": f"{self.project}-WP030",
                "baseline_version": "B1",
                "posting_date": "2026-09-13",
                "qty_reported": "300",
                "qty_verified": "0",
                "reported_by": "engineer@uranos.local",
                "status": "Pending Verification",
            },
        ]
        result = read_verified_progress_window(
            self.project, self.baseline, entries, self.start_date, self.end_date
        )
        wp030 = next(r for r in result["work_packages"] if r["code"] == "WP-030")
        self.assertEqual(wp030["qty_verified"], Decimal("120"))
        self.assertTrue(wp030["is_measured"])

    def test_2_receipts_and_stock_issues_excluded(self):
        """Scenario 2: Receipts and stock movements are never counted as installed physical progress."""
        entries = [
            verified_entry("E-01", posting_date="2026-09-11", qty_reported="50", qty_verified="50"),
            # Purchase Receipt mock record
            {
                "doctype": "Purchase Receipt",
                "name": "MAT-REC-001",
                "project": self.project,
                "posting_date": "2026-09-12",
                "receipt_qty": 5000,
            },
            # Stock Entry mock record
            {
                "doctype": "Stock Entry",
                "name": "STE-001",
                "project": self.project,
                "posting_date": "2026-09-12",
                "stock_issued": 1000,
            },
        ]
        result = read_verified_progress_window(
            self.project, self.baseline, entries, self.start_date, self.end_date
        )
        wp030 = next(r for r in result["work_packages"] if r["code"] == "WP-030")
        # Only the verified installed entry counts
        self.assertEqual(wp030["qty_verified"], Decimal("50"))

    def test_3_correction_without_double_counting(self):
        """Scenario 3: History corrections resolve on their chain; successor replaces predecessor without double counting."""
        entries = [
            # Original verified entry: 100 pieux verified
            verified_entry(
                "E-ORIG",
                posting_date="2026-09-12",
                qty_reported="100",
                qty_verified="100",
            ),
            # Correcting entry: replaces original with 70 pieux (e.g. 30 failed pile driving torque)
            verified_entry(
                "E-CORR",
                posting_date="2026-09-14",
                qty_reported="100",
                qty_verified="70",
                correction_of="E-ORIG",
                revision_reason="30 piles failed penetration refusal test",
            ),
        ]
        result = read_verified_progress_window(
            self.project, self.baseline, entries, self.start_date, self.end_date
        )
        wp030 = next(r for r in result["work_packages"] if r["code"] == "WP-030")
        # Must be 70, NOT 100 + 70 = 170
        self.assertEqual(wp030["qty_verified"], Decimal("70"))
        self.assertEqual(result["effective_corrections"], 1)

    def test_4_period_window_boundaries(self):
        """Scenario 4: Strict 7-calendar-day window; entries before start_date or after end_date excluded."""
        entries = [
            # 1 day before start_date -> excluded
            verified_entry("E-BEFORE", posting_date="2026-09-09", qty_reported="40", qty_verified="40"),
            # On start_date -> included
            verified_entry("E-START", posting_date="2026-09-10", qty_reported="50", qty_verified="50"),
            # Inside window -> included
            verified_entry("E-MID", posting_date="2026-09-13", qty_reported="60", qty_verified="60"),
            # On end_date -> included
            verified_entry("E-END", posting_date="2026-09-16", qty_reported="70", qty_verified="70"),
            # 1 day after end_date -> excluded
            verified_entry("E-AFTER", posting_date="2026-09-17", qty_reported="80", qty_verified="80"),
        ]
        result = read_verified_progress_window(
            self.project, self.baseline, entries, self.start_date, self.end_date
        )
        wp030 = next(r for r in result["work_packages"] if r["code"] == "WP-030")
        # 50 + 60 + 70 = 180 (excluding 40 and 80)
        self.assertEqual(wp030["qty_verified"], Decimal("180"))

        # Non-7-day window rejected
        with self.assertRaises(RuleViolation):
            read_verified_progress_window(self.project, self.baseline, entries, "2026-09-10", "2026-09-17")  # 8 days!

    def test_5_two_distinct_units_kept_separate(self):
        """Scenario 5: Two distinct units (pieux vs modules vs meters) are strictly separated; never summed or converted to hours."""
        entries = [
            # WP030: pieux
            verified_entry("E-PIEUX", wp=f"{self.project}-WP030", posting_date="2026-09-11", qty_reported="250", qty_verified="250"),
            # WP050: modules
            verified_entry("E-MOD", wp=f"{self.project}-WP050", posting_date="2026-09-12", qty_reported="800", qty_verified="800"),
            # WP070: meters of cable
            verified_entry("E-CABLE", wp=f"{self.project}-WP070", posting_date="2026-09-13", qty_reported="1500", qty_verified="1500"),
        ]
        result = read_verified_progress_window(
            self.project, self.baseline, entries, self.start_date, self.end_date
        )
        units = result["units_summary"]
        self.assertEqual(units["pieux"], Decimal("250"))
        self.assertEqual(units["modules"], Decimal("800"))
        self.assertEqual(units["m"], Decimal("1500"))
        # Distinct keys maintained; no cross-unit conflation
        self.assertNotIn("hours", units)
        self.assertNotIn("labour_hours", units)

    def test_6_unauthorized_project_rejected(self):
        """Scenario 6: Cross-project progress entry or calling layer without permission is rejected with RuleViolation."""
        # 1. Foreign project entry in the list
        entries = [
            verified_entry("E-FOREIGN", project="DEMO-PV-OTHER", posting_date="2026-09-12", qty_reported="100", qty_verified="100")
        ]
        with self.assertRaises(RuleViolation):
            read_verified_progress_window(
                self.project, self.baseline, entries, self.start_date, self.end_date
            )

        # 2. Caller lacks project in permitted_projects
        with self.assertRaises(RuleViolation):
            read_verified_progress_window(
                self.project,
                self.baseline,
                [],
                self.start_date,
                self.end_date,
                permitted_projects={"OTHER-PROJECT-99"},
            )

    def test_7_insufficient_data_flagged_and_absent_as_unknown(self):
        """Scenario 7: Insufficient data explicitly flagged; absent work packages reported as None (unknown), not 0."""
        # 1. Missing baseline:
        no_baseline_res = read_verified_progress_window(
            self.project, None, [], self.start_date, self.end_date
        )
        self.assertEqual(no_baseline_res["status"], "Unknown")
        self.assertIn("approved_baseline", no_baseline_res["missing_data"])

        # 2. Baseline present, but WP070 (cables) had NO progress entries in this 7-day window:
        entries = [
            # Progress on WP030 only
            verified_entry("E-PIEUX", wp=f"{self.project}-WP030", posting_date="2026-09-12", qty_reported="100", qty_verified="100"),
            # Explicitly measured zero on WP050
            verified_entry("E-ZERO", wp=f"{self.project}-WP050", posting_date="2026-09-13", qty_reported="0", qty_verified="0"),
        ]
        result = read_verified_progress_window(
            self.project, self.baseline, entries, self.start_date, self.end_date
        )
        wp030 = next(r for r in result["work_packages"] if r["code"] == "WP-030")
        wp050 = next(r for r in result["work_packages"] if r["code"] == "WP-050")
        wp070 = next(r for r in result["work_packages"] if r["code"] == "WP-070")

        # WP030 was measured and verified: 100
        self.assertEqual(wp030["qty_verified"], Decimal("100"))
        self.assertTrue(wp030["is_measured"])

        # WP050 was measured zero: 0 (Decimal)
        self.assertEqual(wp050["qty_verified"], Decimal("0"))
        self.assertTrue(wp050["is_measured"])

        # WP070 was NEVER reported or measured in this period: None (unknown, not 0!)
        self.assertIsNone(wp070["qty_verified"])
        self.assertFalse(wp070["is_measured"])


if __name__ == "__main__":
    unittest.main()
