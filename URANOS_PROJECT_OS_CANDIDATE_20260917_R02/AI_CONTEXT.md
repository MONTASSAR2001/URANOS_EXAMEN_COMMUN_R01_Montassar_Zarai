# URANOS Project OS — AI Engineering Context

## Overview
This document sets the engineering boundaries and operational expectations for developing features within **URANOS Project OS**, specifically for the **Blocages (Issues)** module and project control services.

---

## 1. Directory Structure & Architectural Separation

```
apps/uranos_project_os/uranos_project_os/
├── domain/            <-- PURE PYTHON CORE. Zero Frappe imports. Zero I/O.
│   ├── controls.py
│   ├── logistics.py
│   ├── quality.py
│   ├── stock.py
│   ├── offline.py
│   └── README_RULES.md
│
├── services/          <-- FRAPPE ADAPTERS. Locking, Permissions, DB I/O.
│   ├── common.py      (scoped_doc, pessimistic locking, actor resolution)
│   ├── operations.py
│   ├── reports.py     (Blockers & RFI adapters)
│   ├── materials.py
│   ├── quality.py
│   ├── api.py
│   └── README_RULES.md
│
├── controllers.py     <-- BASE DOCUMENT & TRANSITION GUARDS (UranosDocument)
├── security.py        <-- FAIL-CLOSED PROJECT ISOLATION & SCOPED QUERIES
├── file_security.py   <-- IMMUTABLE EVIDENCE FILES & PERMISSIONS
└── hooks.py           <-- FRAPPE EXTENSION POINTS (Zero core patches)
```

---

## 2. Invariants Checklist for Code Generation

| Invariant | Implementation Requirement |
| :--- | :--- |
| **No Framework Leaks** | `import frappe` is prohibited in `domain/`. Any test asserting domain rules must pass without Frappe installed. |
| **Pessimistic Locking** | Always call `scoped_doc("Project", doc.project, lock=True)` then `scoped_doc(doctype, name, lock=True)`. |
| **Authorized Transitions** | All state changes and protected field updates must occur inside `with authorized_transition():`. |
| **No Self-Verification** | Any verifier or closer must be explicitly checked against `frappe.session.user` and the reporter/resolver. |
| **Evidence Immutability** | Evidence must be verified using `security.validate_evidence(doc)`. Files must be private and local. |
| **Finite Quantities** | Every number must be checked for finite Decimal representation, rejecting `float`, `NaN`, `Inf`. |
| **No Operational Delete** | `on_trash` hooks must call `security.prevent_operational_delete(self)`. |

---

## 3. "Blocages" (Issues) Target Architecture

### Domain Layer (`domain/blockers.py`)
- Defines pure dataclasses: `Blocker`, `BlockerResolution`, `BlockerClosure`.
- State transitions: `Open -> In Progress -> Pending Verification -> Closed`.
- Invariant validations:
  - Transition legality.
  - Project scope consistency.
  - Separation of duties (`resolved_by != closed_by`).
  - Lost hours validation (`Decimal >= 0`).
  - Evidence attachment presence.

### Service Layer (`services/blockers.py` or `services/reports.py`)
- API endpoints:
  - `@frappe.whitelist(methods=["POST"]) def assign_blocker(...)`
  - `@frappe.whitelist(methods=["POST"]) def start_blocker(...)`
  - `@frappe.whitelist(methods=["POST"]) def resolve_blocker(...)`
  - `@frappe.whitelist(methods=["POST"]) def close_blocker(...)`
  - `@frappe.whitelist(methods=["POST"]) def review_blocker_severity(...)`
- Locks: Project-first ordering.
- Execution: `with authorized_transition(): doc.save()`.

### Testing Contract
- Pure unit tests in `tests/unit/test_blockers.py` (No database, no mocks).
- Adapter tests in `tests/qa/test_blocker_adapters.py` (Using `adapter` fixture with synthetic Frappe stubs).
