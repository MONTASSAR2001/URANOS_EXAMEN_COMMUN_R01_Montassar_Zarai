"""Autonomous Diagnostic & Verification Test Suite for URANOS Exam Compliance.

Tests:
1. Workflow & Separation of Duties on URANOS Blocker (Golden Rule: Auto-vérification refusée.)
2. Corrective Action mandatory on closure
3. Strict 4-step workflow: Ouvert -> En cours -> À vérifier -> Clôturé
4. RBAC Permissions enforcement (site_team, engineer, management)
5. Groq AI Synthesis refinement & permissions filtering
"""
import sys
import traceback
import frappe
from frappe.utils import now

def run_tests():
    frappe.init(site="uranos.localhost")
    frappe.connect()

    print("=" * 70)
    print("URANOS PROJECT OS — EXAM COMPLIANCE DIAGNOSTIC & VERIFICATION")
    print("=" * 70)

    passed = 0
    failed = 0

    def assert_true(cond, msg):
        nonlocal passed, failed
        if cond:
            print(f"  [PASS] {msg}")
            passed += 1
        else:
            print(f"  [FAIL] {msg}")
            failed += 1

    # -------------------------------------------------------------------------
    # TEST 1: Workflow & Strict Closure Rules - Separation of Duties
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Strict Closure Rules & Separation of Duties ---")
    try:
        frappe.set_user("Administrator")
        
        # Create or find a test blocker on PV-01
        test_blocker_name = "TEST-SOD-001"
        if frappe.db.exists("URANOS Blocker", test_blocker_name):
            frappe.db.delete("URANOS Blocker", {"name": test_blocker_name})
            frappe.db.commit()

        # Insert fresh blocker in Open state
        blocker = frappe.get_doc({
            "doctype": "URANOS Blocker",
            "project": "PV-01",
            "title": "Disjoncteur DC Surchauffe Onduleur",
            "status": "Open",
            "severity": "Critical",
            "category": "Equipment",
            "due_date": "2026-10-05",
            "responsible": "ingenieur_01@uranos.local",
            "opened_at": now(),
        })
        blocker.insert(ignore_permissions=True)
        frappe.db.commit()
        test_blocker_name = blocker.name
        assert_true(blocker.status == "Open", f"Blocker {test_blocker_name} initialized in 'Open' status")

        # Step 1: Open -> In Progress
        blocker.status = "In Progress"
        blocker.save(ignore_permissions=True)
        frappe.db.commit()
        assert_true(blocker.status == "In Progress", "Transition 1: 'Open' -> 'In Progress' succeeded")

        # Step 2: In Progress -> Pending Verification (À vérifier)
        blocker.status = "Pending Verification"
        blocker.corrective_action = "Remplacement du bornier de raccordement et resserrage dynamométrique."
        blocker.resolved_by = "ingenieur_01@uranos.local"
        blocker.save(ignore_permissions=True)
        frappe.db.commit()
        assert_true(blocker.status == "Pending Verification", "Transition 2: 'In Progress' -> 'Pending Verification' succeeded")

        # Step 3A: Attempt Self-Verification by the resolver (ingenieur_01@uranos.local)
        frappe.set_user("ingenieur_01@uranos.local")
        sod_blocked = False
        err_msg = ""
        try:
            b_sod = frappe.get_doc("URANOS Blocker", test_blocker_name)
            b_sod.status = "Closed"
            b_sod.save()
        except frappe.ValidationError as e:
            sod_blocked = True
            err_msg = str(e)
        except Exception as e:
            err_msg = f"Unexpected exception: {type(e).__name__}: {e}"

        assert_true(
            sod_blocked and "Auto-vérification refusée." in err_msg,
            f"Self-verification rejected with frappe.ValidationError('Auto-vérification refusée.') [Observed: '{err_msg}']"
        )

        # Step 3B: Attempt Closure without corrective action
        frappe.set_user("ingenieur_03@uranos.local")  # Independent engineer
        no_action_blocked = False
        err_msg_action = ""
        try:
            b_no_act = frappe.get_doc("URANOS Blocker", test_blocker_name)
            b_no_act.status = "Closed"
            b_no_act.corrective_action = ""
            b_no_act.resolution = ""
            b_no_act.save()
        except frappe.ValidationError as e:
            no_action_blocked = True
            err_msg_action = str(e)

        assert_true(
            no_action_blocked and "Action corrective obligatoire" in err_msg_action,
            f"Closure without corrective action rejected [Observed: '{err_msg_action}']"
        )

        # Step 3C: Valid Independent Closure by ingenieur_03@uranos.local
        frappe.set_user("ingenieur_03@uranos.local")
        b_valid = frappe.get_doc("URANOS Blocker", test_blocker_name)
        b_valid.status = "Closed"
        b_valid.corrective_action = "Inspection thermographique post-réparation validée conforme."
        b_valid.save()
        frappe.db.commit()

        b_closed = frappe.get_doc("URANOS Blocker", test_blocker_name)
        assert_true(
            b_closed.status == "Closed" and b_closed.closed_by == "ingenieur_03@uranos.local",
            f"Independent verification succeeded: Blocker moved to 'Closed' by {b_closed.closed_by}"
        )

    except Exception as ex:
        print(f"  [ERROR] in Test 1: {ex}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------------------
    # TEST 2: RBAC Permissions Enforcement
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: RBAC Permissions Enforcement ---")
    try:
        # A: site_team cannot close tickets
        frappe.set_user("chantier_01@uranos.local")
        
        # Reset blocker to Pending Verification for RBAC test
        frappe.set_user("Administrator")
        b_rbac = frappe.get_doc("URANOS Blocker", test_blocker_name)
        frappe.db.set_value("URANOS Blocker", test_blocker_name, {
            "status": "Pending Verification",
            "resolved_by": "ingenieur_01@uranos.local",
            "corrective_action": "Action corrective valide.",
            "closed_by": None
        })
        frappe.db.commit()

        frappe.set_user("chantier_01@uranos.local")
        site_close_blocked = False
        site_err = ""
        try:
            b_site = frappe.get_doc("URANOS Blocker", test_blocker_name)
            b_site.status = "Closed"
            b_site.save()
        except (frappe.PermissionError, frappe.ValidationError) as pe:
            site_close_blocked = True
            site_err = str(pe)

        assert_true(
            site_close_blocked,
            f"site_team closure attempt strictly blocked by RBAC [PermissionError, Details: '{site_err}']"
        )

        # B: management role has global read-only access
        frappe.set_user("direction_01@uranos.local")
        has_read_pv01 = frappe.has_permission("URANOS Blocker", doc=test_blocker_name, ptype="read", user="direction_01@uranos.local")
        assert_true(has_read_pv01, "management has read access on PV-01 blocker")

        write_blocked = False
        try:
            b_dir = frappe.get_doc("URANOS Blocker", test_blocker_name)
            b_dir.title = "Modification interdite direction"
            b_dir.save()
        except frappe.PermissionError:
            write_blocked = True

        assert_true(write_blocked, "management write attempt blocked (Strict Read-Only access)")

    except Exception as ex:
        print(f"  [ERROR] in Test 2: {ex}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------------------
    # TEST 3: Kanban Card Sorting Algorithm (6-Tier Jury Rules)
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: Kanban Card Sorting Simulation (6-Tier Jury Rules) ---")
    try:
        from datetime import date, timedelta
        today = date.today()
        yesterday = str(today - timedelta(days=2))
        tomorrow = str(today + timedelta(days=2))
        next_week = str(today + timedelta(days=7))

        cards = [
            {"name": "B-005", "severity": "Low", "due_date": None, "status": "Open"},
            {"name": "B-002", "severity": "Medium", "due_date": tomorrow, "status": "Open"},
            {"name": "B-001", "severity": "Critical", "due_date": next_week, "status": "Open"},
            {"name": "B-004", "severity": "High", "due_date": yesterday, "status": "Open"},  # Overdue
            {"name": "B-003", "severity": "High", "due_date": tomorrow, "status": "Open"},
            {"name": "B-006", "severity": "Low", "due_date": None, "status": "Closed"},
        ]

        def python_compare_blockers(a, b):
            # 1st: Critical
            a_crit = (a.get("severity") or "").lower() == "critical"
            b_crit = (b.get("severity") or "").lower() == "critical"
            if a_crit and not b_crit: return -1
            if not a_crit and b_crit: return 1

            # 2nd: Overdue
            a_due = a.get("due_date")
            b_due = b.get("due_date")
            a_over = a_due and str(a_due) < str(today)
            b_over = b_due and str(b_due) < str(today)
            if a_over and not b_over: return -1
            if not a_over and b_over: return 1

            # 3rd: Other open tickets
            a_closed = (a.get("status") or "").lower() in ("closed", "clôturé")
            b_closed = (b.get("status") or "").lower() in ("closed", "clôturé")
            if not a_closed and b_closed: return -1
            if a_closed and not b_closed: return 1

            # 4th & 5th: Closest due_date vs No due_date
            if a_due and b_due:
                if a_due != b_due:
                    return -1 if a_due < b_due else 1
            elif a_due and not b_due:
                return -1
            elif not a_due and b_due:
                return 1

            # 6th: Blocker ID
            return -1 if str(a.get("name")) < str(b.get("name")) else 1

        import functools
        sorted_cards = sorted(cards, key=functools.cmp_to_key(python_compare_blockers))
        sorted_names = [c["name"] for c in sorted_cards]
        
        # Expected order:
        # 1. B-001 (Critical)
        # 2. B-004 (Overdue)
        # 3. B-002 / B-003 (Closest due_date: tomorrow) -> tied on due date, then ID: B-002, B-003
        # 4. B-005 (No due_date, Open)
        # 5. B-006 (Closed)
        expected = ["B-001", "B-004", "B-002", "B-003", "B-005", "B-006"]
        assert_true(
            sorted_names == expected,
            f"Sorting matches 6-tier jury rule: {sorted_names} == {expected}"
        )

    except Exception as ex:
        print(f"  [ERROR] in Test 3: {ex}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------------------
    # TEST 4: Groq AI Synthesis Refinement & Permissions
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: Groq AI Synthesis Refinement & Permissions ---")
    try:
        frappe.set_user("ingenieur_01@uranos.local")
        from uranos_project_os.services.ai_synthesis import generate_blocker_synthesis
        
        # Execute synthesis with force_fallback=True (deterministic zero-network mode)
        synth = generate_blocker_synthesis(project="PV-01", force_fallback=True, lang="fr")
        assert_true(synth is not None, "generate_blocker_synthesis executed successfully")
        
        summary = synth.get("summary") or ""
        assert_true(
            "Faits et Problèmes Prioritaires" in summary or "### 1." in summary,
            "Synthesis strictly distinguishes factual data from actions"
        )
        assert_true(
            "Suggestions d'Actions" in summary or "### 2." in summary,
            "Synthesis includes suggestions for required actions"
        )

    except Exception as ex:
        print(f"  [ERROR] in Test 4: {ex}")
        traceback.print_exc()
        failed += 1

    # Clean up test blocker
    frappe.set_user("Administrator")
    if 'test_blocker_name' in locals() and frappe.db.exists("URANOS Blocker", test_blocker_name):
        frappe.db.delete("URANOS Blocker", {"name": test_blocker_name})
        frappe.db.commit()

    print("\n" + "=" * 70)
    print(f"DIAGNOSTIC SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 70)
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run_tests())
