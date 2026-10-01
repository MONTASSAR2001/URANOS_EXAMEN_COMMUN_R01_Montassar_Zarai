"""Reuse the explicit dependency fake; this is not a real Frappe test site."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / "qa" / "conftest.py"
_spec = importlib.util.spec_from_file_location("uranos_independent_qa_harness", _path)
_harness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_harness)
adapter = _harness.adapter
FakeDocument = _harness.FakeDocument
Row = _harness.Row
