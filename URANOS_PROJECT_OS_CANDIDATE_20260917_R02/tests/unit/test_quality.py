import unittest
from copy import deepcopy

from uranos_project_os.domain.controls import RuleViolation
from uranos_project_os.domain.quality import (
    blocking_quality_items, current_ifc, evaluate_commissioning,
    validate_commissioning_acceptance, validate_document_transition,
    validate_hold_release, validate_ncr_transition,
)


def document(**changes):
    row = {"name": "DOC-R1", "project": "P-A", "document_code": "SLD", "revision": "1", "issuer": "engineer", "approver": "director", "file": "/private/files/sld.pdf", "status": "IFC", "is_current": True}
    row.update(changes)
    return row


def ncr(**changes):
    row = {"name": "NCR-1", "project": "P-A", "requirement": "Approved torque procedure", "defect": "Torque below procedure requirement", "responsible": "team", "reported_by": "inspector", "corrected_by": "team", "severity": "Critical", "due_date": "2026-09-20", "status": "Pending Verification", "corrective_action": "Retorqued per approved procedure", "before_evidence": ["before.jpg"], "after_evidence": ["after.jpg"]}
    row.update(changes)
    return row


def hold(**changes):
    row = {"name": "HOLD-1", "project": "P-A", "work_package": "DC", "procedure_reference": "TEST-APPROVED-1", "performed_by": "electrician", "verifier": "qa", "status": "Released", "result": "Passed", "evidence": ["inspection-record.pdf"]}
    row.update(changes)
    return row


class DocumentTests(unittest.TestCase):
    def test_current_ifc_returns_unique_current_revision(self):
        old = document(name="DOC-R0", revision="0", status="Superseded", is_current=False)
        self.assertEqual(current_ifc("P-A", "SLD", [old, document()])["name"], "DOC-R1")

    def test_superseded_not_exposed(self):
        old = document(status="Superseded", is_current=False)
        self.assertIsNone(current_ifc("P-A", "SLD", [old]))

    def test_superseded_cannot_be_marked_current(self):
        with self.assertRaises(RuleViolation):
            current_ifc("P-A", "SLD", [document(status="Superseded")])

    def test_multiple_ifc_fail_closed(self):
        with self.assertRaises(RuleViolation):
            current_ifc("P-A", "SLD", [document(), document(name="DOC-R2", revision="2")])

    def test_missing_file_or_self_approval_rejected(self):
        for changes in ({"file": ""}, {"approver": "engineer"}, {"project": "P-B"}, {"status": "Old"}):
            with self.subTest(changes=changes), self.assertRaises(RuleViolation):
                current_ifc("P-A", "SLD", [document(**changes)])

    def test_document_workflow(self):
        draft = document(status="Draft", approver=None, is_current=False)
        validate_document_transition(draft, "engineer", ["P-A"])
        review = dict(draft, status="Internal Review")
        validate_document_transition(review, "engineer", ["P-A"], previous=draft)
        approved = dict(review, status="Approved", approver="director")
        validate_document_transition(approved, "director", ["P-A"], previous=review, can_approve=True)
        issued = dict(approved, status="IFC", is_current=True)
        validate_document_transition(issued, "director", ["P-A"], previous=approved, can_approve=True)
        retired = dict(issued, status="Superseded", is_current=False)
        validate_document_transition(retired, "director", ["P-A"], previous=issued, can_approve=True)
        with self.assertRaises(RuleViolation):
            validate_document_transition(issued, "director", ["P-A"], previous=retired, can_approve=True)

    def test_approved_file_is_immutable(self):
        previous = document(status="Approved")
        with self.assertRaises(RuleViolation):
            validate_document_transition(document(file="another.pdf"), "director", ["P-A"], previous=previous, can_approve=True)

    def test_authorized_status_change_required(self):
        with self.assertRaises(RuleViolation):
            validate_document_transition(document(), "director", ["P-A"], previous=document(status="Approved"))

    def test_new_revision_cannot_replace_unrelated_document(self):
        new = document(name="NEW", revision="2", status="Draft", approver=None, supersedes="OLD")
        with self.assertRaises(RuleViolation):
            validate_document_transition(new, "engineer", ["P-A"], supersedes=document(name="OLD", document_code="LAYOUT"))


class NCRTests(unittest.TestCase):
    def test_independent_verified_closure(self):
        closed = ncr(status="Closed", closure_verifier="qa", closure_verification="Retest passes approved procedure")
        result = validate_ncr_transition(closed, "qa", ["P-A"], previous=ncr(), can_close=True)
        self.assertEqual(result["status"], "Closed")

    def test_correction_cannot_verify_itself(self):
        with self.assertRaises(RuleViolation):
            validate_ncr_transition(ncr(status="Closed", closure_verifier="team", closure_verification="OK"), "team", ["P-A"], previous=ncr(), can_close=True)

    def test_cannot_skip_to_closure(self):
        with self.assertRaises(RuleViolation):
            validate_ncr_transition(ncr(status="Closed", closure_verifier="qa", closure_verification="OK"), "qa", ["P-A"], previous=ncr(status="Open"), can_close=True)

    def test_before_after_evidence_required(self):
        for field in ("before_evidence", "after_evidence", "corrective_action"):
            candidate = ncr(status="Closed", closure_verifier="qa", closure_verification="OK")
            candidate[field] = None
            with self.subTest(field=field), self.assertRaises(RuleViolation):
                validate_ncr_transition(candidate, "qa", ["P-A"], previous=ncr(), can_close=True)

    def test_severity_cannot_be_lowered_without_qa(self):
        with self.assertRaises(RuleViolation):
            validate_ncr_transition(ncr(status="Corrective Action", severity="Low"), "team", ["P-A"], previous=ncr(status="Assigned"))

    def test_cannot_change_responsible_during_closure_to_bypass_sod(self):
        with self.assertRaises(RuleViolation):
            validate_ncr_transition(ncr(status="Closed", responsible="other", corrected_by="other", closure_verifier="team", closure_verification="OK"), "team", ["P-A"], previous=ncr(), can_close=True)

    def test_creation_attribution(self):
        validate_ncr_transition(ncr(status="Open"), "inspector", ["P-A"])
        with self.assertRaises(RuleViolation):
            validate_ncr_transition(ncr(status="Open"), "stranger", ["P-A"])

    def test_scope_and_approval_required(self):
        for scope, permission in ((["P-B"], True), (["P-A"], False)):
            with self.subTest(scope=scope, permission=permission), self.assertRaises(RuleViolation):
                validate_ncr_transition(ncr(status="Closed", closure_verifier="qa", closure_verification="OK"), "qa", scope, previous=ncr(), can_close=permission)


class HoldTests(unittest.TestCase):
    def test_independent_passed_hold(self):
        validate_hold_release(hold(), "qa", ["P-A"], can_release=True)

    def test_no_release_without_proof_or_independence(self):
        for changes in ({"result": "Failed"}, {"evidence": []}, {"procedure_reference": ""}, {"performed_by": "qa"}, {"project": "P-B"}):
            with self.subTest(changes=changes), self.assertRaises(RuleViolation):
                validate_hold_release(hold(**changes), "qa", ["P-A"], can_release=True)

    def test_quality_gates_surface_reasons(self):
        self.assertEqual(blocking_quality_items("P-A", [hold(status="Open")], [ncr()]), ["hold:HOLD-1", "ncr:NCR-1"])


class CommissioningTests(unittest.TestCase):
    def assess(self, **changes):
        args = {"required_tests": ["EARTHING"], "tests": [{"project": "P-A", "test_code": "EARTHING", "status": "Passed", "procedure_reference": "APPROVED-EARTH-TEST", "performed_by": "electrician", "verifier": "qa", "evidence": ["earth-test.pdf"]}], "required_documents": ["SLD"], "documents": [document(status="As-built")]}
        args.update(changes)
        return evaluate_commissioning("P-A", **args)

    def test_complete_dossier(self):
        self.assertTrue(self.assess()["ready"])

    def test_unconfigured_requirements_fail_closed(self):
        for changes in ({"required_tests": []}, {"required_documents": []}):
            with self.subTest(changes=changes), self.assertRaises(RuleViolation):
                self.assess(**changes)

    def test_missing_test_document_punchlist_and_critical_ncr(self):
        assessment = self.assess(tests=[], documents=[], ncrs=[ncr()], punchlist=[{"project": "P-A", "name": "PUNCH1", "status": "Open"}])
        self.assertEqual(set(assessment["missing"]), {"test:EARTHING", "as_built:SLD", "ncr:NCR-1", "punchlist:PUNCH1"})

    def test_ifc_is_not_as_built(self):
        self.assertIn("as_built:SLD", self.assess(documents=[document()])["missing"])

    def test_test_without_evidence_cannot_count(self):
        incomplete = {"project": "P-A", "test_code": "EARTHING", "status": "Passed"}
        self.assertIn("test_evidence:EARTHING", self.assess(tests=[incomplete])["missing"])

    def test_duplicate_test_results_cannot_hide_failure(self):
        test = {"project": "P-A", "test_code": "EARTHING", "status": "Passed"}
        with self.assertRaises(RuleViolation):
            self.assess(tests=[test, dict(test, status="Failed")])

    def test_acceptance_independent_and_evidenced(self):
        dossier = {"project": "P-A", "prepared_by": "engineer", "accepted_by": "director", "acceptance_evidence": ["signed-acceptance.pdf"]}
        validate_commissioning_acceptance(dossier, self.assess(), actor="director", permitted_projects=["P-A"], can_accept=True)
        for changes in ({"prepared_by": "director"}, {"acceptance_evidence": []}):
            with self.subTest(changes=changes), self.assertRaises(RuleViolation):
                validate_commissioning_acceptance(dict(dossier, **changes), self.assess(), actor="director", permitted_projects=["P-A"], can_accept=True)

    def test_incomplete_assessment_cannot_accept(self):
        dossier = {"project": "P-A", "prepared_by": "engineer", "accepted_by": "director", "acceptance_evidence": ["signed.pdf"]}
        with self.assertRaises(RuleViolation):
            validate_commissioning_acceptance(dossier, self.assess(tests=[]), actor="director", permitted_projects=["P-A"], can_accept=True)


if __name__ == "__main__":
    unittest.main()
