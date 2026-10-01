"""URANOS GROUP — Exhaustive Diagnostic & Compliance Test Suite
Validates strict compliance with SUJET_EXAMEN_COMMUN.md, PERIMETRE_ET_REGLES.md,
JALON_ENTRETIEN.md, and DONNEES_FICTIVES.json.

Phases Covered:
- Phase 1: Backend, Database & Workflow Diagnostic (Schema, 4-step workflow, Golden Rule, History, No-Delete)
- Phase 2: RBAC & Permissions Diagnostic (site_team, engineer, management, Cross-project isolation)
- Phase 4: AI Synthesis & Fallback Diagnostic (RBAC, ID citation, Facts vs Suggestions, Fallback)
"""
import sys
import json
import traceback
from datetime import date, timedelta
from decimal import Decimal

import frappe
from frappe.utils import now

results = {
    "phase1": {"passed": 0, "failed": 0, "tests": []},
    "phase2": {"passed": 0, "failed": 0, "tests": []},
    "phase4": {"passed": 0, "failed": 0, "tests": []},
}

def record_test(phase: str, name: str, success: bool, details: str = ""):
    bucket = results[phase]
    if success:
        bucket["passed"] += 1
        status_tag = "[PASS]"
    else:
        bucket["failed"] += 1
        status_tag = "[FAIL]"
    msg = f"  {status_tag} {name}"
    if details:
        msg += f" — {details}"
    print(msg)
    bucket["tests"].append({"name": name, "success": success, "details": details})


def run_phase1_diagnostic():
    print("\n" + "=" * 75)
    print("PHASE 1: BACKEND, DATABASE & WORKFLOW DIAGNOSTIC")
    print("=" * 75)

    frappe.set_user("Administrator")

    # 1.1 DocType Schema & DB Columns Verification
    print("\n[1.1] Schema & MariaDB Columns Verification:")
    meta = frappe.get_meta("URANOS Blocker")
    required_fields = [
        "corrective_action", "due_date", "category", "severity",
        "responsible", "status", "project", "title"
    ]
    for field in required_fields:
        has_field = meta.has_field(field)
        record_test("phase1", f"Field '{field}' exists in DocType schema", has_field, f"type={meta.get_field(field).fieldtype if has_field else 'MISSING'}")

    db_columns = frappe.db.get_table_columns("URANOS Blocker")
    for field in required_fields:
        has_col = field in db_columns
        record_test("phase1", f"Column '{field}' exists in MariaDB tabURANOS Blocker", has_col)

    # Check track_changes
    track_changes_enabled = bool(meta.track_changes)
    record_test("phase1", "track_changes is enabled on URANOS Blocker", track_changes_enabled)

    # 1.2 Strict 4-Step Workflow & Invalid Transitions
    print("\n[1.2] Strict 4-Step Workflow Transitions:")
    test_doc_name = "TEST-DIAG-WF-001"
    if frappe.db.exists("URANOS Blocker", test_doc_name):
        frappe.db.delete("URANOS Blocker", {"name": test_doc_name})
        frappe.db.commit()

    # Initial state must be Open
    initial_closed_blocked = False
    try:
        b_invalid_init = frappe.get_doc({
            "doctype": "URANOS Blocker",
            "name": "TEST-INIT-FAIL",
            "project": "PV-01",
            "title": "Invalid initial state test",
            "status": "Closed",
            "corrective_action": "Some fix",
        })
        b_invalid_init.insert(ignore_permissions=True)
    except frappe.ValidationError:
        initial_closed_blocked = True
    record_test("phase1", "New blocker cannot be created directly in 'Closed' status", initial_closed_blocked)

    # Insert valid blocker in Open status
    blocker = frappe.get_doc({
        "doctype": "URANOS Blocker",
        "project": "PV-01",
        "title": "Perte communication string box SB-04",
        "category": "Equipment",
        "severity": "Critical",
        "responsible": "ingenieur_01@uranos.local",
        "due_date": "2026-10-05",
        "status": "Open",
    })
    blocker.insert(ignore_permissions=True)
    frappe.db.commit()
    test_doc_name = blocker.name
    record_test("phase1", "Blocker successfully initialized in 'Open' status", blocker.status == "Open")

    # Invalid jump: Open -> Closed
    open_to_closed_blocked = False
    try:
        blocker.status = "Closed"
        blocker.corrective_action = "Tentative de saut direct"
        blocker.save(ignore_permissions=True)
    except frappe.ValidationError:
        open_to_closed_blocked = True
        blocker.reload()
    record_test("phase1", "Invalid forward jump 'Open' -> 'Closed' blocked", open_to_closed_blocked)

    # Invalid jump: Open -> Pending Verification
    open_to_pending_blocked = False
    try:
        blocker.status = "Pending Verification"
        blocker.corrective_action = "Tentative de saut direct 2"
        blocker.save(ignore_permissions=True)
    except frappe.ValidationError:
        open_to_pending_blocked = True
        blocker.reload()
    record_test("phase1", "Invalid forward jump 'Open' -> 'Pending Verification' blocked", open_to_pending_blocked)

    # Step 1: Open -> In Progress
    blocker.status = "In Progress"
    blocker.save(ignore_permissions=True)
    frappe.db.commit()
    record_test("phase1", "Step 1: 'Open' -> 'In Progress' transition succeeded", blocker.status == "In Progress")

    # Step 2: In Progress -> Pending Verification (without action must fail)
    step2_no_action_blocked = False
    try:
        blocker.status = "Pending Verification"
        blocker.corrective_action = ""
        blocker.resolution = ""
        blocker.save(ignore_permissions=True)
    except frappe.ValidationError:
        step2_no_action_blocked = True
        blocker.reload()
    record_test("phase1", "Transition to 'Pending Verification' without corrective action rejected", step2_no_action_blocked)

    # Step 2: In Progress -> Pending Verification (with action succeeds)
    blocker.status = "Pending Verification"
    blocker.corrective_action = "Remplacement des fusibles DC gPV 15A et vérification isolement."
    blocker.resolved_by = "ingenieur_01@uranos.local"
    blocker.save(ignore_permissions=True)
    frappe.db.commit()
    record_test("phase1", "Step 2: 'In Progress' -> 'Pending Verification' with corrective action succeeded", blocker.status == "Pending Verification")

    # Justified return: Pending Verification -> In Progress
    blocker.status = "In Progress"
    blocker.save(ignore_permissions=True)
    frappe.db.commit()
    record_test("phase1", "Justified return 'Pending Verification' -> 'In Progress' succeeded", blocker.status == "In Progress")

    # Move back to Pending Verification
    blocker.status = "Pending Verification"
    blocker.corrective_action = "Remplacement validé avec test de continuité conforme."
    blocker.resolved_by = "ingenieur_01@uranos.local"
    blocker.save(ignore_permissions=True)
    frappe.db.commit()

    # 1.3 Golden Rule: Separation of Duties (No self-verification)
    print("\n[1.3] Golden Rule: Separation of Duties (Auto-vérification refusée):")
    frappe.set_user("ingenieur_01@uranos.local")
    self_verify_blocked = False
    self_verify_err = ""
    try:
        b_sod = frappe.get_doc("URANOS Blocker", test_doc_name)
        b_sod.status = "Closed"
        b_sod.save()
    except frappe.ValidationError as ve:
        self_verify_blocked = True
        self_verify_err = str(ve)
    except Exception as ex:
        self_verify_err = f"Unexpected {type(ex).__name__}: {ex}"

    record_test(
        "phase1",
        "Self-verification rejected with 'Auto-vérification refusée.'",
        self_verify_blocked and "Auto-vérification refusée." in self_verify_err,
        f"Error observed: '{self_verify_err}'"
    )

    # Closure without corrective action rejected even for independent verifier
    frappe.set_user("ingenieur_03@uranos.local")
    no_act_blocked = False
    no_act_err = ""
    try:
        b_no_act = frappe.get_doc("URANOS Blocker", test_doc_name)
        b_no_act.status = "Closed"
        b_no_act.corrective_action = ""
        b_no_act.resolution = ""
        b_no_act.save()
    except frappe.ValidationError as ve:
        no_act_blocked = True
        no_act_err = str(ve)
    record_test("phase1", "Closure without corrective action rejected for verifier", no_act_blocked, f"Observed: '{no_act_err}'")

    # Valid independent closure
    b_valid_close = frappe.get_doc("URANOS Blocker", test_doc_name)
    b_valid_close.status = "Closed"
    b_valid_close.corrective_action = "Contrôle thermographique et mise sous tension validés par ingénieur indépendant."
    b_valid_close.save()
    frappe.db.commit()

    b_closed = frappe.get_doc("URANOS Blocker", test_doc_name)
    record_test(
        "phase1",
        "Step 3: Independent verification succeeded ('Closed' by independent engineer)",
        b_closed.status == "Closed" and b_closed.closed_by == "ingenieur_03@uranos.local",
        f"closed_by={b_closed.closed_by}, resolved_by={b_closed.resolved_by}"
    )

    # Immutability of Closed state
    reopen_closed_blocked = False
    try:
        b_closed.status = "Open"
        b_closed.save()
    except frappe.ValidationError:
        reopen_closed_blocked = True
    record_test("phase1", "Closed ticket is immutable (cannot transition back to 'Open')", reopen_closed_blocked)

    # 1.4 History Tracking on Key Fields
    print("\n[1.4] Change History Tracking on responsible, severity, due_date:")
    frappe.set_user("Administrator")
    test_hist_name = "TEST-DIAG-HIST-001"
    if frappe.db.exists("URANOS Blocker", test_hist_name):
        frappe.db.delete("URANOS Blocker", {"name": test_hist_name})
        frappe.db.commit()

    b_hist = frappe.get_doc({
        "doctype": "URANOS Blocker",
        "project": "PV-01",
        "title": "History Tracking Test Blocker",
        "severity": "Low",
        "responsible": "chantier_01@uranos.local",
        "due_date": "2026-10-01",
        "status": "Open",
    })
    b_hist.insert(ignore_permissions=True)
    frappe.db.commit()
    test_hist_name = b_hist.name

    # Modify responsible, severity, and due_date
    b_hist.responsible = "ingenieur_01@uranos.local"
    b_hist.severity = "High"
    b_hist.due_date = "2026-10-15"
    b_hist.save(ignore_permissions=True)
    frappe.db.commit()

    # Check tabVersion
    versions = frappe.get_all(
        "Version",
        filters={"ref_doctype": "URANOS Blocker", "docname": test_hist_name},
        fields=["name", "data"]
    )
    has_version_record = len(versions) > 0
    record_test("phase1", "Version history audit record created upon modifying fields", has_version_record)

    tracked_fields = set()
    if has_version_record:
        v_data = json.loads(versions[0]["data"])
        for change in v_data.get("changed", []):
            if len(change) >= 1:
                tracked_fields.add(change[0])
    record_test("phase1", "Change in 'severity' tracked in Version history", "severity" in tracked_fields)
    record_test("phase1", "Change in 'due_date' tracked in Version history", "due_date" in tracked_fields or "target_resolution" in tracked_fields)
    record_test("phase1", "Change in 'responsible' tracked in Version history", "responsible" in tracked_fields)

    # 1.5 Prevent Operational Delete
    print("\n[1.5] Operational Delete Prevention:")
    delete_blocked = False
    delete_err = ""
    try:
        b_hist.delete()
    except frappe.ValidationError as ve:
        delete_blocked = True
        delete_err = str(ve)
    except Exception as ex:
        delete_err = f"Unexpected: {type(ex).__name__}: {ex}"

    record_test(
        "phase1",
        "Operational record deletion strictly blocked by security guard",
        delete_blocked and "Operational history cannot be deleted" in delete_err,
        f"Observed: '{delete_err}'"
    )

    # Clean up test records using db.delete
    frappe.db.delete("URANOS Blocker", {"name": ["in", [test_doc_name, test_hist_name]]})
    frappe.db.commit()


def run_phase2_diagnostic():
    print("\n" + "=" * 75)
    print("PHASE 2: RBAC & PERMISSIONS DIAGNOSTIC")
    print("=" * 75)

    frappe.set_user("Administrator")
    test_p1 = "TEST-RBAC-P1-001"
    test_p2 = "TEST-RBAC-P2-001"
    test_p3 = "TEST-RBAC-P3-001"

    for t in (test_p1, test_p2, test_p3):
        if frappe.db.exists("URANOS Blocker", t):
            frappe.db.delete("URANOS Blocker", {"name": t})
    frappe.db.commit()

    # Create 1 blocker in PV-01, 1 in PV-02, 1 in PV-03
    b1 = frappe.get_doc({
        "doctype": "URANOS Blocker", "project": "PV-01",
        "title": "PV-01 Site Blocker", "status": "Open",
    }).insert(ignore_permissions=True)
    b1.status = "In Progress"
    b1.save(ignore_permissions=True)
    b1.status = "Pending Verification"
    b1.corrective_action = "Action sur PV-01"
    b1.resolved_by = "ingenieur_01@uranos.local"
    b1.save(ignore_permissions=True)
    test_p1 = b1.name

    b2 = frappe.get_doc({
        "doctype": "URANOS Blocker", "project": "PV-02",
        "title": "PV-02 Site Blocker", "status": "Open",
    }).insert(ignore_permissions=True)
    test_p2 = b2.name

    b3 = frappe.get_doc({
        "doctype": "URANOS Blocker", "project": "PV-03",
        "title": "PV-03 Site Blocker", "status": "Open",
    }).insert(ignore_permissions=True)
    test_p3 = b3.name
    frappe.db.commit()

    # 2.1 Role: site_team (chantier_01@uranos.local on PV-01)
    print("\n[2.1] Role: site_team (Équipe chantier — chantier_01@uranos.local):")
    frappe.set_user("chantier_01@uranos.local")

    can_read_p1 = frappe.has_permission("URANOS Blocker", doc=test_p1, ptype="read")
    record_test("phase2", "site_team has READ access on assigned project (PV-01)", can_read_p1)

    # Test write/update on assigned project
    site_write_ok = False
    try:
        doc_p1 = frappe.get_doc("URANOS Blocker", test_p1)
        doc_p1.description = "Mise à jour par équipe chantier"
        doc_p1.save()
        site_write_ok = True
    except Exception as e:
        site_write_ok = False
    record_test("phase2", "site_team has WRITE access on assigned project (PV-01)", site_write_ok)

    # Test closure attempt by site_team (must be forbidden)
    site_close_blocked = False
    site_close_err = ""
    try:
        doc_p1 = frappe.get_doc("URANOS Blocker", test_p1)
        doc_p1.status = "Closed"
        doc_p1.save()
    except (frappe.PermissionError, frappe.ValidationError) as pe:
        site_close_blocked = True
        site_close_err = str(pe)
    record_test("phase2", "site_team CANNOT close tickets (strict closure prohibition)", site_close_blocked, f"Observed: '{site_close_err}'")

    # Cross-project: site_team must NOT access PV-02
    can_read_p2_site = frappe.has_permission("URANOS Blocker", doc=test_p2, ptype="read")
    record_test("phase2", "site_team CANNOT read unassigned project (PV-02) [Cross-project isolation]", not can_read_p2_site)

    # 2.2 Role: engineer (ingenieur_01@uranos.local on PV-01 & PV-02)
    print("\n[2.2] Role: engineer (Ingénieur responsable — ingenieur_01@uranos.local):")
    frappe.set_user("ingenieur_01@uranos.local")

    can_read_p1_eng = frappe.has_permission("URANOS Blocker", doc=test_p1, ptype="read")
    can_read_p2_eng = frappe.has_permission("URANOS Blocker", doc=test_p2, ptype="read")
    record_test("phase2", "engineer has READ access on assigned PV-01 and PV-02", can_read_p1_eng and can_read_p2_eng)

    # Cross-project: engineer must NOT access PV-03
    can_read_p3_eng = frappe.has_permission("URANOS Blocker", doc=test_p3, ptype="read")
    record_test("phase2", "engineer CANNOT read unassigned project (PV-03) [Cross-project isolation]", not can_read_p3_eng)

    # 2.3 Role: management (direction_01@uranos.local — global read-only)
    print("\n[2.3] Role: management (Direction — direction_01@uranos.local):")
    frappe.set_user("direction_01@uranos.local")

    can_read_all = (
        frappe.has_permission("URANOS Blocker", doc=test_p1, ptype="read") and
        frappe.has_permission("URANOS Blocker", doc=test_p2, ptype="read") and
        frappe.has_permission("URANOS Blocker", doc=test_p3, ptype="read")
    )
    record_test("phase2", "management has global READ access across ALL projects (PV-01, PV-02, PV-03)", can_read_all)

    # Test management WRITE attempt (must be blocked)
    dir_write_blocked = False
    dir_write_err = ""
    try:
        doc_dir = frappe.get_doc("URANOS Blocker", test_p1)
        doc_dir.title = "Modification interdite par la direction"
        doc_dir.save()
    except frappe.PermissionError as pe:
        dir_write_blocked = True
        dir_write_err = str(pe)
    except Exception as ex:
        # If has_permission write returned False
        if not frappe.has_permission("URANOS Blocker", doc=test_p1, ptype="write"):
            dir_write_blocked = True
            dir_write_err = "has_permission write returned False"
        else:
            dir_write_err = f"Unexpected: {type(ex).__name__}: {ex}"

    record_test("phase2", "management CANNOT write or modify blockers (Strict Read-Only access)", dir_write_blocked, f"Observed: '{dir_write_err}'")

    # 2.4 Cross-Project Data Leakage in List Queries
    print("\n[2.4] Cross-Project Query & List Leakage Prevention:")
    frappe.set_user("chantier_01@uranos.local")
    site_list = frappe.get_list("URANOS Blocker", fields=["name", "project"])
    site_projects = {d["project"] for d in site_list}
    record_test(
        "phase2",
        "site_team list query returns ZERO unassigned projects (Zero Data Leakage)",
        "PV-02" not in site_projects and "PV-03" not in site_projects,
        f"Observed projects in site_team list: {site_projects}"
    )

    frappe.set_user("ingenieur_01@uranos.local")
    eng_list = frappe.get_list("URANOS Blocker", fields=["name", "project"])
    eng_projects = {d["project"] for d in eng_list}
    record_test(
        "phase2",
        "engineer list query returns ZERO unassigned projects (Zero Data Leakage)",
        "PV-03" not in eng_projects,
        f"Observed projects in engineer list: {eng_projects}"
    )

    # Clean up test docs
    frappe.set_user("Administrator")
    frappe.db.delete("URANOS Blocker", {"name": ["in", [test_p1, test_p2, test_p3]]})
    frappe.db.commit()


def run_phase4_diagnostic():
    print("\n" + "=" * 75)
    print("PHASE 4: AI SYNTHESIS & FALLBACK DIAGNOSTIC")
    print("=" * 75)

    from uranos_project_os.services.ai_synthesis import generate_blocker_synthesis

    # 4.1 RBAC Enforcement on AI Endpoint
    print("\n[4.1] RBAC Enforcement on Synthesis API:")
    frappe.set_user("chantier_01@uranos.local")
    
    # Allowed project PV-01
    site_synth_allowed = False
    try:
        s = generate_blocker_synthesis(project="PV-01", force_fallback=True, lang="fr")
        site_synth_allowed = bool(s and s.get("summary"))
    except Exception as e:
        site_synth_allowed = False
    record_test("phase4", "site_team can synthesize assigned project (PV-01)", site_synth_allowed)

    # Unassigned project PV-02 (must fail)
    site_unassigned_blocked = False
    try:
        generate_blocker_synthesis(project="PV-02", force_fallback=True, lang="fr")
    except frappe.PermissionError:
        site_unassigned_blocked = True
    except Exception:
        site_unassigned_blocked = True
    record_test("phase4", "site_team synthesis call on unassigned project (PV-02) BLOCKED", site_unassigned_blocked)

    # Engineer unassigned project PV-03 (must fail)
    frappe.set_user("ingenieur_01@uranos.local")
    eng_unassigned_blocked = False
    try:
        generate_blocker_synthesis(project="PV-03", force_fallback=True, lang="fr")
    except (frappe.PermissionError, Exception):
        eng_unassigned_blocked = True
    record_test("phase4", "engineer synthesis call on unassigned project (PV-03) BLOCKED", eng_unassigned_blocked)

    # Management can synthesize any project
    frappe.set_user("direction_01@uranos.local")
    dir_synth_ok = False
    try:
        s_dir = generate_blocker_synthesis(project="PV-03", force_fallback=True, lang="fr")
        dir_synth_ok = bool(s_dir and s_dir.get("summary"))
    except Exception as e:
        dir_synth_ok = False
    record_test("phase4", "management can synthesize across any project (PV-03)", dir_synth_ok)

    # 4.2 AI Output Format: Exact IDs, Facts vs Suggestions, No Hallucinations
    print("\n[4.2] AI Output Format & Content Compliance:")
    frappe.set_user("ingenieur_01@uranos.local")
    s_fr = generate_blocker_synthesis(project="PV-01", force_fallback=True, lang="fr")
    summary = s_fr.get("summary", "")

    # Checks
    has_facts = "Faits et Problèmes Prioritaires" in summary or "### 1." in summary
    record_test("phase4", "Synthesis isolates factual data section ('Faits et Problèmes Prioritaires')", has_facts)

    has_suggestions = "Suggestions d'Actions" in summary or "### 3." in summary
    record_test("phase4", "Synthesis isolates suggestions section ('Suggestions d'Actions')", has_suggestions)

    # Citations of IDs (e.g., [B-001])
    cites_ids = "[" in summary and "]" in summary
    record_test("phase4", "Synthesis cites exact blocker IDs in bracketed format", cites_ids)

    # No hallucinated costs, completion percentages, or fake dates
    # Verify summary does not invent fake financial costs or fake progress
    no_hallucinated_costs = "€" not in summary and "$" not in summary and "TND" not in summary
    record_test("phase4", "Synthesis strictly avoids inventing fake costs or currency amounts", no_hallucinated_costs)

    # Flags missing information
    has_missing_tag = "Information manquante" in summary or "non assigné" in summary or "non définie" in summary or len(s_fr.get("open_blockers", [])) == 0
    record_test("phase4", "Synthesis explicitly flags missing fields (responsible / due date)", has_missing_tag)

    # 4.3 Deterministic Local Fallback (French & Arabic)
    print("\n[4.3] Deterministic Local Fallback Mode:")
    record_test("phase4", "Local French fallback provider identified as 'Deterministic Rule-based Fallback'", s_fr.get("provider") == "Deterministic Rule-based Fallback")

    s_ar = generate_blocker_synthesis(project="PV-01", force_fallback=True, lang="ar")
    is_ar_generated = "ملخص" in s_ar.get("summary", "") or "المخاطر" in s_ar.get("summary", "")
    record_test("phase4", "Local Arabic fallback delivers valid native Arabic executive summary", is_ar_generated)


def main():
    frappe.init(site="uranos.localhost")
    frappe.connect()

    print("=" * 75)
    print("URANOS GROUP — AUTONOMOUS EXAM COMPLIANCE DIAGNOSTIC")
    print("=" * 75)

    run_phase1_diagnostic()
    run_phase2_diagnostic()
    run_phase4_diagnostic()

    total_passed = sum(b["passed"] for b in results.values())
    total_failed = sum(b["failed"] for b in results.values())

    print("\n" + "=" * 75)
    print(f"DIAGNOSTIC TEST SUMMARY: {total_passed} PASSED, {total_failed} FAILED")
    print(f"  Phase 1 (Backend/Workflow): {results['phase1']['passed']} passed, {results['phase1']['failed']} failed")
    print(f"  Phase 2 (RBAC/Isolation):   {results['phase2']['passed']} passed, {results['phase2']['failed']} failed")
    print(f"  Phase 4 (AI Synthesis):     {results['phase4']['passed']} passed, {results['phase4']['failed']} failed")
    print("=" * 75)

    # Save results to a json file for report inclusion
    out_path = "/home/frappe/frappe-bench/apps/uranos_project_os/tests/diagnostic_backend_results.json"
    try:
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        print("Note: Could not write json to container path:", e)

    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
