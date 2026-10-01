from copy import deepcopy

import pytest

from uranos_project_os.domain.controls import RuleViolation, aggregate_progress, baseline_aliases, validate_baseline


def scenario():
    current = validate_baseline("P1", "B2", [{"project": "P1", "name": "NEW-WP", "code": "MODULES",
        "uom": "Nos", "baseline_version": "B2", "qty_planned": 200, "weight": 100}])
    history = [{"project": "P1", "name": "OLD-WP", "code": "MODULES", "uom": "Nos"}]
    entry = {"project": "P1", "name": "E1", "work_package": "OLD-WP", "baseline_version": "B1",
        "reported_by": "team", "verifier": "controller", "qty_reported": 100, "qty_verified": 60,
        "status": "Verified", "evidence": ["FILE1"]}
    return current, history, entry


def test_revision_preserves_historical_progress_without_editing_record():
    current, history, entry = scenario()
    original = deepcopy(entry)
    result = aggregate_progress("P1", current, [entry], approved_versions=["B1", "B2"],
        work_package_aliases=baseline_aliases(current, history))
    assert result["physical_progress"] == 30
    assert entry == original
    assert result["work_packages"][0]["work_package"] == "NEW-WP"


def test_revision_correction_replaces_old_contribution_once():
    current, history, entry = scenario()
    correction = dict(entry, name="E2", qty_verified=50, correction_of="E1", revision_reason="QA recount")
    result = aggregate_progress("P1", current, [entry, correction], approved_versions=["B1", "B2"],
        work_package_aliases=baseline_aliases(current, history))
    assert result["physical_progress"] == 25


@pytest.mark.parametrize("changes", [{"uom": "m"}, {"project": "P2"}])
def test_historical_uom_or_project_conversion_forbidden(changes):
    current, history, _ = scenario()
    history[0].update(changes)
    with pytest.raises(RuleViolation):
        baseline_aliases(current, history)


def test_dual_material_allocation_cannot_double_consume_work():
    current, history, entry = scenario()
    entry.update(kit_issue="KIT", cable_reel="REEL")
    with pytest.raises(RuleViolation):
        aggregate_progress("P1", current, [entry], approved_versions=["B1", "B2"],
            work_package_aliases=baseline_aliases(current, history))
