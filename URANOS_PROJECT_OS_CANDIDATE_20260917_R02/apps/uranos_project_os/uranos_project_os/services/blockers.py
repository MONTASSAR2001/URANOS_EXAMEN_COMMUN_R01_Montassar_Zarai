"""Service adapter layer for URANOS Blocker (Site Issue) lifecycle transitions.

Strict Hexagonal Architecture:
Adapts Frappe DB / Web APIs to pure Domain state machine in domain/blockers.py.
Enforces pessimistic locking (Project first), project isolation, and authorized transitions.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Optional

import frappe
from uranos_project_os.controllers import authorized_transition
from uranos_project_os.domain.blockers import (
    DomainRuleViolation,
    HistoryEntry,
    IssueStatus,
    SiteIssue,
)
from uranos_project_os.services.common import (
    actor,
    require_post,
    require_project,
    scoped_doc,
)

CAPTION_RE = re.compile(r"^\[(.*?)\]\s*(.*?)\s*->\s*(.*?)\s*\|\s*(.*)$")


def _locked(name: str):
    """Pessimistic locking helper strictly preventing deadlocks across concurrent requests.

    Always locks the parent Project first before locking the URANOS Blocker record.
    """
    initial = scoped_doc("URANOS Blocker", name)
    scoped_doc("Project", initial.project, lock=True)
    return scoped_doc("URANOS Blocker", name, lock=True)


def _to_domain(doc) -> SiteIssue:
    """Map Frappe 'URANOS Blocker' document to pure Python SiteIssue entity."""
    status = IssueStatus(doc.status) if doc.status else IssueStatus.OPEN
    lost_hours = Decimal(str(doc.lost_hours)) if doc.get("lost_hours") is not None else Decimal("0")

    history_log = []
    for row in doc.get("evidence", []):
        caption = row.get("caption") or ""
        changed_by = row.get("captured_by") or doc.get("reported_by") or "Administrator"
        match = CAPTION_RE.match(caption)
        if match:
            field_name, old_val, new_val, just = match.groups()
            old_val = None if old_val == "None" else old_val
            new_val = None if new_val == "None" else new_val
            history_log.append(
                HistoryEntry(
                    changed_field=field_name,
                    old_value=old_val,
                    new_value=new_val,
                    changed_by=changed_by,
                    justification=just,
                )
            )
        else:
            try:
                data = json.loads(caption)
                if isinstance(data, dict) and "field" in data:
                    history_log.append(
                        HistoryEntry(
                            changed_field=data["field"],
                            old_value=data.get("old"),
                            new_value=data.get("new"),
                            changed_by=changed_by,
                            justification=data.get("justification", ""),
                        )
                    )
            except Exception:
                pass

    return SiteIssue(
        title=doc.title,
        status=status,
        severity=doc.severity or "Low",
        responsible=doc.responsible,
        due_date=doc.get("target_resolution") or doc.get("due_date"),
        resolved_by=doc.resolved_by,
        closed_by=doc.closed_by,
        corrective_action=doc.resolution,
        history_log=history_log,
        project=doc.project,
        issue_id=doc.name,
        category=doc.category or "Quality",
        description=doc.description,
        lost_hours=lost_hours,
    )


def _apply_to_doc(issue: SiteIssue, doc) -> None:
    """Map pure Domain SiteIssue state back to Frappe document and sync history log."""
    doc.title = issue.title
    doc.status = issue.status.value if isinstance(issue.status, IssueStatus) else str(issue.status)
    doc.severity = issue.severity
    doc.responsible = issue.responsible
    doc.resolved_by = issue.resolved_by
    doc.closed_by = issue.closed_by
    doc.resolution = issue.corrective_action
    if issue.due_date:
        doc.target_resolution = issue.due_date
    if issue.category:
        doc.category = issue.category
    if issue.description is not None:
        doc.description = issue.description
    if getattr(doc, "flags", None) is None:
        try:
            doc.flags = getattr(frappe, "_dict", dict)()
        except Exception:
            pass
    if getattr(doc, "flags", None) is not None:
        try:
            doc.flags.ignore_mandatory = True
        except (AttributeError, TypeError):
            pass

    existing_captions = {row.caption for row in doc.get("evidence", []) if row.caption}
    for entry in issue.history_log:
        caption = f"[{entry.changed_field}] {entry.old_value} -> {entry.new_value} | {entry.justification}"
        if caption not in existing_captions:
            doc.append(
                "evidence",
                {
                    "doctype": "URANOS Evidence",
                    "caption": caption,
                    "captured_by": entry.changed_by,
                    "captured_at": frappe.utils.now(),
                },
            )
            existing_captions.add(caption)


@frappe.whitelist()
def assign_blocker(name: str, responsible: str, justification: str = ""):
    """Assign responsibility for resolving a blocker and transition status to In Progress."""
    require_post()
    user = actor()
    doc = _locked(name)
    require_project(doc)

    issue = _to_domain(doc)
    try:
        issue.assign_issue(responsible_user=responsible, assigned_by=user, justification=justification)
    except DomainRuleViolation as e:
        frappe.throw(str(e), frappe.ValidationError)

    _apply_to_doc(issue, doc)
    with authorized_transition():
        doc.save(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def submit_resolution(name: str, corrective_action: str):
    """Submit corrective action and transition status to Pending Verification."""
    require_post()
    user = actor()
    doc = _locked(name)
    require_project(doc)

    issue = _to_domain(doc)
    try:
        issue.resolve_issue(resolved_by_user=user, corrective_action=corrective_action)
    except DomainRuleViolation as e:
        frappe.throw(str(e), frappe.ValidationError)

    _apply_to_doc(issue, doc)
    doc.resolution_submitted_at = frappe.utils.now()
    with authorized_transition():
        doc.save(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def close_blocker(name: str, review_reason: Optional[str] = None):
    """Close the blocker after independent verification, enforcing the Golden Rule."""
    require_post()
    user = actor()
    doc = _locked(name)
    require_project(doc)

    issue = _to_domain(doc)
    try:
        issue.close_issue(closed_by_user=user)
    except DomainRuleViolation as e:
        frappe.throw(str(e), frappe.ValidationError)

    _apply_to_doc(issue, doc)
    if review_reason:
        doc.review_reason = review_reason
    doc.closed_at = frappe.utils.now()
    doc.resolved_at = frappe.utils.now()
    with authorized_transition():
        doc.save(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def reopen_blocker(name: str, reason: str):
    """Reopen a rejected blocker back to In Progress for rework with a mandatory reason."""
    require_post()
    user = actor()
    doc = _locked(name)
    require_project(doc)

    issue = _to_domain(doc)
    try:
        issue.reopen_issue(reopened_by=user, reason=reason)
    except DomainRuleViolation as e:
        frappe.throw(str(e), frappe.ValidationError)

    _apply_to_doc(issue, doc)
    doc.resolution_submitted_at = None
    with authorized_transition():
        doc.save(ignore_permissions=True)
    return doc.as_dict()
