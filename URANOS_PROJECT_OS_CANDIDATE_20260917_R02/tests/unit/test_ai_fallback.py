"""Unit tests for Phase 4: Cloud AI & RAG Synthesis with Deterministic Fallback.

Verifies:
- Fallback when API key is missing / dummy
- Fallback on network timeout / ConnectionError
- Fallback on Cloud API HTTP 500/503 errors
- Successful AI synthesis when Cloud API responds
- Security boundaries: role enforcement, authentication, and project isolation
- Pure deterministic summary calculations (lost hours, counts, categories)
"""
from decimal import Decimal
import os
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch
import pytest


# Ensure minimal frappe stub exists if frappe is not installed in test runner
def _ensure_frappe_stub():
    if "frappe" in sys.modules and hasattr(sys.modules["frappe"], "whitelist"):
        return sys.modules["frappe"]

    fake_frappe = ModuleType("frappe")
    fake_frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    fake_frappe.PermissionError = type("PermissionError", (Exception,), {})
    fake_frappe.ValidationError = type("ValidationError", (Exception,), {})

    def _throw(msg, exc=None):
        raise (exc or fake_frappe.ValidationError)(msg)

    fake_frappe.throw = _throw
    fake_frappe.session = SimpleNamespace(user="manager@uranos.local")
    fake_frappe.local = SimpleNamespace(response_headers={})
    class ConfDict(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    fake_frappe.conf = ConfDict(groq_api_key=None)
    fake_frappe.get_roles = lambda user: ["URANOS Project Manager"]
    fake_frappe.get_all = lambda *args, **kwargs: []
    fake_frappe.has_permission = lambda *args, **kwargs: True

    sys.modules["frappe"] = fake_frappe
    return fake_frappe


frappe_stub = _ensure_frappe_stub()

from uranos_project_os.services.ai_synthesis import (
    GROQ_COMPLETIONS_URL,
    GROQ_MODEL,
    build_deterministic_blocker_summary,
    call_cloud_llm_synthesis,
    generate_blocker_synthesis,
    chat_with_project_ai,
)
import uranos_project_os.security as security


@pytest.fixture
def mock_blockers():
    open_blockers = [
        {
            "name": "BLK-001",
            "title": "Module delivery delayed by customs",
            "severity": "Critical",
            "category": "Material",
            "status": "Open",
            "description": "Port authority clearance pending",
            "lost_hours": Decimal("24.5"),
            "opened_at": "2026-09-20 08:00:00",
            "work_package": "WP-050",
        },
        {
            "name": "BLK-002",
            "title": "Trenching excavator hydraulic breakdown",
            "severity": "High",
            "category": "Equipment",
            "status": "In Progress",
            "description": "Spare cylinder ordered",
            "lost_hours": Decimal("12.0"),
            "opened_at": "2026-09-22 14:00:00",
            "work_package": "WP-020",
        },
        {
            "name": "BLK-003",
            "title": "Minor dust storm on Zone B",
            "severity": "Low",
            "category": "Weather",
            "status": "Open",
            "description": "Work paused for 2 hours",
            "lost_hours": Decimal("2.0"),
            "opened_at": "2026-09-25 10:00:00",
            "work_package": "WP-030",
        },
    ]

    closed_blockers = [
        {
            "name": "BLK-HIST-01",
            "title": "Customs clearance delay on tracker motors",
            "severity": "Critical",
            "category": "Material",
            "resolution": "Engaged local bonded broker and expedited transit declaration within 18h",
            "closed_at": "2026-08-15 16:00:00",
            "lost_hours": Decimal("18.0"),
        },
        {
            "name": "BLK-HIST-02",
            "title": "Excavator hose failure on Zone A",
            "severity": "High",
            "category": "Equipment",
            "resolution": "Mobilized secondary rental unit from regional depot",
            "closed_at": "2026-08-20 11:00:00",
            "lost_hours": Decimal("8.0"),
        },
    ]

    return open_blockers, closed_blockers


def test_deterministic_summary_calculation(mock_blockers):
    """Test pure rule-based summarization logic without any I/O."""
    open_b, closed_b = mock_blockers
    res = build_deterministic_blocker_summary("PV-01", open_b, closed_b)

    assert res["project"] == "PV-01"
    assert res["is_ai_generated"] is False
    assert res["provider"] == "Deterministic Rule-based Fallback"
    assert res["open_count"] == 3
    assert res["closed_count"] == 2
    assert res["critical_count"] == 2  # Critical + High
    assert res["total_lost_hours"] == 38.5  # 24.5 + 12.0 + 2.0
    assert "Material (1)" in res["summary"]
    assert "Historical Resolution Precedents" in res["summary"]
    assert "Customs clearance delay" in res["summary"]


def test_ai_fallback_when_api_key_missing(monkeypatch, mock_blockers):
    """When Cloud AI API key is missing or dummy, silently fallback to rule-based summary."""
    open_b, closed_b = mock_blockers

    if hasattr(frappe_stub, "conf"):
        if hasattr(frappe_stub.conf, "__setitem__"):
            frappe_stub.conf["groq_api_key"] = None
        else:
            setattr(frappe_stub.conf, "groq_api_key", None)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    frappe_stub.session.user = "manager@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Project Manager"]
    monkeypatch.setattr(security, "allowed_projects", lambda u=None, *args, **kwargs: frozenset({"PV-01"}))

    def _get_all(doctype, filters=None, **kwargs):
        if doctype == "URANOS Blocker":
            if isinstance(filters.get("status"), list):
                return open_b
            return closed_b
        return []

    monkeypatch.setattr(frappe_stub, "get_all", _get_all)

    result = generate_blocker_synthesis("PV-01")

    assert result["is_ai_generated"] is False
    assert result["provider"] == "Deterministic Rule-based Fallback"
    assert result["open_count"] == 3
    assert result["critical_count"] == 2
    assert result["total_lost_hours"] == 38.5
    assert "Executive Blocker Synthesis" in result["summary"]


def test_ai_fallback_on_network_timeout(monkeypatch, mock_blockers):
    """When Groq Cloud AI times out due to remote site connectivity, fallback cleanly."""
    open_b, closed_b = mock_blockers

    if hasattr(frappe_stub, "conf"):
        if hasattr(frappe_stub.conf, "__setitem__"):
            frappe_stub.conf["groq_api_key"] = "gsk_test_mock_key"
        else:
            setattr(frappe_stub.conf, "groq_api_key", "gsk_test_mock_key")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_key")
    frappe_stub.session.user = "manager@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Project Manager"]
    monkeypatch.setattr(security, "allowed_projects", lambda u=None, *args, **kwargs: frozenset({"PV-01"}))

    def _get_all(doctype, filters=None, **kwargs):
        if doctype == "URANOS Blocker":
            if isinstance(filters.get("status"), list):
                return open_b
            return closed_b
        return []

    monkeypatch.setattr(frappe_stub, "get_all", _get_all)

    import requests

    def mock_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("Connection timed out to Groq Cloud AI on site")

    monkeypatch.setattr(requests, "post", mock_timeout)

    result = generate_blocker_synthesis("PV-01")

    assert result["is_ai_generated"] is False
    assert result["provider"] == "Deterministic Rule-based Fallback"
    assert result["open_count"] == 3
    assert "Executive Blocker Synthesis" in result["summary"]


def test_ai_fallback_on_http_error(monkeypatch, mock_blockers):
    """When Groq Cloud AI returns 4xx/5xx errors, fallback gracefully without HTTP 500."""
    open_b, closed_b = mock_blockers

    if hasattr(frappe_stub, "conf"):
        if hasattr(frappe_stub.conf, "__setitem__"):
            frappe_stub.conf["groq_api_key"] = "gsk_test_mock_key"
        else:
            setattr(frappe_stub.conf, "groq_api_key", "gsk_test_mock_key")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_key")
    frappe_stub.session.user = "manager@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Project Manager"]
    monkeypatch.setattr(security, "allowed_projects", lambda u=None, *args, **kwargs: frozenset({"PV-01"}))

    def _get_all(doctype, filters=None, **kwargs):
        if doctype == "URANOS Blocker":
            if isinstance(filters.get("status"), list):
                return open_b
            return closed_b
        return []

    monkeypatch.setattr(frappe_stub, "get_all", _get_all)

    import requests

    mock_resp = Mock()
    mock_resp.status_code = 503
    mock_resp.text = "Service Temporarily Unavailable"
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_resp)

    result = generate_blocker_synthesis("PV-01")

    assert result["is_ai_generated"] is False
    assert result["provider"] == "Deterministic Rule-based Fallback"
    assert result["open_count"] == 3


def test_ai_synthesis_success_when_api_healthy(monkeypatch, mock_blockers):
    """When Groq Llama 3.3 responds 200 OK, deliver the LLM RAG synthesis with is_ai_generated=True."""
    open_b, closed_b = mock_blockers

    if hasattr(frappe_stub, "conf"):
        if hasattr(frappe_stub.conf, "__setitem__"):
            frappe_stub.conf["groq_api_key"] = "gsk_live_test_key"
        else:
            setattr(frappe_stub.conf, "groq_api_key", "gsk_live_test_key")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_live_test_key")
    frappe_stub.session.user = "manager@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Project Manager"]
    monkeypatch.setattr(security, "allowed_projects", lambda u=None, *args, **kwargs: frozenset({"PV-01"}))

    def _get_all(doctype, filters=None, **kwargs):
        if doctype == "URANOS Blocker":
            if isinstance(filters.get("status"), list):
                return open_b
            return closed_b
        return []

    monkeypatch.setattr(frappe_stub, "get_all", _get_all)

    import requests

    called_args = {}

    def mock_post(url, json=None, headers=None, timeout=None):
        called_args["url"] = url
        called_args["json"] = json
        called_args["headers"] = headers
        called_args["timeout"] = timeout
        resp = Mock()
        resp.status_code = 200
        ai_text = (
            "### Strategic AI Blocker Analysis — PV-01\n\n"
            "1. **Customs Delay Mitigation**: Deploy bonded warehouse broker immediately based on past precedent BLK-HIST-01.\n"
            "2. **Excavator Redundancy**: Engage local equipment rental provider to maintain daily trenching pace.\n"
        )
        resp.json = lambda: {
            "choices": [
                {"message": {"content": ai_text}}
            ]
        }
        return resp

    monkeypatch.setattr(requests, "post", mock_post)

    result = generate_blocker_synthesis("PV-01")

    assert result["is_ai_generated"] is True
    assert result["provider"] == "Cloud AI (Groq Llama 3.3)"
    assert "Strategic AI Blocker Analysis" in result["summary"]
    assert result["open_count"] == 3
    assert called_args["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert called_args["json"]["model"] in ("llama-3.3-70b-versatile", "qwen/qwen3.8-27b")
    assert called_args["headers"]["Authorization"] == "Bearer gsk_live_test_key"



def test_ai_synthesis_rejects_unauthenticated_user(monkeypatch):
    """Guest users must be rejected before any synthesis or data retrieval."""
    frappe_stub.session.user = "Guest"
    with pytest.raises(frappe_stub.PermissionError):
        generate_blocker_synthesis("PV-01")


def test_ai_synthesis_rejects_unauthorized_project(monkeypatch):
    """Users cannot synthesize blockers for projects outside their explicit scope."""
    frappe_stub.session.user = "manager@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Project Manager"]
    monkeypatch.setattr(security, "allowed_projects", lambda u=None, *args, **kwargs: frozenset({"PV-01"}))

    with pytest.raises(frappe_stub.PermissionError):
        generate_blocker_synthesis("PV-99-FORBIDDEN")


def test_ai_synthesis_rejects_unauthorized_role(monkeypatch):
    """Users without Manager/Director roles are rejected."""
    frappe_stub.session.user = "auditor@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Read Only Auditor"]
    monkeypatch.setattr(security, "allowed_projects", lambda u: frozenset({"PV-01"}))

    with pytest.raises(frappe_stub.PermissionError):
        generate_blocker_synthesis("PV-01")


def test_ai_synthesis_arabic_localization(monkeypatch, mock_blockers):
    """Fallback synthesis generates Arabic text when language is ar."""
    open_b, closed_b = mock_blockers
    frappe_stub.session.user = "manager@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Project Manager"]
    monkeypatch.setattr(security, "allowed_projects", lambda u=None, *args, **kwargs: frozenset({"PV-01"}))

    def _get_all(doctype, filters=None, **kwargs):
        if doctype == "URANOS Blocker":
            if isinstance(filters.get("status"), list):
                return open_b
            return closed_b
        return []

    monkeypatch.setattr(frappe_stub, "get_all", _get_all)
    monkeypatch.setattr(frappe_stub.local, "lang", "ar", raising=False)

    res = generate_blocker_synthesis("PV-01", force_fallback=True, lang="ar")
    assert res["lang"] == "ar"
    assert "ملخص تنفيذي" in res["summary"]
    assert "المخاطر الرئيسية" in res["summary"]
    assert "الإجراءات الفورية المطلوبة" in res["summary"]


def test_ai_synthesis_french_localization(monkeypatch, mock_blockers):
    """Fallback synthesis generates French text when language is fr."""
    open_b, closed_b = mock_blockers
    frappe_stub.session.user = "manager@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Project Manager"]
    monkeypatch.setattr(security, "allowed_projects", lambda u=None, *args, **kwargs: frozenset({"PV-01"}))

    def _get_all(doctype, filters=None, **kwargs):
        if doctype == "URANOS Blocker":
            if isinstance(filters.get("status"), list):
                return open_b
            return closed_b
        return []

    monkeypatch.setattr(frappe_stub, "get_all", _get_all)
    monkeypatch.setattr(frappe_stub.local, "lang", "fr", raising=False)

    res = generate_blocker_synthesis("PV-01", force_fallback=True, lang="fr")
    assert res["lang"] == "fr"
    assert "Résumé Exécutif" in res["summary"]
    assert "Risques Clés" in res["summary"]
    assert "Actions Immédiates" in res["summary"]


def test_chat_with_project_ai_deterministic_reply(monkeypatch, mock_blockers):
    """Chatbot provides intelligent factual replies offline."""
    open_b, closed_b = mock_blockers
    frappe_stub.session.user = "manager@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Project Manager"]
    monkeypatch.setattr(security, "allowed_projects", lambda u=None, *args, **kwargs: frozenset({"PV-01"}))

    def _get_all(doctype, filters=None, **kwargs):
        if doctype == "URANOS Blocker":
            if isinstance(filters.get("status"), list):
                return open_b
            return closed_b
        return []

    monkeypatch.setattr(frappe_stub, "get_all", _get_all)

    # Question about material
    res_mat = chat_with_project_ai("PV-01", "What is the status of the material blocker?", lang="en")
    assert res_mat["project"] == "PV-01"
    assert "Material" in res_mat["reply"]
    assert "BLK-001" in res_mat["reply"] or "Module delivery" in res_mat["reply"]

    # Question about critical
    res_crit = chat_with_project_ai("PV-01", "Tell me about critical risks", lang="en")
    assert "Critical" in res_crit["reply"]

    # Question in Arabic
    res_ar = chat_with_project_ai("PV-01", "ما هي حالة المواد؟", lang="ar")
    assert res_ar["lang"] == "ar"
    assert "المواد" in res_ar["reply"]


def test_chat_with_project_ai_security_checks(monkeypatch):
    """Chatbot rejects guest, unauthorized project, and empty message."""
    frappe_stub.session.user = "Guest"
    with pytest.raises(frappe_stub.PermissionError):
        chat_with_project_ai("PV-01", "Hello")

    frappe_stub.session.user = "manager@uranos.local"
    frappe_stub.get_roles = lambda u: ["URANOS Project Manager"]
    monkeypatch.setattr(security, "allowed_projects", lambda u=None, *args, **kwargs: frozenset({"PV-01"}))

    with pytest.raises(frappe_stub.PermissionError):
        chat_with_project_ai("PV-FORBIDDEN", "Hello")

    with pytest.raises(Exception):
        chat_with_project_ai("PV-01", "   ")

