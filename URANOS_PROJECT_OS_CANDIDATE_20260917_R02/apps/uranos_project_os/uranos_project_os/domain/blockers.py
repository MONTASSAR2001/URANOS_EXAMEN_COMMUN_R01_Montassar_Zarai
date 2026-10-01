"""Pure domain model and state machine for Site Issues (Blocages).

Strict Hexagonal Architecture rule:
This file contains pure Python business logic only.
NEVER import frappe or any framework/database/IO library here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, List, Optional, Union


class DomainRuleViolation(ValueError):
    """Raised when an invariant of the pure business domain is violated."""


# Alias for compatibility with URANOS controls
RuleViolation = DomainRuleViolation


class IssueStatus(str, Enum):
    """Operational lifecycle statuses for a Site Issue (Blocage)."""

    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    PENDING_VERIFICATION = "Pending Verification"
    CLOSED = "Closed"


@dataclass
class HistoryEntry:
    """Immutable audit trail entry documenting critical field modifications."""

    changed_field: str
    old_value: Any
    new_value: Any
    changed_by: str
    justification: str
    changed_on: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.changed_field or not str(self.changed_field).strip():
            raise DomainRuleViolation("changed_field must be a non-empty string")
        if not self.changed_by or not str(self.changed_by).strip():
            raise DomainRuleViolation("changed_by must be a non-empty user identifier")


@dataclass
class SiteIssue:
    """Core domain entity representing a project obstacle / site issue."""

    title: str
    status: IssueStatus = IssueStatus.OPEN
    severity: str = "Low"
    responsible: Optional[str] = None
    due_date: Optional[Union[date, datetime, str]] = None
    resolved_by: Optional[str] = None
    closed_by: Optional[str] = None
    corrective_action: Optional[str] = None
    history_log: List[HistoryEntry] = field(default_factory=list)

    # Optional metadata attributes for project integration
    project: Optional[str] = None
    issue_id: Optional[str] = None
    category: str = "Quality"
    description: Optional[str] = None
    lost_hours: Decimal = Decimal("0")

    CRITICAL_FIELDS = frozenset({"severity", "responsible", "due_date"})

    def __post_init__(self) -> None:
        if not self.title or not str(self.title).strip():
            raise DomainRuleViolation("Issue title must be a non-empty string")
        if isinstance(self.status, str) and not isinstance(self.status, IssueStatus):
            self.status = IssueStatus(self.status)
        if self.history_log is None:
            self.history_log = []

    def update_critical_field(
        self,
        field_name: str,
        new_value: Any,
        user: str,
        justification: str,
    ) -> HistoryEntry:
        """Update an issue field.

        If the field belongs to CRITICAL_FIELDS ('severity', 'responsible', 'due_date'),
        a non-empty justification is strictly enforced and a HistoryEntry is appended.
        """
        if not hasattr(self, field_name):
            raise DomainRuleViolation(f"Field '{field_name}' does not exist on SiteIssue")

        if not user or not str(user).strip():
            raise DomainRuleViolation("The actor user making the change must be specified")

        clean_justification = str(justification or "").strip()
        is_critical = field_name in self.CRITICAL_FIELDS

        if is_critical and not clean_justification:
            raise DomainRuleViolation(
                f"Modifying critical field '{field_name}' strictly requires a non-empty justification"
            )

        old_value = getattr(self, field_name)
        setattr(self, field_name, new_value)

        entry = HistoryEntry(
            changed_field=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=user.strip(),
            justification=clean_justification,
        )
        self.history_log.append(entry)
        return entry

    def assign_issue(self, responsible_user: str, assigned_by: str, justification: str = "") -> None:
        """Assign responsibility for resolving the issue and move to IN_PROGRESS."""
        if not responsible_user or not str(responsible_user).strip():
            raise DomainRuleViolation("Responsible user must be a non-empty identifier")

        self.update_critical_field("responsible", responsible_user.strip(), assigned_by, justification)
        if self.status == IssueStatus.OPEN:
            self.status = IssueStatus.IN_PROGRESS

    def resolve_issue(self, resolved_by_user: str, corrective_action: str) -> None:
        """Record the corrective action and submit for independent verification."""
        if not resolved_by_user or not str(resolved_by_user).strip():
            raise DomainRuleViolation("resolved_by_user must be a non-empty identifier")

        if not corrective_action or not str(corrective_action).strip():
            raise DomainRuleViolation("Cannot resolve an issue without a recorded corrective action")

        self.resolved_by = resolved_by_user.strip()
        self.corrective_action = corrective_action.strip()
        self.status = IssueStatus.PENDING_VERIFICATION

    def close_issue(self, closed_by_user: str) -> None:
        """Close the issue after independent verification.

        Enforces the Golden Rule:
        The resolver ('resolved_by') MUST NOT be the verifier/closer ('closed_by_user').
        """
        if not closed_by_user or not str(closed_by_user).strip():
            raise DomainRuleViolation("closed_by_user must be a non-empty identifier")

        if not self.corrective_action or not str(self.corrective_action).strip():
            raise DomainRuleViolation("Cannot close issue without a recorded corrective action")

        resolvers = {
            u.strip()
            for u in (self.resolved_by, self.responsible)
            if u and str(u).strip()
        }
        if closed_by_user.strip() in resolvers:
            raise DomainRuleViolation("Auto-vérification refusée.")

        self.closed_by = closed_by_user.strip()
        self.status = IssueStatus.CLOSED

    def reopen_issue(self, reopened_by: str, reason: str) -> None:
        """Reopen a rejected issue back to IN_PROGRESS for rework."""
        if not reopened_by or not str(reopened_by).strip():
            raise DomainRuleViolation("reopened_by must be a non-empty user identifier")
        if not reason or not str(reason).strip():
            raise DomainRuleViolation("Reopening an issue requires an explicit reason")

        self.update_critical_field("status", IssueStatus.IN_PROGRESS, reopened_by, reason)
        self.closed_by = None
