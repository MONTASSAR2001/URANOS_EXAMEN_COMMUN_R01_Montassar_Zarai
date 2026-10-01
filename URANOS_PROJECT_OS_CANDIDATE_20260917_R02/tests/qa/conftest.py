"""Portable adapter harness. This is NOT a Frappe/database/HTTP integration site."""
import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


class Row(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


class FakeDocument(Row):
    def __init__(self, values=None, *, previous=None, fields=None, children=None):
        super().__init__(values or {})
        object.__setattr__(self, "previous", previous)
        object.__setattr__(self, "children", children or [])
        object.__setattr__(self, "meta", SimpleNamespace(
            fields=fields or [], has_field=lambda name: name in self))
        object.__setattr__(self, "flags", Row())
        object.__setattr__(self, "permission_checks", [])

    def get_doc_before_save(self):
        return self.previous

    def get_all_children(self):
        return self.children

    def check_permission(self, permission):
        self.permission_checks.append(permission)

    def as_dict(self):
        return dict(self)

    def set(self, key, value):
        self[key] = value

    def reload(self):
        return self

    def insert(self, **kwargs):
        self.setdefault("name", "SYNTHETIC-NEW")
        self.setdefault("docstatus", 0)
        return self

    def save(self, **kwargs):
        return self


@pytest.fixture
def adapter(monkeypatch):
    """Load actual application adapters against a deliberately small dependency fake.

    No fake implementation of Frappe roles, queries, persistence, SQL locking,
    permissions, rollback or HTTP is claimed. Tests observe which boundary the
    application invokes and run its actual validators.
    """
    names = [name for name in sys.modules if name.startswith((
        "uranos_project_os.services.", "uranos_project_os.controllers", "uranos_project_os.security"))]
    saved = {name: sys.modules.pop(name) for name in names}
    frappe = ModuleType("frappe")
    frappe.PermissionError = type("PermissionError", (Exception,), {})
    frappe.ValidationError = type("ValidationError", (Exception,), {})
    frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
    frappe.DuplicateEntryError = type("DuplicateEntryError", (Exception,), {})
    frappe.UniqueValidationError = type("UniqueValidationError", (Exception,), {})
    frappe.session = SimpleNamespace(user="field@example.invalid")
    frappe.local = SimpleNamespace(request=SimpleNamespace(method="POST"), response_headers={})
    frappe.flags = Row()
    frappe.conf = Row()
    frappe.whitelist = lambda *args, **kwargs: lambda function: function
    frappe.utils = SimpleNamespace(now=lambda: "2026-09-17 12:00:00")
    frappe.get_roles = lambda user: ["URANOS Site Controller"]
    frappe.get_all = lambda *args, **kwargs: []
    frappe.get_list = lambda *args, **kwargs: []
    frappe.get_doc = lambda values: FakeDocument(values)
    frappe.db = SimpleNamespace(exists=lambda *args: False, table_exists=lambda *args: True, get_value=lambda *args, **kwargs: None,
        escape=lambda value: "'" + value.replace("'", "''") + "'", sql=lambda *args, **kwargs: [(1,)])

    def throw(message, exception=None, **kwargs):
        raise (exception or frappe.ValidationError)(message)
    frappe.throw = throw
    model = ModuleType("frappe.model")
    document = ModuleType("frappe.model.document")
    document.Document = FakeDocument
    for name, module in {"frappe": frappe, "frappe.model": model, "frappe.model.document": document}.items():
        monkeypatch.setitem(sys.modules, name, module)
    modules = {name: importlib.import_module("uranos_project_os." + path) for name, path in {
        "security": "security", "controllers": "controllers", "common": "services.common",
        "operations": "services.operations", "quality": "services.quality", "api": "services.api",
    }.items()}
    yield SimpleNamespace(frappe=frappe, **modules)
    for name in list(sys.modules):
        if name.startswith(("uranos_project_os.services.", "uranos_project_os.controllers", "uranos_project_os.security")):
            sys.modules.pop(name, None)
    sys.modules.update(saved)
