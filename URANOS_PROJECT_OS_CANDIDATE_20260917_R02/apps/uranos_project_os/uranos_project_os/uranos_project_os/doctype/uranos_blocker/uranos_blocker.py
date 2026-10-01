"""URANOS Blocker controller enforcing strict 4-step workflow, RBAC, and Separation of Duties."""
from __future__ import annotations

import frappe
from uranos_project_os.controllers import UranosDocument
from uranos_project_os.security import is_engineer, is_site_team

STATUS_NORM = {
    "open": "Open",
    "ouvert": "Open",
    "in progress": "In Progress",
    "en cours": "In Progress",
    "pending verification": "Pending Verification",
    "à vérifier": "Pending Verification",
    "a verifier": "Pending Verification",
    "closed": "Closed",
    "clôturé": "Closed",
    "cloture": "Closed",
}


def normalize_status(val: str | None) -> str:
    if not val:
        return "Open"
    clean = str(val).strip().lower()
    return STATUS_NORM.get(clean, str(val))


class URANOSBlocker(UranosDocument):
    def validate(self):
        self.status = normalize_status(self.status)
        self._sync_alias_fields()
        self._enforce_workflow_and_closure()
        super().validate()

    def _sync_alias_fields(self):
        # Keep corrective_action and resolution in sync
        if self.get("corrective_action"):
            self.resolution = self.corrective_action
        elif self.get("resolution"):
            self.corrective_action = self.resolution

        # Keep due_date and target_resolution in sync
        if self.get("due_date"):
            self.target_resolution = self.due_date
        elif self.get("target_resolution"):
            try:
                self.due_date = str(self.target_resolution)[:10]
            except Exception:
                pass

    def _enforce_workflow_and_closure(self):
        old = self.get_doc_before_save()
        old_status = normalize_status(old.status) if old else None
        new_status = normalize_status(self.status)

        current_user = frappe.session.user

        # 1. New document check: Initial status must be Open
        if not old:
            if new_status in ("Closed", "Pending Verification"):
                frappe.throw(
                    "Un nouvel obstacle doit être créé avec le statut 'Ouvert'.",
                    frappe.ValidationError,
                )
            return

        # If status didn't change, no transition validation needed
        if old_status == new_status:
            return

        # 2. Strict 4-step workflow: Ouvert -> En cours -> À vérifier -> Clôturé
        # Valid forward transitions:
        # Open -> In Progress
        # In Progress -> Pending Verification
        # Pending Verification -> Closed
        # Reopening transition:
        # Pending Verification -> In Progress
        valid_transitions = {
            "Open": {"In Progress"},
            "In Progress": {"Pending Verification"},
            "Pending Verification": {"Closed", "In Progress"},
            "Closed": set(),  # Closed tickets are immutable
        }

        allowed_next = valid_transitions.get(old_status, set())
        if new_status not in allowed_next:
            frappe.throw(
                f"Transition de statut invalide ('{old_status}' → '{new_status}'). "
                f"Le flux strict est : Ouvert → En cours → À vérifier → Clôturé.",
                frappe.ValidationError,
            )

        # 3. Transition to Pending Verification (À vérifier)
        if new_status == "Pending Verification":
            action = self.get("corrective_action") or self.get("resolution")
            if not action or not str(action).strip():
                frappe.throw(
                    "Une action corrective est requise pour soumettre à vérification.",
                    frappe.ValidationError,
                )
            if not self.get("resolved_by"):
                self.resolved_by = current_user
            if not self.get("resolution_submitted_at"):
                self.resolution_submitted_at = frappe.utils.now()

        # 4. Transition to Closed (Clôturé)
        if new_status == "Closed":
            # RBAC check: Équipe chantier (site_team) cannot close
            if is_site_team(current_user) and not (is_engineer(current_user) or current_user == "Administrator"):
                frappe.throw(
                    "L'équipe chantier n'est pas autorisée à clôturer un obstacle.",
                    frappe.PermissionError,
                )

            # Rule a: A corrective_action text field is filled
            action = self.get("corrective_action") or self.get("resolution")
            if not action or not str(action).strip():
                frappe.throw(
                    "Action corrective obligatoire pour clôturer l'obstacle.",
                    frappe.ValidationError,
                )

            # Rule b: Separation of Duties (Golden Rule)
            # The user performing the closure (frappe.session.user) MUST BE DIFFERENT
            # from the user who executed/resolved the issue (resolved_by or assigned responsible).
            resolvers = {
                u.strip()
                for u in (self.get("resolved_by"), self.get("responsible"))
                if u and str(u).strip()
            }
            if current_user in resolvers:
                frappe.throw("Auto-vérification refusée.", frappe.ValidationError)

            self.closed_by = current_user
            self.closed_at = frappe.utils.now()
            self.resolved_at = self.resolved_at or frappe.utils.now()
