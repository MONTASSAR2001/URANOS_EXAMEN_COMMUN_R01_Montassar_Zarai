"""IR-F03 adapter regressions; boundary stubs are NOT real DB/lock evidence."""
import importlib.util
import json
import sys
from copy import deepcopy
from unittest.mock import Mock, patch

import pytest
import uranos_project_os
from test_support_workflow_adapters import SERVICES, Row, change, load, policy


@pytest.fixture
def scenario():
    _reports, changes, frappe, security, common = load()
    security.SCOPED_FIELDS["URANOS Baseline"] = "project"
    common.actor = Mock(return_value="engineer")
    fields = {"code": "MODULES", "uom": "Nos", "qty_planned": 100, "weight": 100,
              "baseline_start": "2026-09-01", "baseline_finish": "2026-10-01"}
    wp = Row(doctype="URANOS Work Package", name="WP2", project="P", baseline_version="2",
             title="Modules", site="Site", discipline="Electrical", criticality="Normal",
             required_documents=[Row(document_code="LAYOUT", required_status="IFC", mandatory=1)], **fields)
    target = Row(doctype="URANOS Baseline", name="B2", project="P", version="2", supersedes="B1",
                 change_request="CH", revision_reason="Layout revision", owner="author", status="Draft",
                 packages=[Row(work_package="WP2", **fields)])
    previous = Row(doctype="URANOS Baseline", name="B1", project="P", version="1", status="Approved")
    doc = change(cost_impact=0, impacted_objects=[Row(reference_doctype="URANOS Baseline", reference_name="B2", impact="Revise quantities")])
    profile = Row(doctype="URANOS Project Profile", name="PROFILE", project="P", current_baseline="B1")
    docs = {("URANOS Baseline", "B1"): previous, ("URANOS Baseline", "B2"): target,
            ("URANOS Work Package", "WP2"): wp, ("URANOS Change Request", "CH"): doc,
            ("URANOS Project Profile", "PROFILE"): profile, ("Project", "P"): Row(name="P", company="CO")}
    common.scoped_doc.side_effect = lambda doctype, name, **kwargs: docs[(doctype, name)]
    frappe.db.get_value.return_value = "P"
    frappe.db.exists.return_value = False
    frappe.get_list.side_effect = lambda doctype, **kwargs: [Row(name="PROFILE")] if doctype == "URANOS Project Profile" else []
    frappe.get_doc.side_effect = lambda doctype, name: docs[(doctype, name)]
    modules = {"frappe": frappe, "uranos_project_os.security": security,
               "uranos_project_os.controllers": sys.modules.get("uranos_project_os.controllers"),
               "uranos_project_os.services.common": common, "uranos_project_os.services.changes": changes}
    # Reuse the actual private capability reference from the separately loaded
    # change adapter; never implement a fake version of its business rules.
    from types import ModuleType
    controller = ModuleType("uranos_project_os.controllers")
    controller.authorized_transition = changes.authorized_transition
    modules["uranos_project_os.controllers"] = controller
    with patch.dict(sys.modules, modules), patch.object(uranos_project_os, "security", security, create=True):
        spec = importlib.util.spec_from_file_location("uranos_project_os.services.operations", SERVICES / "operations.py")
        operations = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(operations)
        with patch.object(changes, "_locked", return_value=doc), patch.object(changes, "_policy", return_value=policy()):
            def assess():
                security.require_roles.return_value = "finance-assessor"
                changes.assess_change_cost("CH", 0, "POL")
                doc.cost_impact = 0  # persisted Currency numeric representation

            def approve():
                assess()
                security.require_roles.return_value = "engineer"
                changes.transition_change("CH", "Technical Approval")
                changes.transition_change("CH", "Approved")

            def apply():
                security.require_roles.return_value = "engineer"
                with patch.object(operations, "_locked", return_value=target):
                    return operations.approve_baseline(target.name)

            yield Row(changes=changes, operations=operations, frappe=frappe, common=common, security=security,
                      doc=doc, target=target, previous=previous, wp=wp, docs=docs, profile=profile,
                      assess=assess, approve=approve, apply=apply)


def test_assessment_captures_exact_server_scope_and_locks_sources(scenario):
    s = scenario
    s.assess()
    scope = json.loads(s.doc.scope_snapshot)
    expected = scope["baselines"][0]
    assert expected["name"] == "B2" and expected["supersedes"] == "B1" and expected["version"] == "2"
    package = expected["packages"][0]
    assert package["work_package"] == "WP2" and package["qty_planned"] == "100"
    assert package["required_documents"] == [{"document_code": "LAYOUT", "mandatory": 1, "required_status": "IFC"}]
    assert {"cost_impact", "policy", "approved_at", "status", "baseline_approved"}.isdisjoint(expected)
    for doctype, name in (("URANOS Baseline", "B2"), ("URANOS Baseline", "B1"), ("URANOS Work Package", "WP2")):
        assert any(call.args == (doctype, name) and call.kwargs.get("lock") for call in s.common.scoped_doc.call_args_list)


@pytest.mark.parametrize("doctype,name", [("Task", "TASK"), ("URANOS Work Package", "WP2")])
def test_project_approved_unrelated_impact_does_not_authorize_revision(scenario, doctype, name):
    s = scenario
    s.doc.impacted_objects = [Row(reference_doctype=doctype, reference_name=name, impact="Unrelated approved impact")]
    s.approve()
    with patch.object(s.operations, "_save") as save, pytest.raises(ValueError, match="exact target baseline"):
        s.apply()
    save.assert_not_called()
    assert s.previous.status == "Approved" and s.target.status == "Draft" and s.profile.current_baseline == "B1"


def test_b2_authority_cannot_apply_b3(scenario):
    s = scenario
    s.approve()
    s.target.name = "B3"
    with pytest.raises(ValueError, match="exact target baseline"):
        s.apply()
    assert s.previous.status == "Approved"


def test_changing_impact_target_after_assessment_invalidates_it(scenario):
    s = scenario
    s.assess()
    other = deepcopy(s.target)
    other.name = "B3"
    s.docs[("URANOS Baseline", "B3")] = other
    s.doc.impacted_objects[0].reference_name = "B3"
    with pytest.raises(ValueError, match="scope changed after assessment"):
        s.changes.transition_change("CH", "Technical Approval")


@pytest.mark.parametrize("field,value", [("qty_planned", 200), ("code", "NEW-CODE"), ("uom", "m"),
    ("baseline_start", "2026-09-02"), ("baseline_finish", "2026-11-01")])
@pytest.mark.parametrize("signed", [False, True])
def test_proposal_quantity_code_unit_or_date_change_invalidates_all_authority(scenario, field, value, signed):
    s = scenario
    (s.approve if signed else s.assess)()
    s.wp[field] = value
    s.target.packages[0][field] = value
    with pytest.raises(ValueError, match="scope changed after assessment"):
        if signed:
            s.apply()
        else:
            s.changes.transition_change("CH", "Technical Approval")
    assert s.previous.status == "Approved" and s.target.status == "Draft"


@pytest.mark.parametrize("field,value", [("document_code", "NEW-PLAN"), ("required_status", "Approved"), ("mandatory", 0)])
def test_proposed_document_requirement_change_invalidates_signed_authority(scenario, field, value):
    s = scenario
    s.approve()
    s.wp.required_documents[0][field] = value
    with pytest.raises(ValueError, match="scope changed after assessment"):
        s.apply()
    assert s.profile.current_baseline == "B1"


def test_changing_weights_while_preserving_valid_total_invalidates_scope(scenario):
    s = scenario
    extra = deepcopy(s.wp)
    extra.name, extra.code, extra.weight = "WP3", "OTHER", 40
    s.wp.weight, s.target.packages[0].weight = 60, 60
    s.docs[("URANOS Work Package", "WP3")] = extra
    s.target.packages.append(Row(work_package="WP3", **{key: extra[key] for key in
        ("code", "uom", "qty_planned", "weight", "baseline_start", "baseline_finish")}))
    s.approve()
    s.wp.weight, s.target.packages[0].weight = 50, 50
    extra.weight, s.target.packages[1].weight = 50, 50
    with pytest.raises(ValueError, match="scope changed after assessment"):
        s.apply()


@pytest.mark.parametrize("field", ["version", "supersedes"])
def test_changed_revision_identity_invalidates_authority(scenario, field):
    s = scenario
    s.approve()
    if field == "version":
        s.target.version = s.wp.baseline_version = "3"
    else:
        s.target.supersedes = "B0"
        s.docs[("URANOS Baseline", "B0")] = Row(name="B0", project="P")
    with pytest.raises(ValueError, match="scope changed after assessment"):
        s.changes.verify_baseline_authorization(s.doc, s.target)


@pytest.mark.parametrize("legacy", [None, "", '{"baselines":[]}', '{"version":0,"baselines":[]}'])
def test_legacy_approval_has_no_retroactive_authority(scenario, legacy):
    s = scenario
    s.approve()
    s.doc.scope_snapshot = legacy
    with pytest.raises(ValueError, match="snapshot"):
        s.apply()
    assert s.target.status == "Draft" and s.profile.current_baseline == "B1"


def test_nonbaseline_legacy_technical_approval_also_requires_new_assessment(scenario):
    s = scenario
    s.doc.impacted_objects = [Row(reference_doctype="Task", reference_name="TASK", impact="Schedule")]
    s.doc.scope_snapshot = None
    with pytest.raises(ValueError, match="scope snapshot"):
        s.changes.transition_change("CH", "Technical Approval")


def test_editing_baseline_row_without_wp_is_not_a_second_authoritative_quantity(scenario):
    s = scenario
    s.assess()
    s.target.packages[0].qty_planned = 500
    with pytest.raises(ValueError, match="authoritative work packages"):
        s.changes.transition_change("CH", "Technical Approval")


def test_cross_project_or_cross_change_target_rejected(scenario):
    s = scenario
    s.target.change_request = "ANOTHER-CHANGE"
    with pytest.raises(ValueError, match="name this change request"):
        s.assess()
    s.target.change_request, s.wp.project = "CH", "OTHER-PROJECT"
    with pytest.raises(ValueError, match="version/project mismatch"):
        s.assess()


def test_proposed_snapshot_is_stable_after_exact_application(scenario):
    s = scenario
    s.approve()
    digest, scope = s.doc.payload_hash, s.doc.scope_snapshot
    s.apply()
    assert s.target.status == "Approved" and s.previous.status == "Superseded"
    assert s.wp.baseline_approved == 1 and s.profile.current_baseline == "B2"
    s.wp.status, s.wp.material_ready, s.wp.modified = "In Progress", 1, "later"
    s.changes.verify_baseline_authorization(s.doc, s.target)
    assert s.doc.payload_hash == digest and s.doc.scope_snapshot == scope
    s.changes.transition_change("CH", "Implemented", "Applied the exact signed revision")
    assert s.doc.payload_hash == digest
    with pytest.raises(ValueError, match="unapproved revision"):
        s.apply()


def test_snapshot_tamper_cannot_reuse_original_signature(scenario):
    s = scenario
    s.approve()
    s.target.packages[0].qty_planned = s.wp.qty_planned = 200
    # Even a hypothetical trusted DB mutation of the snapshot cannot turn the
    # old hash into an approval for the revised content.
    s.doc.scope_snapshot = s.changes._canonical_json(s.changes._capture_scope(s.doc, s.changes._affected(s.doc)))
    with pytest.raises(ValueError, match="intact independently approved scope signature"):
        s.apply()


def test_financial_signature_does_not_follow_changed_scope(scenario):
    s = scenario
    s.approve()
    s.doc.cost_impact, s.doc.financial_approver = 5, "finance"
    s.doc.payload_hash = s.doc.cost_assessment_hash = s.changes._digest(s.doc, policy(), s.changes._affected(s.doc))
    s.frappe.get_all.return_value = [Row(policy="POL", requester=s.doc.requested_by, approver="finance",
        payload_hash="signature-for-another-snapshot", approved_roles='["URANOS Finance Controller"]')]
    with pytest.raises(ValueError, match="does not match"):
        s.apply()


def test_mutated_unsigned_draft_can_be_reassessed_but_approved_change_cannot(scenario):
    s = scenario
    s.assess()
    original = s.doc.cost_assessment_hash
    s.target.packages[0].qty_planned = s.wp.qty_planned = 200
    s.approve()
    assert s.doc.payload_hash != original
    with pytest.raises(ValueError, match="must precede technical approval"):
        s.assess()
