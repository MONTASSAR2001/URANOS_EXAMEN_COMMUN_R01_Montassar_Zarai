"""Deterministic URANOS project controls; the Frappe adapter owns persistence.

Actor identities, authorization flags and permission scopes MUST come from the
authenticated server session. None of these functions confers authorization.
Quantities remain Decimal until the API's explicit serialization boundary.
"""

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


class RuleViolation(ValueError):
    """An operational invariant was violated."""


def identifier(value, field):
    if not isinstance(value, str) or not value.strip() or value != value.strip() or value.strip() == "A COMPLETER":
        raise RuleViolation(f"{field}: a non-empty identifier is required")
    return value.strip()


def number(value, field, *, minimum=Decimal(0), maximum=Decimal("1e18")):
    """Reject booleans, nonfinite values and unreasonable numeric payloads."""
    if isinstance(value, bool) or value is None:
        raise RuleViolation(f"{field}: a finite decimal is required")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise RuleViolation(f"{field}: a finite decimal is required") from exc
    if not result.is_finite() or result < minimum or result > maximum:
        raise RuleViolation(f"{field}: value outside allowed range")
    if result.as_tuple().exponent < -12:
        raise RuleViolation(f"{field}: at most 12 fractional decimal places")
    return result


def calendar_date(value, field):
    if isinstance(value, datetime):
        raise RuleViolation(f"{field}: date required, not timestamp")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise RuleViolation(f"{field}: ISO calendar date required") from exc


def check_scope(project, permitted_projects):
    project = identifier(project, "project")
    if isinstance(permitted_projects, str) or project not in permitted_projects:
        raise RuleViolation("project: actor is outside the permitted project scope")
    return project


def same_project(record, project):
    if identifier(record.get("project"), "project") != project:
        raise RuleViolation("cross-project relationship is forbidden")


def evidence_present(value):
    """Evidence means persisted attachment/reference IDs, not client booleans."""
    if not isinstance(value, (list, tuple)) or not value:
        return False
    return all(
        isinstance(item, str) and bool(item.strip())
        or isinstance(item, Mapping) and isinstance(item.get("file"), str) and bool(item["file"].strip())
        for item in value
    )


def validate_baseline(project, version, packages):
    """Normalize a complete approved baseline; weights are percentage points."""
    project = identifier(project, "project")
    version = identifier(version, "baseline_version")
    if not packages:
        raise RuleViolation("baseline requires work packages")
    result = []
    names = set()
    for package in packages:
        same_project(package, project)
        name = identifier(package.get("name"), "work_package.name")
        if name in names:
            raise RuleViolation("duplicate work package in baseline")
        names.add(name)
        if identifier(package.get("baseline_version"), "baseline_version") != version:
            raise RuleViolation("baseline contains mixed versions")
        quantity = number(package.get("qty_planned"), "qty_planned")
        if quantity <= 0:
            raise RuleViolation("qty_planned must be positive; use explicit milestones for milestone work")
        weight = number(package.get("weight"), "weight", maximum=Decimal(100))
        if package.get("baseline_start") and package.get("baseline_finish"):
            if calendar_date(package["baseline_start"], "baseline_start") > calendar_date(package["baseline_finish"], "baseline_finish"):
                raise RuleViolation("baseline_finish precedes baseline_start")
        result.append(dict(package, name=name, qty_planned=quantity, weight=weight))
    if sum((item["weight"] for item in result), Decimal(0)) != 100:
        raise RuleViolation("approved baseline weights must total exactly 100 percentage points")
    return {"project": project, "version": version, "packages": result}


PROGRESS_TRANSITIONS = {
    "Draft": {"Draft", "Reported", "Pending Verification", "Cancelled"},
    "Reported": {"Reported", "Pending Verification", "Cancelled"},
    "Pending Verification": {"Pending Verification", "Verified", "Rejected", "Rejected/Rework", "Cancelled"},
    "Verified": set(),
    "Rejected": set(),
    "Rejected/Rework": set(),
    "Cancelled": set(),
}


def _progress_shape(entry, project):
    same_project(entry, project)
    if entry.get("kit_issue") and entry.get("cable_reel"):
        raise RuleViolation("one contribution cannot consume both kit and reel allocations")
    for field in ("name", "work_package", "baseline_version", "reported_by"):
        identifier(entry.get(field), field)
    status = entry.get("status")
    if status not in PROGRESS_TRANSITIONS:
        raise RuleViolation("invalid progress status")
    reported = number(entry.get("qty_reported"), "qty_reported")
    verified = number(entry.get("qty_verified", 0), "qty_verified")
    if verified > reported:
        raise RuleViolation("qty_verified cannot exceed qty_reported")
    if status == "Verified":
        verifier = identifier(entry.get("verifier"), "verifier")
        if verifier == entry["reported_by"]:
            raise RuleViolation("a reporter cannot verify their own progress")
        if not evidence_present(entry.get("evidence")):
            raise RuleViolation("verified progress requires persisted evidence")
    elif verified or entry.get("verifier"):
        raise RuleViolation("unverified progress cannot carry verified quantity or verifier")
    if entry.get("correction_of"):
        identifier(entry.get("revision_reason"), "revision_reason")
        if entry["correction_of"] == entry["name"]:
            raise RuleViolation("progress cannot correct itself")
    return dict(entry, qty_reported=reported, qty_verified=verified)


def validate_progress_entry(entry, actor, permitted_projects, *, can_verify=False, previous=None, correction=None):
    """Validate a creation/transition, including immutable verified work.

    A correction is a NEW entry whose verified quantity replaces the entire
    previous contribution, never a negative delta. The server must lock the
    correction target and enforce one verified successor transactionally.
    """
    actor = identifier(actor, "actor")
    project = check_scope(entry.get("project"), permitted_projects)
    result = _progress_shape(entry, project)
    status = result["status"]
    if previous is None:
        if status not in {"Draft", "Reported", "Pending Verification"}:
            raise RuleViolation("new progress must first be reported for independent verification")
        if entry["reported_by"] != actor:
            raise RuleViolation("reported_by must be the authenticated actor")
    else:
        _progress_shape(previous, project)
        for field in ("name", "project", "work_package", "baseline_version", "reported_by", "correction_of"):
            if entry.get(field) != previous.get(field):
                raise RuleViolation(f"{field} cannot change during a progress transition")
        if status not in PROGRESS_TRANSITIONS[previous["status"]]:
            raise RuleViolation("invalid progress transition; verified records require a new correction")
        if previous["status"] != "Draft" and result["qty_reported"] != number(previous["qty_reported"], "qty_reported"):
            raise RuleViolation("reported quantity is immutable after submission")
        if previous["status"] != "Draft":
            for field in ("activity", "zone", "crew", "posting_date", "revision_reason", "kit_issue", "cable_reel"):
                if entry.get(field) != previous.get(field):
                    raise RuleViolation(f"reported {field} is immutable after submission")
            if any(item not in entry.get("evidence", ()) for item in previous.get("evidence", ())):
                raise RuleViolation("submitted progress evidence cannot be removed")
        if status != "Verified" and actor != previous["reported_by"] and can_verify is not True:
            raise RuleViolation("only reporter or authorized controller may transition this entry")
    if status == "Verified":
        if can_verify is not True or result.get("verifier") != actor:
            raise RuleViolation("only an authorized authenticated verifier can verify progress")
    if entry.get("correction_of"):
        if correction is None or correction.get("name") != entry["correction_of"]:
            raise RuleViolation("correction target must be loaded from the system of record")
        _progress_shape(correction, project)
        if correction["status"] != "Verified":
            raise RuleViolation("only verified progress can be corrected")
        for field in ("work_package", "activity", "zone", "baseline_version", "kit_issue", "cable_reel"):
            if entry.get(field) != correction.get(field):
                raise RuleViolation(f"correction must retain original {field}")
    return result


def baseline_aliases(current_baseline, historical_packages):
    """Stable code+UOM identity across immutable baseline-specific WP records.

    The adapter supplies only packages belonging to approved/superseded
    baselines. No guessed code conversion, unit conversion or stored-row edits.
    """
    project = current_baseline["project"]
    current = {}
    for row in current_baseline["packages"]:
        code = identifier(row.get("code"), "work_package.code")
        if code in current:
            raise RuleViolation("duplicate stable work package code")
        current[code] = row
    aliases = {}
    for old in historical_packages:
        same_project(old, project)
        target = current.get(old.get("code"))
        if target is None:
            continue  # aggregation fails if a contribution references this removed scope
        if identifier(old.get("uom"), "historical uom") != identifier(target.get("uom"), "current uom"):
            raise RuleViolation("work package UOM cannot change across approved revisions")
        source = identifier(old.get("name"), "historical work package")
        if source in aliases and aliases[source] != target["name"]:
            raise RuleViolation("ambiguous historical work package mapping")
        aliases[source] = target["name"]
    return aliases


def aggregate_progress(project, baseline, entries, *, approved_versions=None, work_package_aliases=None):
    """Calculate verified-only progress with immutable replacement chains.

    Older approved baseline versions may contribute quantities to the current
    approved baseline if explicitly listed in approved_versions. They cannot
    silently alter its planned quantities or weights.
    """
    project = identifier(project, "project")
    same_project(baseline, project)
    baseline = validate_baseline(project, baseline["version"], baseline["packages"])
    versions = {baseline["version"]} if approved_versions is None else set(approved_versions)
    if baseline["version"] not in versions:
        raise RuleViolation("current baseline version is not approved")
    packages = {item["name"]: item for item in baseline["packages"]}
    aliases = {name: name for name in packages}
    for source, target in (work_package_aliases or {}).items():
        if target not in packages or (source in packages and source != target):
            raise RuleViolation("invalid current-baseline work package mapping")
        aliases[source] = target
    records = {}
    for original in entries:
        entry = _progress_shape(original, project)
        if entry["name"] in records:
            raise RuleViolation("duplicate progress identity")
        if entry["work_package"] not in aliases:
            raise RuleViolation("progress references a work package outside the current baseline")
        if entry["baseline_version"] not in versions:
            raise RuleViolation("progress references an unapproved baseline version")
        records[entry["name"]] = entry
    superseded = set()
    successors = {}
    for entry in records.values():
        target = entry.get("correction_of")
        if not target:
            continue
        if target not in records:
            raise RuleViolation("correction target missing from complete progress history")
        original = records[target]
        if original["status"] != "Verified":
            raise RuleViolation("correction target is not verified")
        for field in ("work_package", "activity", "zone", "baseline_version", "kit_issue", "cable_reel"):
            if entry.get(field) != original.get(field):
                raise RuleViolation(f"correction changed {field}")
        if entry["status"] == "Verified":
            if target in successors:
                raise RuleViolation("forked correction chain would double count verified progress")
            successors[target] = entry["name"]
            superseded.add(target)
    for name in records:
        seen = set()
        current = name
        while current:
            if current in seen:
                raise RuleViolation("cyclic progress correction chain")
            seen.add(current)
            current = records[current].get("correction_of")
    verified = {name: Decimal(0) for name in packages}
    reported = {name: Decimal(0) for name in packages}
    correction_count = 0
    for name, entry in records.items():
        if name in superseded or entry["status"] in {"Draft", "Cancelled", "Rejected", "Rejected/Rework"}:
            continue
        # A pending correction must not inflate either existing reported or verified totals.
        if entry.get("correction_of") and entry["status"] != "Verified":
            continue
        work_package = aliases[entry["work_package"]]
        reported[work_package] += entry["qty_reported"]
        if entry["status"] == "Verified":
            verified[work_package] += entry["qty_verified"]
            correction_count += bool(entry.get("correction_of"))
    rows = []
    for name, package in packages.items():
        fraction = min(verified[name] / package["qty_planned"], Decimal(1))
        rows.append({
            "work_package": name, "qty_planned": package["qty_planned"],
            "qty_reported": reported[name], "qty_verified": verified[name],
            "weight": package["weight"], "completion_percent": fraction * 100,
            "weighted_progress": fraction * package["weight"],
            "overrun_qty": max(verified[name] - package["qty_planned"], Decimal(0)),
        })
    return {"project": project, "baseline_version": baseline["version"], "physical_progress": sum((row["weighted_progress"] for row in rows), Decimal(0)), "work_packages": rows, "effective_corrections": correction_count}


GATE_CONDITIONS = {
    0: ("project_identity", "site_location", "capacity", "client", "responsible_people", "scope", "approved_baseline", "warehouses", "work_package_template", "equipment_list"),
    1: ("layout_approved", "sld_approved", "material_lists_approved", "revision_control"),
    2: ("requirements_approved", "purchase_orders_released"),
    3: ("shipments_registered", "transport_documents", "eta_reviewed"),
    4: ("site_warehouse", "responsible_people", "access_ready", "safety_ready", "resources_ready"),
    5: ("civil_scope_verified",),
    6: ("piling_scope_verified", "piling_inspections_passed"),
    7: ("structures_verified", "alignment_torque_passed"),
    8: ("modules_verified", "module_inspections_passed"),
    9: ("dc_scope_verified", "polarity_insulation_passed"),
    10: ("inverters_installed_verified", "connections_verified", "precommissioning_passed"),
    11: ("trenches_verified", "cables_verified", "pre_backfill_inspections_passed"),
    12: ("station_scope_verified", "mv_scope_verified", "earthing_tests_passed"),
    13: ("communications_verified", "scada_ppc_tests_passed", "weather_integration_verified"),
    14: ("commissioning_tests_passed", "commissioning_documents_complete", "punchlist_resolved"),
    15: ("as_built_complete", "equipment_dossiers_complete", "certificates_complete", "residual_stock_reconciled", "handover_accepted"),
}


def evaluate_stage_gate(project, gate, conditions, *, completed_gates=(), prerequisite_gates=(), required_ifc_codes=(), documents=(), holds=(), ncrs=(), approvals=(), required_approvals=0):
    """Return an actionable checklist; conditions are server-derived evidence.

    Gates can run in parallel. Only Gate 0 is universally required; project
    specific dependencies must be explicitly supplied from approved configuration.
    """
    from .quality import current_ifc, blocking_quality_items

    project = identifier(project, "project")
    if type(gate) is not int or gate not in GATE_CONDITIONS:
        raise RuleViolation("unknown stage gate")
    if type(required_approvals) is not int or not 0 <= required_approvals <= 10:
        raise RuleViolation("invalid required approval count")
    required = set(prerequisite_gates)
    if gate > 0:
        required.add(0)
    if gate in required or any(type(value) is not int or value not in GATE_CONDITIONS for value in required):
        raise RuleViolation("invalid gate prerequisite")
    missing = [key for key in GATE_CONDITIONS[gate] if conditions.get(key) is not True]
    missing.extend(f"gate:{value}" for value in sorted(required - set(completed_gates)))
    if gate == 1 and not required_ifc_codes:
        missing.append("required_ifc_configuration")
    for code in required_ifc_codes:
        if current_ifc(project, code, documents) is None:
            missing.append(f"ifc:{code}")
    missing.extend(blocking_quality_items(project, holds, ncrs))
    approved_by = set()
    for approval in approvals:
        same_project(approval, project)
        if approval.get("gate") != gate or approval.get("status") != "Approved":
            continue
        actor = identifier(approval.get("approved_by"), "approved_by")
        if actor == identifier(approval.get("requested_by"), "requested_by"):
            raise RuleViolation("gate request cannot be self-approved")
        approved_by.add(actor)
    if len(approved_by) < required_approvals:
        missing.append("independent_approvals")
    return {"project": project, "gate": gate, "ready": not missing, "missing": missing}


def dashboard_summary(project, progress, *, planned_percent=None, material_readiness_percent=None, blockers=(), ncrs=(), stock_variances=(), today, finance=None, finance_allowed=False):
    """Produce an allowlisted dashboard; operational and financial views differ."""
    project = identifier(project, "project")
    same_project(progress, project)
    actual = number(progress.get("physical_progress"), "physical_progress", maximum=Decimal(100))
    today = calendar_date(today, "today")
    planned = None if planned_percent is None else number(planned_percent, "planned_percent", maximum=Decimal(100))
    material = None if material_readiness_percent is None else number(material_readiness_percent, "material_readiness_percent", maximum=Decimal(100))
    risks = []
    for kind, items in (("blocker", blockers), ("ncr", ncrs)):
        for item in items:
            same_project(item, project)
            name = identifier(item.get("name"), "name")
            severity = item.get("severity")
            if severity not in {"Low", "Medium", "High", "Critical"}:
                raise RuleViolation("unknown risk severity")
            if kind == "ncr":
                from .quality import NCR_TRANSITIONS
                if item.get("status") not in NCR_TRANSITIONS:
                    raise RuleViolation("invalid NCR status")
            elif item.get("status") not in {"Open", "Assigned", "In Progress", "Escalated", "Resolved", "Closed", "Cancelled"}:
                raise RuleViolation("invalid blocker status")
            if item.get("status") in {"Closed", "Resolved", "Cancelled"}:
                continue
            due = calendar_date(item["due_date"], "due_date") if item.get("due_date") else None
            overdue = due is not None and due < today
            urgent = severity == "Critical" or (kind == "ncr" and severity == "High" and overdue)
            risks.append({"code": f"{kind}_open", "source_type": kind, "source_name": name, "severity": "Red" if urgent else "Amber", "overdue": overdue})
    for variance in stock_variances:
        same_project(variance, project)
        amount = number(variance.get("variance"), "variance", minimum=Decimal("-1e18"))
        if amount and variance.get("risk_class") in {"R3", "R4"} and variance.get("status") != "Resolved":
            risks.append({"code": "high_risk_stock_variance", "source_type": "stock_variance", "source_name": identifier(variance.get("name"), "name"), "severity": "Red"})
    if planned is not None and actual < planned:
        risks.append({"code": "behind_baseline", "severity": "Amber"})
    if material is not None and material < 100:
        risks.append({"code": "material_shortfall", "severity": "Amber"})
    missing = [name for name, value in (("planned_percent", planned), ("material_readiness_percent", material)) if value is None]
    status = "Red" if any(item["severity"] == "Red" for item in risks) else "Amber" if risks else "Unknown" if missing else "Green"
    result = {"project": project, "physical_progress": actual, "planned_progress": planned, "progress_delta": None if planned is None else actual - planned, "material_readiness": material, "status": status, "risks": risks, "missing_data": missing}
    if finance_allowed is True:
        result["finance"] = None
        if finance is not None:
            same_project(finance, project)
            summary = {"currency": identifier(finance.get("currency"), "currency")}
            for field in ("budget", "committed", "received", "invoiced", "paid", "forecast"):
                summary[field] = None if finance.get(field) is None else number(finance[field], field)
            summary["budget_remaining"] = None if summary["budget"] is None or summary["committed"] is None else summary["budget"] - summary["committed"]
            summary["forecast_variance"] = None if summary["forecast"] is None or summary["budget"] is None else summary["forecast"] - summary["budget"]
            result["finance"] = summary
    return result


def validate_delegated_approval(delegation, *, actor, project, action, on_date, amount, currency, requested_by):
    """Evaluate a server-loaded, independently approved, non-transitive mandate."""
    actor = identifier(actor, "actor")
    project = identifier(project, "project")
    same_project(delegation, project)
    if delegation.get("status") != "Approved":
        raise RuleViolation("delegation must be approved")
    delegator = identifier(delegation.get("delegator"), "delegator")
    if actor != delegation.get("delegate") or actor in {delegator, requested_by}:
        raise RuleViolation("invalid delegate or self-approval")
    if delegation.get("parent_delegation"):
        raise RuleViolation("transitive delegation is not permitted")
    start = calendar_date(delegation.get("valid_from"), "valid_from")
    finish = calendar_date(delegation.get("valid_to"), "valid_to")
    if start > finish or not start <= calendar_date(on_date, "on_date") <= finish:
        raise RuleViolation("delegation is outside its validity window")
    if action not in delegation.get("actions", ()):
        raise RuleViolation("action is outside delegated scope")
    if identifier(currency, "currency") != identifier(delegation.get("currency"), "delegation.currency"):
        raise RuleViolation("delegation currency differs; implicit exchange is forbidden")
    if number(amount, "amount") > number(delegation.get("amount_limit"), "amount_limit"):
        raise RuleViolation("delegation transaction limit exceeded")
    return True


CHANGE_TRANSITIONS = {
    "Proposed": {"Impact Analysis", "Rejected"},
    "Impact Analysis": {"Technical Approval", "Rejected"},
    "Technical Approval": {"Financial Approval", "Approved", "Rejected"},
    "Financial Approval": {"Approved", "Rejected"},
    "Approved": {"Implemented"},
    "Implemented": {"Verified"},
    "Verified": {"Closed"},
    "Rejected": set(),
    "Closed": set(),
}


def validate_change_transition(change, actor, permitted_projects, *, previous=None, can_approve_technical=False, can_approve_financial=False):
    """Record technical/financial authority without inventing production limits.

    financial_approval_required must be a policy-derived bool; any nonzero cost
    impact additionally requires financial approval. The server verifies role,
    financial threshold and delegation before setting authorization flags.
    """
    actor = identifier(actor, "actor")
    project = check_scope(change.get("project"), permitted_projects)
    for field in ("name", "requested_by", "description", "reason"):
        identifier(change.get(field), field)
    status = change.get("status")
    if status not in CHANGE_TRANSITIONS:
        raise RuleViolation("invalid change status")
    if previous is None:
        if status != "Proposed" or change["requested_by"] != actor:
            raise RuleViolation("change must begin as an attributable proposal")
    else:
        same_project(previous, project)
        for field in ("name", "requested_by"):
            if change[field] != previous.get(field):
                raise RuleViolation("change identity and requester are immutable")
        if previous.get("status") not in CHANGE_TRANSITIONS or status not in CHANGE_TRANSITIONS[previous["status"]]:
            raise RuleViolation("invalid change transition")
        if previous["status"] in {"Technical Approval", "Financial Approval", "Approved", "Implemented", "Verified"}:
            for field in ("description", "reason", "cost_impact", "schedule_impact_days", "material_impact", "document_impact", "financial_approval_required", "affected_records"):
                if change.get(field) != previous.get(field):
                    raise RuleViolation("approved change impacts are immutable; create a new proposal")
            if change.get("technical_approver") != previous.get("technical_approver"):
                raise RuleViolation("technical approval identity is immutable")
        if previous["status"] in {"Financial Approval", "Approved", "Implemented", "Verified"}:
            if change.get("financial_approver") != previous.get("financial_approver"):
                raise RuleViolation("financial approval identity is immutable")
        if previous["status"] in {"Implemented", "Verified"} and change.get("implemented_by") != previous.get("implemented_by"):
            raise RuleViolation("implementation identity is immutable")
    if status not in {"Proposed", "Impact Analysis", "Rejected"}:
        cost = number(change.get("cost_impact"), "cost_impact", minimum=Decimal("-1e18"))
        number(change.get("schedule_impact_days"), "schedule_impact_days", minimum=Decimal("-1e18"))
        identifier(change.get("material_impact"), "material_impact")
        identifier(change.get("document_impact"), "document_impact")
        if type(change.get("financial_approval_required")) is not bool:
            raise RuleViolation("financial approval policy must be explicitly configured")
        records = change.get("affected_records")
        if not isinstance(records, (list, tuple)):
            raise RuleViolation("change propagation requires an explicit affected-record list")
        for record in records:
            same_project(record, project)
            identifier(record.get("name"), "affected record name")
            if record.get("type") not in {"BOM", "Kit", "Document", "Baseline", "Purchase Order", "Stock", "Task", "Test Procedure", "Work Package"}:
                raise RuleViolation("unsupported change propagation record type")
        technical = identifier(change.get("technical_approver"), "technical_approver")
        if technical == change["requested_by"]:
            raise RuleViolation("technical change cannot be self-approved")
        if status == "Technical Approval" and (can_approve_technical is not True or technical != actor):
            raise RuleViolation("technical approval requires authorized authenticated approver")
        financial_required = bool(cost) or change["financial_approval_required"]
        if status in {"Financial Approval", "Approved", "Implemented", "Verified", "Closed"} and financial_required:
            financial = identifier(change.get("financial_approver"), "financial_approver")
            if financial in {change["requested_by"], technical}:
                raise RuleViolation("financial approval requires a distinct independent approver")
            if status == "Approved" and previous["status"] != "Financial Approval":
                raise RuleViolation("cost/policy change must pass financial approval before release")
        if status == "Financial Approval" and (can_approve_financial is not True or change.get("financial_approver") != actor):
            raise RuleViolation("financial approval requires authorized authenticated approver")
        if status == "Approved" and not (can_approve_technical is True or can_approve_financial is True):
            raise RuleViolation("change release requires an authorized approver")
    if status == "Implemented" and change.get("implemented_by") != actor:
        raise RuleViolation("change implementation must be attributable")
    if status in {"Verified", "Closed"}:
        if not evidence_present(change.get("verification_evidence")):
            raise RuleViolation("change verification requires evidence")
        if change.get("verified_by") == change.get("implemented_by"):
            raise RuleViolation("change implementation cannot be self-verified")
        identifier(change.get("implemented_by"), "implemented_by")
        identifier(change.get("verified_by"), "verified_by")
        if status == "Verified" and (can_approve_technical is not True or change["verified_by"] != actor):
            raise RuleViolation("change verification requires independent technical authority")
    return dict(change)


def portfolio_kpi_summary(projects, profiles, blockers, *, daily_yield_hours=Decimal("4.8"), co2_factor_per_mwh=Decimal("0.7")):
    """Pure domain calculation for portfolio KPI metrics.

    Zero-IO, deterministic, Decimal-only arithmetic.
    """
    total_sites = len(projects)
    active_sites = sum(1 for p in projects if p.get("status") in {"Open", "In Progress"})

    total_capacity_mw = sum(
        (number(p.get("capacity_ac_mw") or 0, "capacity_ac_mw") for p in profiles),
        Decimal(0),
    )
    total_capacity_dc_mwp = sum(
        (number(p.get("capacity_dc_mwp") or 0, "capacity_dc_mwp") for p in profiles),
        Decimal(0),
    )

    total_lost_hours = sum(
        (number(b.get("lost_hours") or 0, "lost_hours") for b in blockers),
        Decimal(0),
    )

    active_blockers = [
        b for b in blockers
        if b.get("status") in {"Open", "Assigned", "In Progress", "Pending Verification", "Escalated"}
    ]

    operational_rate = (
        round((Decimal(active_sites) / Decimal(total_sites)) * Decimal(100), 1)
        if total_sites > 0
        else Decimal(0)
    )

    energy_today_mwh = round(total_capacity_mw * daily_yield_hours, 2)
    co2_avoided_t = round(energy_today_mwh * co2_factor_per_mwh, 2)

    return {
        "total_sites": total_sites,
        "active_sites": active_sites,
        "operational_rate_percent": operational_rate,
        "total_capacity_mw": total_capacity_mw,
        "total_capacity_dc_mwp": total_capacity_dc_mwp,
        "lost_hours": total_lost_hours,
        "active_blockers_count": len(active_blockers),
        "total_blockers_count": len(blockers),
        "energy_today_mwh": energy_today_mwh,
        "co2_avoided_t": co2_avoided_t,
    }


def read_verified_progress_window(
    project_id,
    baseline_dict,
    entries_list,
    start_date,
    end_date=None,
    *,
    permitted_projects=None,
    approved_versions=None,
):
    """Read independently verified installed quantities over an explicit 7-calendar-day window.

    Strict Hexagonal Domain function (Pure Python, Decimal-only, Zero-IO).
    Complies with JALON_ENTRETIEN.md (Points 2, 3, 4):
    - Strictly excludes Draft, Reported, and Pending Verification entries.
    - Excludes non-progress documents (receipts, stock issues, movements).
    - Resolves correction chains without double-counting (superseded verified records replaced).
    - Strictly validates 7-calendar-day period boundaries (rejects entries outside [start_date, end_date]).
    - Keeps distinct units (UOMs) completely separated (never adds meters to pieces).
    - Does NOT convert physical quantities into labour hours or financial amounts.
    - Explicitly reports absent progress as unknown (None), while genuine verified zero is reported as 0.
    - Rejects unauthorized or cross-project access.
    """
    from datetime import timedelta

    if permitted_projects is not None:
        check_scope(project_id, permitted_projects)
    project = identifier(project_id, "project")

    # Date parsing and window validation
    if isinstance(start_date, str):
        try:
            start_dt = date.fromisoformat(start_date[:10])
        except (ValueError, TypeError):
            raise RuleViolation("invalid start_date format, expected YYYY-MM-DD")
    elif isinstance(start_date, (date, datetime)):
        start_dt = start_date if isinstance(start_date, date) else start_date.date()
    else:
        raise RuleViolation("start_date is required and must be date or ISO string")

    if end_date is None:
        end_dt = start_dt + timedelta(days=6)
    elif isinstance(end_date, str):
        try:
            end_dt = date.fromisoformat(end_date[:10])
        except (ValueError, TypeError):
            raise RuleViolation("invalid end_date format, expected YYYY-MM-DD")
    elif isinstance(end_date, (date, datetime)):
        end_dt = end_date if isinstance(end_date, date) else end_date.date()
    else:
        raise RuleViolation("end_date must be date or ISO string")

    if start_dt > end_dt:
        raise RuleViolation("start_date cannot be after end_date")

    calendar_days = (end_dt - start_dt).days + 1
    if calendar_days != 7:
        raise RuleViolation(f"period window must be exactly 7 calendar days, got {calendar_days}")

    period_info = {
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
        "calendar_days": 7,
    }

    # Baseline validation and missing data flagging
    if (
        not baseline_dict
        or not isinstance(baseline_dict, dict)
        or not baseline_dict.get("packages")
    ):
        return {
            "project": project,
            "baseline_version": None,
            "period": period_info,
            "work_packages": [],
            "units_summary": {},
            "effective_corrections": 0,
            "missing_data": ["approved_baseline"],
            "status": "Unknown",
        }

    same_project(baseline_dict, project)
    validated_baseline = validate_baseline(
        project, baseline_dict.get("version"), baseline_dict["packages"]
    )
    versions = {validated_baseline["version"]} if approved_versions is None else set(approved_versions)
    if validated_baseline["version"] not in versions:
        raise RuleViolation("current baseline version is not approved")

    packages = {item["name"]: item for item in validated_baseline["packages"]}

    # Non-progress doctypes to ignore
    EXCLUDED_DOCTYPES = frozenset({
        "Purchase Receipt",
        "Stock Entry",
        "Purchase Order",
        "Stock Ledger Entry",
        "Item",
        "Material Request",
    })

    # Filter progress entries
    valid_entries = {}
    for raw in entries_list or []:
        if not isinstance(raw, dict):
            continue
        # Exclude non-progress documents (receipts, stock issues)
        if raw.get("doctype") in EXCLUDED_DOCTYPES:
            continue
        if "stock_issued" in raw and "qty_verified" not in raw and "work_package" not in raw:
            continue
        if "receipt_qty" in raw and "work_package" not in raw:
            continue

        # If work_package not provided, not a field progress entry
        if not raw.get("work_package"):
            continue

        # Cross-project enforcement
        if raw.get("project") and raw["project"] != project:
            raise RuleViolation(f"cross-project entry rejected: {raw.get('project')} != {project}")

        # Shape validation
        entry = _progress_shape(raw, project)
        if entry["name"] in valid_entries:
            raise RuleViolation("duplicate progress entry identity")
        if entry["work_package"] not in packages:
            raise RuleViolation("progress references a work package outside the baseline")
        if entry["baseline_version"] not in versions:
            raise RuleViolation("progress references an unapproved baseline version")

        valid_entries[entry["name"]] = entry

    # Resolve correction chains
    superseded = set()
    successors = {}
    for entry in valid_entries.values():
        target = entry.get("correction_of")
        if not target:
            continue
        if target not in valid_entries:
            raise RuleViolation("correction target missing from complete progress history")
        original = valid_entries[target]
        if original["status"] != "Verified":
            raise RuleViolation("correction target is not verified")
        for field in ("work_package", "activity", "zone", "baseline_version"):
            if entry.get(field) != original.get(field):
                raise RuleViolation(f"correction changed {field}")
        if entry["status"] == "Verified":
            if target in successors:
                raise RuleViolation("forked correction chain would double count verified progress")
            successors[target] = entry["name"]
            superseded.add(target)

    # Cycle detection
    for name in valid_entries:
        seen = set()
        curr = name
        while curr:
            if curr in seen:
                raise RuleViolation("cyclic progress correction chain")
            seen.add(curr)
            curr = valid_entries[curr].get("correction_of")

    # Accumulate quantities strictly within the 7-day calendar window
    verified_by_wp = {wp: Decimal(0) for wp in packages}
    measured_wp = {wp: False for wp in packages}
    effective_corrections = 0

    for name, entry in valid_entries.items():
        # Exclude superseded, draft, unverified, rejected
        if name in superseded or entry["status"] != "Verified":
            continue

        # Posting date check for the 7-day window
        raw_p_date = entry.get("posting_date") or entry.get("date")
        if not raw_p_date:
            continue
        if isinstance(raw_p_date, str):
            try:
                p_dt = date.fromisoformat(str(raw_p_date)[:10])
            except (ValueError, TypeError):
                continue
        elif isinstance(raw_p_date, (date, datetime)):
            p_dt = raw_p_date if isinstance(raw_p_date, date) else raw_p_date.date()
        else:
            continue

        # Strictly check window boundaries [start_dt, end_dt]
        if start_dt <= p_dt <= end_dt:
            wp = entry["work_package"]
            verified_by_wp[wp] += entry["qty_verified"]
            measured_wp[wp] = True
            if entry.get("correction_of"):
                effective_corrections += 1

    # Format result rows with explicit separation of UOM and absent data
    wp_rows = []
    units_summary = {}

    for name, pkg in packages.items():
        uom = pkg.get("uom", "units")
        has_measurement = measured_wp[name]
        qty_verified = verified_by_wp[name] if has_measurement else None

        if has_measurement:
            units_summary[uom] = units_summary.get(uom, Decimal(0)) + verified_by_wp[name]

        wp_rows.append({
            "work_package": name,
            "code": pkg.get("code", name),
            "title": pkg.get("title", name),
            "uom": uom,
            "qty_planned": pkg["qty_planned"],
            "qty_verified": qty_verified,  # None if genuinely absent (unknown)
            "is_measured": has_measurement,
        })

    return {
        "project": project,
        "baseline_version": validated_baseline["version"],
        "period": period_info,
        "work_packages": wp_rows,
        "units_summary": units_summary,
        "effective_corrections": effective_corrections,
        "missing_data": [],
        "status": "OK",
    }

