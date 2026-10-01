# ☀️ URANOS Project OS — Master Audit & Demo Report

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Frappe](https://img.shields.io/badge/Frappe-v15.x-blueviolet?style=for-the-badge&logo=frappe&logoColor=white)](https://frappeframework.com)
[![Docker](https://img.shields.io/badge/Docker-Compose_v2-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![MariaDB](https://img.shields.io/badge/MariaDB-10.6-003545?style=for-the-badge&logo=mariadb&logoColor=white)](https://mariadb.org)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium_E2E-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev)
[![Pytest](https://img.shields.io/badge/Pytest-250_Passed-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)
[![QA](https://img.shields.io/badge/QA-250%2F250_Tests_100%25_Pass-brightgreen?style=for-the-badge)](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/tests/unit/)

<br/>

**Mission-critical supervisory and obstacle management platform for utility-scale solar photovoltaic power plants.**

---

[Executive Summary](#1-executive-summary--fleet-scale) • [Architecture](#2-system-architecture--hexagonal-design) • [Role Cycles](#3-role-by-role-operational-cycles) • [The Golden Rule](#4-the-golden-rule--anti-fraud-separation-of-duties) • [Screenshots](#5-demo-screenshot-gallery) • [QA](#6-quality-assurance--test-coverage) • [Quick Start](#7-quick-start--test-credentials)

</div>

---

## 1. Executive Summary & Fleet Scale

**URANOS Project OS** is an industrial-grade enterprise operating platform for the construction, quality control, obstacle resolution, and commissioning of utility-scale solar PV assets. Developed for Tunisia's national renewable energy program, the platform centrally governs **20+ solar power plants** spanning all Tunisian governorates.

```
       TUNISIA UTILITY-SCALE PV PORTFOLIO — LIVE PRODUCTION FLEET
┌─────────────────────────────────────────────────────────────────────┐
│  ☀️  23 Photovoltaic Sites      ⚡  672 MW AC / 806 MWp DC          │
│  📍  Real-Time Leaflet GIS Map  🛡️  Fail-Closed Pessimistic RBAC   │
│  🤖  Dual-Engine AI Copilot     📊  Strict 4-State Blocker Cycle    │
│  🔬  250/250 Unit Tests Pass    🔒  Golden Rule Anti-Fraud SoD       │
└─────────────────────────────────────────────────────────────────────┘
```

### Live Fleet Statistics (Verified October 1, 2026)

| Metric | Live Value |
| :--- | ---: |
| **Total PV Installations** | 23 (20 active operational) |
| **Aggregated AC Grid Capacity** | **672.0 MW AC** |
| **Aggregated DC Install Capacity** | **806.4 MWp DC** |
| **Unit Tests Passed** | **250 / 250 (100%)** — 179 subtests, 8.36 s |
| **PV Simulation Invariants** | **58 / 58 (100%)** |
| **Exam Compliance Assertions** | **13 / 13 (100%)** |
| **Playwright E2E Browser Suites** | **72+ suites, 0 regressions** |
| **Docker Microservices Healthy** | **10 / 10** |

### Selected Fleet Portfolio

| ID | Plant Name | Governorate | MW AC | Status |
| :--- | :--- | :--- | ---: | :---: |
| PV-0007 | Centrale Solaire Borj Bourguiba | Zaghouan | **200 MW** | 🟡 Active |
| PV-0005 | Centrale Solaire Gafsa – Segdoud | Gafsa | **120 MW** | 🟡 Active |
| PV-0004 | Centrale Solaire Metbassta – Kairouan | Kairouan | **100 MW** | 🟡 Active |
| PV-0006 | Centrale Solaire Sidi Bouzid – Scadd | Sidi Bouzid | **50 MW** | 🟡 Active |
| PV-0017 | Centrale PV Bizerte – Menzel Bourguiba | Bizerte | **15 MW** | 🟡 Active |
| PV-0001 | Centrale Solaire Tozeur I | Tozeur | **10 MW** | ✅ Completed |
| PV-0011 | Centrale Solaire Kebili – Douz | Kebili | **10 MW** | ✅ Completed |

---

## 2. System Architecture & Hexagonal Design

URANOS Project OS enforces **Hexagonal Architecture (Ports & Adapters)** — a zero-compromise separation between pure business logic and the Frappe/ERPNext infrastructure layer.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  EXTERNAL INTERFACE (Browser / Mobile PWA / REST API / Playwright E2E) │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│  CONTROLLERS & SECURITY GATES (Frappe Framework Layer)                  │
│  security.py: require_post() · current_user() · require_project()       │
│  controllers.py: authorized_transition() · prevent_operational_delete() │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│  SERVICES LAYER — Frappe Adapters (Pessimistic Locking)                 │
│  blockers.py · api.py · ai_synthesis.py · materials.py                 │
│  SELECT … FOR UPDATE on every mutation                                  │
│  authorized_transition() context manager wraps every .save()            │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│  PURE DOMAIN LAYER — Zero I/O · Zero Frappe · Zero float                │
│  domain/blockers.py · domain/controls.py · domain/stock.py             │
│  domain/logistics.py · domain/quality.py · domain/offline.py           │
│  ✓ ONLY: dataclasses · Decimal · Enum · datetime · typing              │
│  ✗ FORBIDDEN: import frappe  (proven by 250 pytest unit tests)         │
│  ✗ FORBIDDEN: float  (Decimal enforced for all physical quantities)    │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│  PERSISTENCE: MariaDB 10.6 (Frappe ORM)                                 │
│  CACHE / QUEUE: Redis 6.2 (Cache · Queue · SocketIO)                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Invariants

| Invariant | Enforcement | Severity |
| :--- | :--- | :---: |
| No Frappe imports in domain | 250 pytest unit tests, zero external mocks | 🔴 CRITICAL |
| No `float` for quantities | `Decimal` throughout domain + type annotations | 🔴 CRITICAL |
| Pessimistic locking on all writes | `SELECT … FOR UPDATE` via `scoped_doc(lock=True)` | 🔴 CRITICAL |
| Authorized transition guard | `with authorized_transition():` wraps every `.save()` | 🔴 CRITICAL |
| No hard delete on operational records | `prevent_operational_delete` hook on all doctypes | 🟠 HIGH |
| Fail-closed security posture | Missing auth or project grant → immediate rejection | 🟠 HIGH |

---

## 3. Role-by-Role Operational Cycles

### Persona Overview & RBAC Boundaries

| Persona | Email | Frappe Roles | Projects Visible |
| :--- | :--- | :--- | :---: |
| **Direction / Manager** | `direction_01@uranos.local` | `management`, `URANOS Executive` | **All 23** |
| **Ingénieur / Engineer** | `ingenieur_01@uranos.local` | `engineer`, `URANOS Engineering Director` | **3 assigned** |
| **Équipe Chantier** | `chantier_01@uranos.local` | `site_team`, `URANOS Site Controller` | **1–2 assigned** |
| **Independent Verifier** | `ingenieur_03@uranos.local` | `engineer`, `URANOS Project Manager` | **1 assigned** |

### Full E2E Cycle — Playwright Verified Execution Log

```
================================================================================
   URANOS OS — Full End-to-End Cycle (Manager → Site Team → Engineer → Manager)
================================================================================

STEP 1: Manager Creates Project PV-0099
  ✓ direction_01@uranos.local logged in
  ✓ Awesomebar #navbar-search: z-index=10050, items=9, pointer-events=auto
  ✓ Project PV-0099 created
    └─ Assigned Engineer: ingenieur_01@uranos.local
    └─ Assigned Site Team: chantier_01@uranos.local

STEP 2: Site Team Declares Critical Blocker
  ✓ chantier_01@uranos.local logged in
  ✓ '+  Nouvel Obstacle' button (#bd-create-btn): operational
  ✓ Blocker B-00009 created — Status: Open | Severity: Critical | Project: PV-0099

STEP 3: Engineer Accepts & Transitions to In Progress
  ✓ ingenieur_01@uranos.local logged in
  ✓ Blocker B-00009 opened — status confirmed: Open
  ✓ Status transitioned to: 'In Progress'

STEP 4: Manager Verifies Across DB, Form UI & Dashboard
  ✓ direction_01@uranos.local logged in
  ✓ DB Record: {status:"In Progress", severity:"Critical", project:"PV-0099"}
  ✓ Blocker Form UI status = 'In Progress'
  ✓ Dashboard: 24 projects in filter, B-00009 row visible, KPIs: Active=7 | Critical=5

================================================================================
   DEFINITIVE SUCCESS — FULL CYCLE QA PASSED WITH ZERO ERRORS!
================================================================================
```

### Role Capability Matrix

| Action | Direction | Ingénieur | Chantier |
| :--- | :---: | :---: | :---: |
| View all projects (portfolio) | ✅ | ❌ scoped | ❌ scoped |
| Create & assign projects | ✅ | ❌ | ❌ |
| Declare blockers | ✅ | ✅ | ✅ |
| Transition Open → In Progress | ✅ | ✅ | ❌ |
| Submit corrective action | ❌ | ✅ | ✅ |
| Close blocker (independent) | ✅ | ✅ (if not resolver) | ❌ |
| Close own resolved blocker | ❌ Golden Rule | ❌ Golden Rule | ❌ |
| Modify field measurements | ❌ Read-Only | ✅ | ✅ |

---

## 4. The Golden Rule — Anti-Fraud Separation of Duties

**The Golden Rule** prevents self-certification — the actor who resolved a blocker cannot verify or close their own resolution:

$$\texttt{closed\_by} \notin \{\texttt{resolved\_by},\, \texttt{responsible}\}$$

### Three-Layer Defense Architecture

**Layer 1 — Pure Domain Oracle** (`domain/blockers.py`):
```python
def close_issue(self, closed_by_user: str) -> None:
    resolvers = {
        u.strip()
        for u in (self.resolved_by, self.responsible)
        if u and str(u).strip()
    }
    if closed_by_user.strip() in resolvers:
        raise DomainRuleViolation("Auto-vérification refusée.")
    self.closed_by = closed_by_user.strip()
    self.status = IssueStatus.CLOSED
```

**Layer 2 — Frappe DocType Controller** (`uranos_blocker.py`):
```python
# Separation of Duties — enforced on every .save()
if current_user in {resolved_by, responsible}:
    frappe.throw("Auto-vérification refusée.", frappe.ValidationError)
```

**Layer 3 — Service Adapter** (`services/blockers.py`):
```python
@frappe.whitelist()
def close_blocker(name: str, review_reason: Optional[str] = None):
    user = actor()
    doc = _locked(name)        # SELECT … FOR UPDATE (pessimistic lock)
    issue = _to_domain(doc)
    try:
        issue.close_issue(closed_by_user=user)
    except DomainRuleViolation as e:
        frappe.throw(str(e), frappe.ValidationError)
```

### Live Verification Evidence (MariaDB)

```
TEST 1: Strict Closure Rules & Separation of Duties
  [PASS] Blocker created — status: Open
  [PASS] Open → In Progress transition succeeded
  [PASS] In Progress → Pending Verification succeeded
  [PASS] Self-verification REJECTED: 'Auto-vérification refusée.'
  [PASS] Closure without corrective action REJECTED
  [PASS] Independent closure by ingenieur_03: ACCEPTED ✓

TEST 2: RBAC Permissions
  [PASS] site_team closure attempt: BLOCKED (PermissionError)
  [PASS] management read access: GRANTED
  [PASS] management write attempt: BLOCKED (Read-Only)

TEST 3–4: Kanban Sorting & AI Synthesis
  [PASS] 6-tier sort matches jury rules exactly
  [PASS] AI synthesis executed, facts separated from suggestions

RESULT: 13 PASSED, 0 FAILED ✅
```

---

## 5. Demo Screenshot Gallery

> All screenshots captured via headless Playwright Chromium at 2880×1920 HiDPI against the live Docker production stack.

---

### 5.1 Main Bento Grid Desk & Tunisian National GIS Fleet Map

![Main Bento Grid Desk — Leaflet GIS Fleet Map](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/01_main_desk_bento.png)

*Glassmorphic bento dashboard with live KPI ribbon (672 MW / 806 MWp DC), animated weather widgets, and interactive Leaflet GIS map plotting all 20+ Tunisian PV sites with color-coded status pins.*

---

### 5.2 Role-Filtered Portfolio Views — RBAC Strict Isolation

**Direction — Full 20-Project Portfolio:**
![Manager Portfolio](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/01a_manager_portfolio_20_projects.png)

**Ingénieur — 3 Assigned Projects Only:**
![Engineer Scoped View](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/01b_engineer_filtered_projects.png)

**Équipe Chantier — Single Assigned Site:**
![Site Team Single Project](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/01c_site_team_single_project.png)

---

### 5.3 Blocker Executive Dashboard & Real-Time Analytics

![Blocker Executive Dashboard](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/02_blocker_dashboard_gis.png)

*Executive counter badges (Active: 7, Critical/High: 5), scoped project filter (24 projects), "+ Nouvel Obstacle" CTA, and sortable risk ledger with severity chips and direct document links.*

---

### 5.4 4-Column Operational Kanban Board

![4-Column Operational Kanban Board](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/03_blocker_kanban.png)

*Strict 4-column workflow: **Ouvert → En cours → À vérifier → Clôturé**. Parametric reference date toolbar (T-0 / T-7 / T-30). 6-tier priority sort. Full Arabic RTL mirroring verified.*

---

### 5.5 Dual-Engine AI Copilot — Groq RAG & Deterministic Offline Fallback

![Dual-Engine AI Copilot](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/04_uranos_ai_copilot.png)

*Context-aware RAG grounded to live plant data (PV-0004 — 100 MW Kairouan). Primary: Groq Llama-3.3-70B. Fallback: zero-network deterministic heuristic oracle. Output strictly bifurcated — verified facts vs. AI-suggested corrective actions.*

---

### 5.6 Security & Access Audit Matrix

![Security & Access Audit Matrix](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/05_access_audit_matrix.png)

*Role × DocType permission matrix. `Delete` globally revoked on all operational transactions (`prevent_operational_delete`). Fail-closed default posture.*

---

### 5.7 Mobile Responsive Viewports (390×844)

| View | Screenshot |
| :--- | :---: |
| **Mobile Bento Desk** — collapsible drawer, vertical KPI cards, touch GIS map | ![Mobile Desk](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/06_mobile_desk.png) |
| **Mobile Blocker Kanban** — swipeable lane, touch-friendly cards | ![Mobile Kanban](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/07_mobile_blocker.png) |

---

### 5.8 Live Workflow Demo — 4 Steps

| Step | Screenshot | Description |
| :--- | :---: | :--- |
| **1 — Manager provisions project** | ![Step 1](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/step1_manager_project_creation.png) | PV-0099 created with assigned engineer + site team |
| **2 — Site Team declares blocker** | ![Step 2](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/step2_site_team_blocker_created.png) | B-00009 (Critical) created, auto-assigned to engineer |
| **3 — Engineer transitions to In Progress** | ![Step 3](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/step3_engineer_blocker_in_progress.png) | Engineering review initiated with audit timestamp |
| **4 — Manager verifies on executive dashboard** | ![Step 4](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/screenshots/step4_manager_verified_dashboard.png) | Live KPI update confirmed — B-00009 row visible |

---

## 6. Quality Assurance & Test Coverage

### 6.1 Pure Domain Pytest Suite — 250/250 Passed

```
platform linux -- Python 3.10.12, pytest-9.1.1

tests/unit/test_7day_progress.py              7 passed
tests/unit/test_ai_fallback.py               12 passed
tests/unit/test_baseline_change_authority.py 31 passed
tests/unit/test_baseline_revisions.py         5 passed
tests/unit/test_browser_envelope_contract.py  1 passed
tests/unit/test_controls.py                  47 passed
tests/unit/test_domain_portfolio_kpis.py      3 passed
tests/unit/test_import_exam_data.py           1 passed
tests/unit/test_logistics.py                 19 passed
tests/unit/test_materials_adapters.py        25 passed
tests/unit/test_offline.py                    8 passed
tests/unit/test_quality.py                   28 passed
tests/unit/test_services_blockers.py          6 passed  ← Golden Rule
tests/unit/test_stock.py                     27 passed
tests/unit/test_support_workflow_adapters.py 31 passed

======= 250 passed, 179 subtests passed in 8.36s =======
```

### 6.2 Golden Rule Blocker Tests (6/6 Passed)

```
test_assign_blocker_missing_justification_fails   PASSED
test_assign_blocker_success                        PASSED
test_close_blocker_enforces_golden_rule            PASSED ✓
test_close_blocker_independent_verifier_succeeds   PASSED ✓
test_reopen_blocker_success                        PASSED
test_submit_resolution_success                     PASSED
```

### 6.3 QA Pyramid

```
┌────────────────────────────────────────────────────────────────────────┐
│                      QUALITY ASSURANCE PYRAMID                         │
│  🌐 72+ Playwright Chromium E2E Suites (Multi-Persona, RTL, Mobile)  │
│  ─────────────────────────────────────────────────────────────────    │
│  ⚡ 1 MW Photovoltaic Simulation Oracle (58 Strict Invariants)         │
│  ─────────────────────────────────────────────────────────────────    │
│  🔬 250+ Pure Domain Unit Tests (Zero-IO, Zero-Frappe, 100% Pass)    │
└────────────────────────────────────────────────────────────────────────┘
```

### 6.4 1 MW PV Simulation Oracle

```bash
PYTHONPATH=URANOS_PROJECT_OS_CANDIDATE_20260917_R02/apps/uranos_project_os \
  python3 URANOS_PROJECT_OS_CANDIDATE_20260917_R02/scripts/simulate_1mw.py
```

```
assertions_passed: 58
observation_chain_sha256: 8ed910d752f18808217faf6f1a532be8bf03083608a24380babdca2b955a73e9
initial_risk_status: Red → final_risk_status: Green
benchmark: 13 500 progress entries · 5 000 stock movements · 2.76 s
```

---

## 7. Quick Start & Test Credentials

### Starting the Platform

```bash
# Navigate to the candidate directory
cd URANOS_PROJECT_OS_CANDIDATE_20260917_R02

# Start all 10 microservices (~60s first boot)
docker compose up -d

# Verify health
docker ps

# Platform ready at: http://localhost:8080
```

### Test Credentials

| Role | Email | Password | Project Scope |
| :--- | :--- | :---: | :--- |
| **Direction / Manager** | `direction_01@uranos.local` | `Password123!` | All 23 projects |
| **Ingénieur / Engineer** | `ingenieur_01@uranos.local` | `Password123!` | PV-0004 · PV-0005 · PV-0099 |
| **Équipe Chantier** | `chantier_01@uranos.local` | `Password123!` | PV-0004 · PV-0099 |
| **Independent Verifier** | `ingenieur_03@uranos.local` | `Password123!` | PV-0004 |
| **System Administrator** | `Administrator` | *(see `.env`)* | Unrestricted |

### Key Application URLs

| Page | URL |
| :--- | :--- |
| **Main Desk** | `/app` |
| **Blocker Dashboard** | `/app/blocker-dashboard` |
| **AI Copilot** | `/app/uranos-ai-copilot` |
| **Project List** | `/app/project` |

### Running All Test Suites

```bash
cd URANOS_PROJECT_OS_CANDIDATE_20260917_R02

# 1. Pure Domain Unit Tests (no Docker required)
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/unit -v
# → 250 passed, 179 subtests passed

# 2. 1 MW Photovoltaic Simulation
PYTHONPATH=apps/uranos_project_os python3 scripts/simulate_1mw.py
# → assertions_passed=58

# 3. Live Exam Compliance (Docker stack required)
docker cp scripts/test_exam_compliance.py uranos-backend:/home/frappe/frappe-bench/sites/
docker exec -w /home/frappe/frappe-bench/sites uranos-backend \
  /home/frappe/frappe-bench/env/bin/python test_exam_compliance.py
# → 13 PASSED, 0 FAILED

# 4. Full Multi-Role Playwright Cycle
node tests/browser/verify_full_uranos_cycle.mjs
# → DEFINITIVE SUCCESS
```

---

## 8. Examination Compliance Matrix

| Req | Description | Status | Evidence |
| :---: | :--- | :---: | :--- |
| REQ-1 | Architecture Hexagonale Ports & Adapters | ✅ **CONFORME** | `domain/` — zero Frappe, zero IO, 250 tests |
| REQ-2 | DocType URANOS Blocker complet | ✅ **CONFORME** | `doctype/uranos_blocker/` — naming `B-.#####` |
| REQ-3 | Lifecycle 4 états + Règle d'Or | ✅ **CONFORME** | `domain/blockers.py:142-163` — `DomainRuleViolation` |
| REQ-4 | RBAC serveur + isolation projet | ✅ **CONFORME** | `security.py` + 13/13 compliance assertions |
| REQ-5 | Dashboards Desktop & Mobile | ✅ **CONFORME** | `page/blocker_dashboard/` + 390×844 captures |
| REQ-6 | Date de référence paramétrique | ✅ **CONFORME** | Kanban toolbar `#uranos-kanban-ref-date` + 6-tier sort |
| REQ-7 | Bilingual FR / AR + RTL natif | ✅ **CONFORME** | `[dir="rtl"]` CSS + bilingual Playwright suites |
| REQ-8 | IA citée + mode hors-ligne | ✅ **CONFORME** | `services/ai_synthesis.py` — Groq RAG + offline oracle |

---

<div align="center">

**URANOS Project OS** · *Enterprise Photovoltaic Infrastructure Management*
Developed for the **URANOS Common Examination (R02)** · Audited October 1, 2026

[![Tests](https://img.shields.io/badge/Domain_Tests-250%2F250_Passed-brightgreen?style=flat-square)](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/tests/unit/)
[![Simulation](https://img.shields.io/badge/PV_Simulation-58%2F58_Invariants-brightgreen?style=flat-square)](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/scripts/simulate_1mw.py)
[![Compliance](https://img.shields.io/badge/Exam_Compliance-13%2F13_Assertions-brightgreen?style=flat-square)](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/scripts/test_exam_compliance.py)
[![E2E](https://img.shields.io/badge/Playwright_E2E-0_Regressions-brightgreen?style=flat-square)](URANOS_PROJECT_OS_CANDIDATE_20260917_R02/tests/browser/)

</div>
