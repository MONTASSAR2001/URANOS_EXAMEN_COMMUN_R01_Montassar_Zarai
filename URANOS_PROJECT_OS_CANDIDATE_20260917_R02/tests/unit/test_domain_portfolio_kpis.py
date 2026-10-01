"""Unit tests for URANOS Portfolio Dashboard KPIs (Pure Domain).

Tests pure domain calculations in domain/controls.py.
"""
from decimal import Decimal
import unittest

from uranos_project_os.domain.controls import RuleViolation, portfolio_kpi_summary


class PortfolioDomainKPITests(unittest.TestCase):
    def test_empty_inputs_return_zero_metrics(self):
        summary = portfolio_kpi_summary([], [], [])
        self.assertEqual(summary["total_sites"], 0)
        self.assertEqual(summary["active_sites"], 0)
        self.assertEqual(summary["operational_rate_percent"], Decimal(0))
        self.assertEqual(summary["total_capacity_mw"], Decimal(0))
        self.assertEqual(summary["total_capacity_dc_mwp"], Decimal(0))
        self.assertEqual(summary["lost_hours"], Decimal(0))
        self.assertEqual(summary["active_blockers_count"], 0)
        self.assertEqual(summary["total_blockers_count"], 0)
        self.assertEqual(summary["energy_today_mwh"], Decimal(0))
        self.assertEqual(summary["co2_avoided_t"], Decimal(0))

    def test_exact_portfolio_aggregates(self):
        projects = [
            {"name": "PV-01", "status": "Open"},
            {"name": "PV-02", "status": "In Progress"},
            {"name": "PV-03", "status": "Closed"},
            {"name": "PV-04", "status": "Cancelled"},
        ]
        profiles = [
            {"project": "PV-01", "capacity_ac_mw": "10.5", "capacity_dc_mwp": "12.6"},
            {"project": "PV-02", "capacity_ac_mw": "5.0", "capacity_dc_mwp": "6.0"},
            {"project": "PV-03", "capacity_ac_mw": "20.0", "capacity_dc_mwp": "24.0"},
        ]
        blockers = [
            {"project": "PV-01", "status": "Open", "lost_hours": "4.5"},
            {"project": "PV-01", "status": "In Progress", "lost_hours": "12.0"},
            {"project": "PV-02", "status": "Pending Verification", "lost_hours": "8.0"},
            {"project": "PV-03", "status": "Closed", "lost_hours": "15.0"},
        ]

        summary = portfolio_kpi_summary(projects, profiles, blockers)

        self.assertEqual(summary["total_sites"], 4)
        self.assertEqual(summary["active_sites"], 2)  # Open + In Progress
        self.assertEqual(summary["operational_rate_percent"], Decimal("50.0"))
        self.assertEqual(summary["total_capacity_mw"], Decimal("35.5"))
        self.assertEqual(summary["total_capacity_dc_mwp"], Decimal("42.6"))
        self.assertEqual(summary["lost_hours"], Decimal("39.5"))
        self.assertEqual(summary["active_blockers_count"], 3)  # Open, In Progress, Pending Verification
        self.assertEqual(summary["total_blockers_count"], 4)

        # Energy: 35.5 * 4.8 = 170.40 MWh
        self.assertEqual(summary["energy_today_mwh"], Decimal("170.40"))
        # CO2: 170.40 * 0.7 = 119.28 t
        self.assertEqual(summary["co2_avoided_t"], Decimal("119.28"))

    def test_invalid_capacity_rejects_negative_or_bad_values(self):
        projects = [{"name": "PV-01", "status": "Open"}]
        profiles = [{"project": "PV-01", "capacity_ac_mw": "-5.0"}]
        with self.assertRaises(RuleViolation):
            portfolio_kpi_summary(projects, profiles, [])
