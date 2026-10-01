"""Unit tests for URANOS Blocker service adapter (services/blockers.py).

Tests pure domain integration, 5-step lifecycle transitions, locking, and the Golden Rule (no self-verification).
"""
import importlib.util
from contextlib import nullcontext
from copy import deepcopy
from datetime import date
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch
import unittest

import pytest
import uranos_project_os

SERVICES = Path(__file__).resolve().parents[2] / "apps/uranos_project_os/uranos_project_os/services"


class Row(dict):
    def __getattr__(self, key):
        if key.startswith("__"):
            raise AttributeError(key)
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value

    def set(self, key, value):
        self[key] = value

    def append(self, key, value):
        self.setdefault(key, []).append(Row(value))

    def as_dict(self):
        return deepcopy(dict(self))

    def save(self, **kwargs):
        self["saved"] = True
        return self


def load_blockers_service():
    fake = ModuleType("frappe")
    fake.whitelist = lambda *args, **kwargs: lambda fn: fn
    fake.PermissionError = PermissionError
    fake.ValidationError = ValueError

    def _throw(message, exc=None):
        raise (exc or ValueError)(message)

    fake.throw = _throw
    fake.session = SimpleNamespace(user="coordinator")
    fake.utils = SimpleNamespace(
        now=lambda: "2026-09-27 12:00:00",
        getdate=lambda value=None: date.fromisoformat(str(value)) if value else date(2026, 9, 27),
    )

    security = ModuleType("uranos_project_os.security")
    security.require_roles = Mock(return_value="coordinator")
    security.require_project = Mock(return_value="PRJ-001")
    security.current_user = Mock(return_value="coordinator")
    security.SCOPED_FIELDS = {"URANOS Blocker": "project", "Project": "name"}
    security.project_for = Mock(return_value="PRJ-001")

    controller = ModuleType("uranos_project_os.controllers")
    controller.authorized_transition = nullcontext

    common = ModuleType("uranos_project_os.services.common")
    common.require_post = Mock()
    common.actor = Mock(return_value="coordinator")
    common.require_project = Mock(return_value="PRJ-001")
    common.scoped_doc = Mock()

    modules = {
        "frappe": fake,
        "uranos_project_os.security": security,
        "uranos_project_os.controllers": controller,
        "uranos_project_os.services.common": common,
    }

    with patch.dict("sys.modules", modules), patch.object(uranos_project_os, "security", security, create=True):
        spec = importlib.util.spec_from_file_location("uranos_project_os.services.blockers", SERVICES / "blockers.py")
        blockers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(blockers)

    return blockers, fake, security, common


class TestBlockersService(unittest.TestCase):
    def setUp(self):
        self.blockers, self.fake, self.security, self.common = load_blockers_service()
        self.doc = Row(
            doctype="URANOS Blocker",
            name="BLK-001",
            project="PRJ-001",
            title="Foundation Crack Detected",
            status="Open",
            severity="High",
            responsible=None,
            evidence=[],
        )
        self.common.scoped_doc.side_effect = lambda dt, name, lock=False: self.doc

    def test_assign_blocker_success(self):
        self.common.actor.return_value = "lead_engineer"
        result = self.blockers.assign_blocker("BLK-001", "site_agent", justification="Assigned to civil team")

        self.assertEqual(result["status"], "In Progress")
        self.assertEqual(result["responsible"], "site_agent")
        self.assertTrue(result.get("saved"))
        self.assertTrue(len(self.doc.get("evidence", [])) > 0)
        self.assertIn("responsible", self.doc.evidence[-1].caption)

    def test_assign_blocker_missing_justification_fails(self):
        self.common.actor.return_value = "lead_engineer"
        with self.assertRaises(ValueError):
            self.blockers.assign_blocker("BLK-001", "site_agent", justification="")

    def test_submit_resolution_success(self):
        self.doc.status = "In Progress"
        self.doc.responsible = "site_agent"
        self.common.actor.return_value = "site_agent"

        result = self.blockers.submit_resolution("BLK-001", corrective_action="Epoxy injection completed")

        self.assertEqual(result["status"], "Pending Verification")
        self.assertEqual(result["resolution"], "Epoxy injection completed")
        self.assertEqual(result["resolved_by"], "site_agent")
        self.assertEqual(result["resolution_submitted_at"], "2026-09-27 12:00:00")
        self.assertTrue(result.get("saved"))

    def test_close_blocker_enforces_golden_rule(self):
        """Resolver CANNOT self-verify and close their own blocker."""
        self.doc.status = "Pending Verification"
        self.doc.responsible = "site_agent"
        self.doc.resolved_by = "site_agent"
        self.doc.resolution = "Epoxy injection completed"

        # Attempt to self-verify as site_agent
        self.common.actor.return_value = "site_agent"
        with self.assertRaises(ValueError) as ctx:
            self.blockers.close_blocker("BLK-001", review_reason="Self-signed closure")

        self.assertTrue(
            "Auto-vérification refusée." in str(ctx.exception)
            or "Golden Rule Violation" in str(ctx.exception)
        )

    def test_close_blocker_independent_verifier_succeeds(self):
        """Independent verifier (different from resolver) successfully closes the blocker."""
        self.doc.status = "Pending Verification"
        self.doc.responsible = "site_agent"
        self.doc.resolved_by = "site_agent"
        self.doc.resolution = "Epoxy injection completed"

        # Independent QA engineer closes it
        self.common.actor.return_value = "qa_inspector"
        result = self.blockers.close_blocker("BLK-001", review_reason="On-site ultrasonic check passed")

        self.assertEqual(result["status"], "Closed")
        self.assertEqual(result["closed_by"], "qa_inspector")
        self.assertEqual(result["review_reason"], "On-site ultrasonic check passed")
        self.assertEqual(result["closed_at"], "2026-09-27 12:00:00")
        self.assertTrue(result.get("saved"))

    def test_reopen_blocker_success(self):
        self.doc.status = "Pending Verification"
        self.doc.responsible = "site_agent"
        self.doc.resolved_by = "site_agent"
        self.doc.resolution = "Epoxy injection completed"
        self.doc.resolution_submitted_at = "2026-09-27 10:00:00"

        self.common.actor.return_value = "qa_inspector"
        result = self.blockers.reopen_blocker("BLK-001", reason="Seepage still observed after test")

        self.assertEqual(result["status"], "In Progress")
        self.assertIsNone(result.get("closed_by"))
        self.assertIsNone(result.get("resolution_submitted_at"))
        self.assertTrue(result.get("saved"))
