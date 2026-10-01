"""Advanced RAG Real-Time Injection, Accuracy Verification & Safe Cleanup Test.

Executes:
1. Injects real-time dummy blocker 'TEST-RAG-999: Advanced Integration Anomaly' (Critical, 42.5h) into MariaDB.
2. Directly invokes chat_with_project_ai to verify that the RAG pipeline dynamically detects
   and retrieves the new record with exact numerical and factual precision.
3. Cleans up the dummy record from MariaDB to preserve environment integrity.
4. Returns a comprehensive diagnostic report.
"""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Dict

import frappe
from uranos_project_os.services.ai_synthesis import chat_with_project_ai


def run_advanced_rag_verification() -> Dict[str, Any]:
    print("=" * 70)
    print("🚀 STARTING ADVANCED RAG REAL-TIME VERIFICATION WORKFLOW")
    print("=" * 70)

    project = "PV-01"
    test_title = "TEST-RAG-999: Advanced Integration Anomaly"
    test_lost_hours = 42.5
    test_severity = "Critical"
    test_category = "Quality"
    test_user = "ingenieur_01@uranos.local"

    # Step 0: Ensure any old leftover test record is cleared
    existing = frappe.db.get_value("URANOS Blocker", {"title": test_title}, "name")
    if existing:
        print(f"🧹 Clearing prior test record: {existing}")
        frappe.db.delete("URANOS Blocker", {"name": existing})
        frappe.db.commit()

    # Step 1: Real-Time Data Injection
    print(f"\n[STEP 1] Injecting dummy anomaly record into MariaDB for project '{project}'...")
    frappe.set_user(test_user)
    
    doc = frappe.get_doc({
        "doctype": "URANOS Blocker",
        "project": project,
        "title": test_title,
        "severity": test_severity,
        "category": test_category,
        "status": "Open",
        "lost_hours": test_lost_hours,
        "description": "Dummy anomaly record injected to verify real-time RAG context retrieval and numerical accuracy without hallucination.",
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    injected_doc_name = doc.name
    print(f"  ✓ Injected record ID: {injected_doc_name}")
    print(f"  ✓ Title: {doc.title}")
    print(f"  ✓ Severity: {doc.severity}")
    print(f"  ✓ Lost Hours: {doc.lost_hours}")
    print(f"  ✓ Status: {doc.status}")

    # Verify directly in MariaDB before query
    db_record = frappe.db.get_value(
        "URANOS Blocker",
        injected_doc_name,
        ["name", "title", "severity", "lost_hours", "status"],
        as_dict=True,
    )
    assert db_record is not None, "Failed to confirm injection in MariaDB"
    print(f"  ✓ MariaDB confirmed persistence: {db_record}")

    # Step 2: Query AI via chat_with_project_ai
    query_message = "What is the status of the TEST-RAG-999 anomaly and how many hours were lost?"
    print(f"\n[STEP 2] Executing AI Copilot Query...")
    print(f"  Query: '{query_message}'")
    print(f"  User: {test_user} (scoped to {project})")

    ai_result = chat_with_project_ai(
        project=project,
        message=query_message,
        lang="en",
    )

    ai_reply = ai_result.get("reply", "")
    provider = ai_result.get("provider", "Unknown")
    is_ai = ai_result.get("is_ai_generated", False)

    print(f"\n[STEP 3] Evaluating AI Response Accuracy...")
    print(f"  Provider: {provider}")
    print(f"  Is AI Generated: {is_ai}")
    print(f"  Exact AI Reply:\n{'-'*50}\n{ai_reply}\n{'-'*50}")

    # Step 3: Accuracy Assertions
    reply_lower = ai_reply.lower()
    has_test_id = "test-rag-999" in reply_lower
    has_lost_hours = "42.5" in ai_reply
    has_status_or_sev = ("open" in reply_lower) or ("critical" in reply_lower)

    print(f"  ✓ Verification Checks:")
    print(f"    - Explicitly Cites 'TEST-RAG-999': {has_test_id}")
    print(f"    - Exact Numerical Match '42.5': {has_lost_hours}")
    print(f"    - Correct Status/Severity Grounding: {has_status_or_sev}")

    accuracy_passed = has_test_id and has_lost_hours and has_status_or_sev

    # Step 4: Database Cleanup
    print(f"\n[STEP 4] Cleaning up dummy record from MariaDB...")
    frappe.db.delete("URANOS Blocker", {"name": injected_doc_name})
    frappe.db.commit()

    still_exists = frappe.db.exists("URANOS Blocker", injected_doc_name)
    print(f"  ✓ Confirmation: Record exists after cleanup? {bool(still_exists)}")
    assert not still_exists, "Failed to clean up dummy record from MariaDB"
    print(f"  ✓ Production database successfully cleaned!")

    # Step 5: Post-cleanup verification query to confirm no phantom memory
    print(f"\n[STEP 5] Verifying AI behavior after cleanup (zero phantom hallucinations)...")
    post_cleanup_result = chat_with_project_ai(
        project=project,
        message="Is the TEST-RAG-999 anomaly still present in the database?",
        lang="en",
    )
    post_reply = post_cleanup_result.get("reply", "")
    print(f"  Post-cleanup Reply:\n{post_reply}")

    report = {
        "status": "SUCCESS" if accuracy_passed else "FAILED",
        "injected_record_name": injected_doc_name,
        "injected_data": {
            "title": test_title,
            "severity": test_severity,
            "lost_hours": test_lost_hours,
            "status": "Open",
        },
        "query": query_message,
        "ai_provider": provider,
        "is_ai_generated": is_ai,
        "ai_reply": ai_reply,
        "checks": {
            "has_test_id": has_test_id,
            "has_lost_hours": has_lost_hours,
            "has_status_or_sev": has_status_or_sev,
            "accuracy_passed": accuracy_passed,
        },
        "cleanup_confirmed": not still_exists,
        "post_cleanup_reply": post_reply,
    }

    print("\n" + "=" * 70)
    print("🎯 ADVANCED RAG VERIFICATION COMPLETED WITH STATUS:", report["status"])
    print("=" * 70)
    return report
