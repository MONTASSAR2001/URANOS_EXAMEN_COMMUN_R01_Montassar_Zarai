# URANOS Project OS — Agentic Architecture & Coding Guidelines

## Core Architectural Invariant: Hexagonal Architecture (Ports & Adapters)

This codebase strictly enforces Hexagonal Architecture with an uncompromising boundary between pure business logic and the Frappe/ERPNext framework.

### 1. Pure Domain Layer (`apps/uranos_project_os/uranos_project_os/domain/`)
- **STRICT PROHIBITION**: NEVER import `frappe` or any of its submodules (`frappe.db`, `frappe.model`, etc.) inside `domain/`.
- **Pure Python Only**: Must rely exclusively on standard library primitives: `dataclasses`, `Decimal`, `enum`, `datetime`, `hashlib`, `typing`.
- **Deterministic & Zero-IO**: Domain functions must be deterministic, pure functions with no network, disk, or database access.
- **Precision**: NEVER use `float` for physical progress, stock quantities, or financial amounts. Always use `Decimal`.
- **Fail-Fast Error Handling**: Violations must raise custom standard exceptions (such as `RuleViolation` or `StockRuleError`), never Frappe-specific exceptions.
- **Immutability**: Historical, verified, or approved states are immutable. Revisions and corrections must create new auditable successor entries.

### 2. Services / Adapters Layer (`apps/uranos_project_os/uranos_project_os/services/`)
- **Authority on Transitions**: All database mutations and document state transitions MUST reside in the `services/` directory.
- **Pessimistic Locking**: Every mutation MUST enforce pessimistic locking (`for_update=True` via `scoped_doc(..., lock=True)`). Always lock the parent `Project` first to prevent deadlocks across concurrent requests.
- **Authorized Transitions**: All document `.save()` and state transitions MUST be executed within the `with authorized_transition():` context manager. Direct Desk/REST client modifications outside this context will be rejected by `controllers.py`.
- **Fail-Closed Security**: Every public API or transition function must:
  1. Verify authentication (`security.current_user()`).
  2. Verify explicit project grant (`security.require_project(project)`).
  3. Verify required business roles (`security.require_roles(...)`).
- **Audit & Evidence**: Project evidence files must be private, local uploads (`/private/files/`) and verified via `security.validate_evidence(doc)`.
- **No Operational Delete**: Hard deletion is forbidden on all operational records (`prevent_operational_delete`).

### 3. "Blocages" (Issues / Obstacles) Module Invariants
- **Lifecycle Transitions**: `Open` -> `In Progress` -> `Pending Verification` -> `Closed` (with support for rejection/reopening).
- **Golden Rule (No Self-Verification)**: The resolver (`resolved_by`) MUST NOT be the verifier/closer (`closed_by != resolved_by`).
- **Risk Visibility**: A resolved blocker remains an active operational risk until independent review and closure.
- **Evidence Mandate**: Submitting a resolution and closing a blocker requires verified attached evidence files.
- **Lost Hours Tracking**: `lost_hours` must be a positive finite `Decimal`.
