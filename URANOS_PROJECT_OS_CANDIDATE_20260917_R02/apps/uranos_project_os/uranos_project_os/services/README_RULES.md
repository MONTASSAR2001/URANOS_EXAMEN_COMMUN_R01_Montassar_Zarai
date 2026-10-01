# Services Layer Rules (`services/README_RULES.md`)

## 1. Role & Purpose of the Services Layer
The `services/` directory contains Frappe adapters. Its sole responsibility is to mediate between the Frappe database / HTTP request layer and the pure domain logic. It owns:
- HTTP method enforcement (`POST` for mutations).
- Security, role checks, and project isolation.
- Concurrency control via pessimistic database locking.
- Persistence execution inside the `authorized_transition()` context.

---

## 2. Standard 5-Step Adapter Execution Flow

Every mutation function in this layer MUST follow this exact 5-step sequence:

```
[Incoming Request]
       |
       v
+-------------------------------------------------------------+
| Step 1: Verify Role Permissions & Authentication            |
| - Check HTTP method: require_post()                         |
| - Verify session user: actor()                              |
| - Check business role: security.require_roles(...)          |
+-------------------------------------------------------------+
       |
       v
+-------------------------------------------------------------+
| Step 2: Enforce Pessimistic Database Locking                |
| - Lock parent Project first: scoped_doc("Project", ..., lock=True)|
| - Lock target DocType: scoped_doc(doctype, name, lock=True) |
| - SQL query uses FOR UPDATE to prevent race conditions       |
+-------------------------------------------------------------+
       |
       v
+-------------------------------------------------------------+
| Step 3: Enforce Project Isolation & Evidence Validation     |
| - Confirm target belongs to user's allowed projects         |
| - security.require_project(doc.project)                     |
| - Validate private attachments: security.validate_evidence(doc)|
+-------------------------------------------------------------+
       |
       v
+-------------------------------------------------------------+
| Step 4: Execute Pure Domain Logic                           |
| - Call corresponding domain validator in domain/            |
| - Pass pure Python dicts / dataclasses / Decimal values     |
| - Catch RuleViolation and translate to frappe.throw         |
+-------------------------------------------------------------+
       |
       v
+-------------------------------------------------------------+
| Step 5: Save Inside Authorized Transition Context           |
| - with authorized_transition(): doc.save()                  |
| - Return narrow, non-financial serializable response        |
+-------------------------------------------------------------+
```

---

## 3. Critical Implementation Checklist for Services

1. **Pessimistic Lock Ordering (`Project` First)**:
   ```python
   def _locked(doctype, name):
       initial = scoped_doc(doctype, name, permission="write")
       scoped_doc("Project", initial.project, lock=True)
       return scoped_doc(doctype, name, permission="write", lock=True)
   ```
   *Rationale*: Locking `Project` first guarantees consistent global lock acquisition order, eliminating deadlocks across concurrent requests.

2. **Authorized Transition Wrapper**:
   Direct `.save()` without `with authorized_transition():` will be blocked by `UranosDocument.validate()` in `controllers.py`. Never expose a whitelisted method that enables `authorized_transition` arbitrarily.

3. **No Financial Leaks**:
   Field APIs and responses must use explicit field allowlists. ERP cost, rate, and valuation fields must never be exposed to users lacking `URANOS Executive` or `URANOS Finance Controller` roles.

4. **Audit Trail**:
   Always record timestamps using `frappe.utils.now()` and actor identities using `frappe.session.user`. Do not trust actor parameters passed from client requests.
