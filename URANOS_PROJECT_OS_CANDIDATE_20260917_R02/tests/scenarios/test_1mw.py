import sys
import unittest
from decimal import Decimal
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from scripts.simulate_1mw import EvidenceLog, run_benchmark, run_scenario


class OneMWDomainScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_scenario()

    def test_procurement_and_material_traceability_scope(self):
        self.assertEqual([self.result[key] for key in ("suppliers", "purchase_orders", "shipments", "containers", "crews")], [2, 3, 2, 3, 2])
        self.assertEqual(self.result["connector_loss"], 4)
        self.assertEqual(self.result["cable_loss_m"], 20)
        self.assertEqual(self.result["reel_remaining_m"], 180)

    def test_progress_and_quality_conclude_without_double_count(self):
        self.assertEqual(self.result["partial_progress_percent"], Decimal("7.2"))
        self.assertEqual(self.result["final_progress_percent"], 100)
        self.assertEqual(self.result["completed_gates"], list(range(16)))
        self.assertEqual(self.result["commissioning_tests"], 7)
        self.assertEqual(self.result["initial_risk_status"], "Red")
        self.assertEqual(self.result["final_risk_status"], "Green")

    def test_retry_oracle_and_evidence_boundaries_explicit(self):
        self.assertEqual(self.result["offline_unique_drafts_in_oracle"], 1)
        self.assertIn("actual ERPNext supplier/PO/receipt/stock postings", self.result["not_run"])
        self.assertIn("backup and full DB/files restore", self.result["not_run"])
        self.assertGreaterEqual(len(self.result["checks"]), 50)
        self.assertTrue(all(row["status"] == "PASS" for row in self.result["checks"]))

    def test_observation_snapshot_cannot_be_changed_by_input_mutation(self):
        log = EvidenceLog()
        source = {"quantity": 10}
        log.observe("first", source)
        digest = log.verify_chain()
        source["quantity"] = 999
        self.assertEqual(log.verify_chain(), digest)
        self.assertIn('"quantity":10', log.events[0].canonical_snapshot)

    def test_scaled_benchmark_asserts_lineage_and_stock_invariants(self):
        result = run_benchmark(project_count=2, originals_per_project=100, movements_per_project=20, document_codes_per_project=3)
        self.assertEqual(result["projects"], 2)
        self.assertGreater(result["progress_entries"], 200)
        self.assertEqual(result["stock_movements"], 40)
        self.assertEqual(result["documents"], 24)
        self.assertEqual(result["verified_percent_each_project"], [Decimal("9.9")] * 2)
        self.assertFalse(result["page_latency_tested"])
        self.assertFalse(result["sql_load_tested"])


if __name__ == "__main__":
    unittest.main()
