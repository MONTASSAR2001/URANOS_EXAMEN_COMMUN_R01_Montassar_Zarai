# Domain Layer Rules (`domain/README_RULES.md`)

## 1. Absolute Architectural Constraints
1. **ZERO Framework Dependencies**:
   - `import frappe` (and any related Frappe/ERPNext submodules) is **STRICTLY FORBIDDEN** in this directory.
   - Any commit or file in `domain/` that imports `frappe` will immediately break the architectural test suite (`tests/test_package_contents.py` and `tests/review/test_independent_boundaries.py`).
2. **Pure Python Only**:
   - Allowed primitives: standard library modules (`dataclasses`, `Decimal`, `enum`, `datetime`, `hashlib`, `typing`, `json`).
   - All numerical quantities, weights, progress percentages, and lost hours MUST use `Decimal` (never `float`).
   - Functions must be pure and deterministic: no I/O, no network, no database calls, no environment reading.
3. **Fail-Fast with Rule Violations**:
   - Raise domain-specific exceptions (e.g. `RuleViolation` from `domain/controls.py`).
   - Never raise Frappe-specific exceptions (`frappe.ValidationError`, `frappe.PermissionError`).

---

## 2. Business Invariants for the "Blocages" (Issues) Module

### A. State Machine & Transitions
The Blocker lifecycle follows a strict four-state workflow:
```
           +-----------------------+
           |         Open          |
           +-----------------------+
                       |
                       v
           +-----------------------+
           |      In Progress      | <-----+ (Reopened on rejection)
           +-----------------------+       |
                       |                   |
                       v                   |
           +-----------------------+       |
           | Pending Verification  | ------+
           +-----------------------+
                       |
                       v
           +-----------------------+
           |        Closed         |
           +-----------------------+
```

1. **`Open`**: Blocker registered with title, description, category, and initial severity.
2. **`In Progress`**: An explicit, enabled, project-scoped user is assigned responsibility.
3. **`Pending Verification`**: The assigned responsible user records the resolution, notes, and lost hours, and attaches evidence. The issue remains an active risk in the system until verified.
4. **`Closed`**: An independent coordinator verifies the resolution and evidence, marking the blocker as closed.

### B. The Golden Rule: "No Self-Verification"
- **`resolved_by != closed_by`**: The actor who submitted the resolution (`resolved_by` or `responsible`) **MUST NOT** be the actor who verifies and closes the blocker (`closed_by`).
- A coordinator who resolves an issue cannot verify their own resolution; another authorized coordinator must verify and close it.

### C. No Hard Deletion
- Operational records represent historical truth. Hard deletion (`DELETE FROM tabURANOS Blocker`) is strictly prohibited.
- Cancelled or invalidated blockers must be transitioned through an auditable cancellation state (`Cancelled`).

### D. Lost Hours & Numeric Rules
- `lost_hours` must be a non-negative, finite `Decimal` (at most 6 decimal places).
- Hours lost cannot be implicitly converted into physical progress or financial costs without an authorized change request or disposition.

### E. Evidence Requirement
- Submitting a resolution requires persisted evidence file references.
- Empty or client-side boolean flags do not constitute evidence.
