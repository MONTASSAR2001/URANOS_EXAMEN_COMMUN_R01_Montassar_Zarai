# URANOS Project OS - Master Development Plan

## Phase 1: Hexagonal Domain & Data Modeling (Days 1-2)
- **DocType Creation:** Create `Site Issue` (Blocage) and `Site Issue History` (Child Table) via Frappe Desk.
- **Pure Domain Logic (`domain/blockers.py`):**
  - Implement state machine: `Open -> In Progress -> Pending Verification -> Closed`.
  - Enforce the Golden Rule: `resolved_by != closed_by` (No Self-Verification).
  - Implement audit trail logic: Any change to `severity`, `responsible`, or `due_date` must append a history record with a mandatory `justification`.
  - **Constraint:** Strictly NO `frappe` imports in the domain layer. Use pure Python (`dataclasses`, `Enum`).

## Phase 2: Services, Security & Offline Sync (Days 3-4)
- **Service Layer (`services/blockers.py`):**
  - Wrap database writes in `with authorized_transition():`.
  - Enforce Pessimistic Locking (`for_update=True`) to prevent race conditions.
  - Apply strict Project Isolation (Row-Level Security via Frappe permissions).
- **Offline Capabilities (PWA):**
  - Utilize Frappe's offline service worker capabilities to allow site engineers to draft and save "Site Issues" in IndexedDB when internet connectivity drops on the chantier, syncing automatically when online.

## Phase 3: "Top Chic" UI/UX (Day 5)
- **Kanban Board:** Enable Frappe's native Kanban view for drag-and-drop issue transitions.
- **Smart Dashboard:** Create a custom Frappe Page with Frappe Charts (Vanilla JS) to visualize critical and overdue issues per project.
- **Interactive Dialogs:** Use `frappe.ui.Dialog` in `workflows.js` to prompt users for justifications and corrective actions via elegant modal popups instead of page reloads.
- **RTL & Localization:** Ensure all strings use `_("Text")` for automatic Arabic/French translation and RTL layout switching.

## Phase 4: Cloud AI & RAG Integration (Day 6)
- **Architecture:** Implement a Retrieval-Augmented Generation (RAG) pipeline using a Cloud LLM API (e.g., Groq or OpenAI API) via LangChain.
- **Flow:** 
  1. Fetch currently open issues.
  2. Retrieve similar historically closed issues from the MariaDB database to serve as context.
  3. Send the context and prompt to the Cloud API to generate a "Smart Synthesis" of recommended corrective actions.
- **Deterministic Fallback (Exam Requirement):** Implement a pure Python rule-based summarization algorithm in a `try/except` block. If the Cloud API fails (e.g., `ConnectionError` due to no internet on site, or API timeout), the system must silently fall back to the deterministic local summary, ensuring strict compliance with the exam's offline/fallback requirements.

## Phase 5: Testing & Deliverables (Day 7)
- Write `pytest` scripts in the `tests/` directory to verify the Hexagonal boundaries and the "No Self-Verification" rule.
- Generate `README.md`, `TEST_RESULTS.md`, and `DECISIONS.md` documenting the AI tools used, the LangChain Cloud API configuration, and future improvements.
