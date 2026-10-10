"""Constraint checker – deterministic, never calls an LLM.

ConstraintChecker(constraint, action, state, as_of) -> pass/fail/unknown + reason
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from app.config import KB_DIR
from app.models import (
    CandidateAction,
    CheckResult,
    ConstraintCheckDetail,
    ConstraintType,
    SimulationState,
)

logger = logging.getLogger(__name__)


def _load_constraints() -> list[dict]:
    p = KB_DIR / "constraints.json"
    return json.loads(p.read_text())["constraints"]


def _parse_date(s: Optional[str]) -> Optional[date]:
    """Best-effort date parsing from various formats in the KB."""
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except (ValueError, IndexError):
            continue
    return None


def temporal_status(legal_status: str, effective_from: Optional[str], as_of: str) -> str:
    """Determine temporal status of a constraint or claim against as_of date.

    Returns one of: in_force, NOT_YET_IN_FORCE, voluntary_non_binding,
    inference, evidence_gap, analysis_parameter, or the original status.
    """
    as_of_date = _parse_date(as_of)

    # Check explicit legal_status keywords first
    lower = (legal_status or "").lower()
    if "not_yet" in lower:
        return "NOT_YET_IN_FORCE"
    if "voluntary" in lower:
        return "VOLUNTARY_NON_BINDING"
    if "inference" in lower:
        return "INFERENCE"
    if "evidence_gap" in lower:
        return "EVIDENCE_GAP"
    if "analysis" in lower:
        return "ANALYSIS_PARAMETER"

    # Check effective_from date vs as_of
    eff = _parse_date(effective_from)
    if eff and as_of_date and eff > as_of_date:
        return "NOT_YET_IN_FORCE"

    # Check for future indicators in legal_status
    if "future" in lower:
        return "NOT_YET_IN_FORCE"
    if "published" in lower and "effective" in lower:
        # e.g. "published_effective_2027-12-31" – parse the embedded date
        for part in lower.replace("_", " ").split():
            d = _parse_date(part)
            if d and as_of_date and d > as_of_date:
                return "NOT_YET_IN_FORCE"

    if "adopted" in lower and "pending" in lower:
        return "ADOPTED_PENDING"

    if "in_force" in lower:
        return "IN_FORCE"

    return legal_status or "UNKNOWN"


def check_constraint(
    constraint: dict,
    action: CandidateAction,
    state: SimulationState,
    as_of: str = "2026-10-07",
) -> ConstraintCheckDetail:
    """Check a single constraint against an action + state.

    Returns a ConstraintCheckDetail with pass/fail/unknown.
    """
    cid = constraint["constraint_id"]
    ctype = ConstraintType(constraint["type"])
    legal = constraint.get("legal_status", "")
    eff = constraint.get("effective_from")
    params = constraint.get("parameters", {})
    rule = constraint.get("rule", "")
    evidence_ids = constraint.get("evidence_claims", [])

    t_status = temporal_status(legal, eff, as_of)

    # ── CON-INT-001: RA band exclusivity ───────────────────────────
    if cid == "CON-INT-001":
        forbidden = params.get("forbidden_band_mhz", [4200, 4400])
        # Check if any carrier or action frequency is in the forbidden band
        action_freq = action.parameters.get("carrier_mhz") or action.parameters.get("frequency_mhz")
        if action_freq:
            freq = float(action_freq)
            if forbidden[0] <= freq <= forbidden[1]:
                return ConstraintCheckDetail(
                    constraint_id=cid, title=constraint["title"], type=ctype,
                    result=CheckResult.FAIL,
                    reason=f"Carrier/action at {freq} MHz is inside RA band {forbidden}",
                    evidence_ids=evidence_ids, legal_status=legal,
                    effective_from=eff, as_of_status=t_status,
                )
        # Check n77 upper edge proximity
        if action.action_type == "carrier_change":
            freq = action.parameters.get("carrier_mhz", action.parameters.get("frequency_mhz"))
            if freq and float(freq) >= forbidden[0]:
                return ConstraintCheckDetail(
                    constraint_id=cid, title=constraint["title"], type=ctype,
                    result=CheckResult.FAIL,
                    reason=f"Carrier at {freq} MHz is inside or abuts RA band {forbidden}",
                    evidence_ids=evidence_ids, legal_status=legal,
                    effective_from=eff, as_of_status=t_status,
                )

    # ── CON-INT-003: Minimum safety margin ─────────────────────────
    if cid == "CON-INT-003":
        min_margin = params.get("min_margin_db", 6)
        if action.action_type in ("traffic_steering", "handover", "human_escalation", "do_nothing"):
            return ConstraintCheckDetail(
                constraint_id=cid, title=constraint["title"], type=ctype,
                result=CheckResult.PASS,
                reason="Non-emitting mitigation action preserves existing airspace safety margin envelope",
                evidence_ids=evidence_ids, legal_status=legal,
                effective_from=eff, as_of_status=t_status,
            )
        margin = action.simulated_margin_db
        if margin is not None:
            if margin < min_margin:
                return ConstraintCheckDetail(
                    constraint_id=cid, title=constraint["title"], type=ctype,
                    result=CheckResult.FAIL,
                    reason=f"SIMULATION margin {margin:.1f} dB < required {min_margin} dB",
                    evidence_ids=evidence_ids, legal_status=legal,
                    effective_from=eff, as_of_status=t_status,
                )
            return ConstraintCheckDetail(
                constraint_id=cid, title=constraint["title"], type=ctype,
                result=CheckResult.PASS,
                reason=f"SIMULATION margin {margin:.1f} dB >= required {min_margin} dB",
                evidence_ids=evidence_ids, legal_status=legal,
                effective_from=eff, as_of_status=t_status,
            )
        # Cannot check without simulation
        return ConstraintCheckDetail(
            constraint_id=cid, title=constraint["title"], type=ctype,
            result=CheckResult.UNKNOWN,
            reason="No simulated margin available; cannot verify safety",
            evidence_ids=evidence_ids, legal_status=legal,
            effective_from=eff, as_of_status=t_status,
        )

    # ── CON-INT-004: Authorization is national ─────────────────────
    if cid == "CON-INT-004":
        if action.action_type == "carrier_change":
            freq = action.parameters.get("carrier_mhz") or action.parameters.get("frequency_mhz")
            if freq:
                freq = float(freq)
                jurisdiction = state.jurisdiction.lower()
                # India licensed: 3300-3670 MHz
                if jurisdiction == "india":
                    if freq < 3300 or freq > 3670:
                        return ConstraintCheckDetail(
                            constraint_id=cid, title=constraint["title"], type=ctype,
                            result=CheckResult.FAIL,
                            reason=f"Carrier {freq} MHz not licensed in India (3300-3670 MHz)",
                            evidence_ids=evidence_ids, legal_status=legal,
                            effective_from=eff, as_of_status=t_status,
                        )

    # ── CON-INT-002: Safety assessment required ────────────────────
    if cid == "CON-INT-002":
        # Any power increase near aviation areas needs assessment
        if action.action_type == "power_change":
            delta = action.parameters.get("power_delta_db", 0)
            if delta > 0:
                return ConstraintCheckDetail(
                    constraint_id=cid, title=constraint["title"], type=ctype,
                    result=CheckResult.FAIL,
                    reason=f"Power increase +{delta} dB near aviation area requires interference assessment (RR 4.10)",
                    evidence_ids=evidence_ids, legal_status=legal,
                    effective_from=eff, as_of_status=t_status,
                )

    # ── CON-IN-003: India airport restrictions (UNKNOWN) ───────────
    if cid == "CON-IN-003":
        if state.jurisdiction.lower() == "india":
            if action.action_type in ("power_change", "carrier_change"):
                return ConstraintCheckDetail(
                    constraint_id=cid, title=constraint["title"], type=ctype,
                    result=CheckResult.UNKNOWN,
                    reason="India airport-area 5G restrictions: no primary source with parameters (GAP-006). Precautionary default.",
                    evidence_ids=evidence_ids, legal_status=legal,
                    effective_from=eff, as_of_status=t_status,
                )

    # ── CON-IN-004: Dynamic changes need human authorization ──────
    if cid == "CON-IN-004":
        if state.jurisdiction.lower() == "india":
            if action.action_type in ("power_change", "carrier_change"):
                requires = params.get("requires_human_authorization", True)
                if requires:
                    return ConstraintCheckDetail(
                        constraint_id=cid, title=constraint["title"], type=ctype,
                        result=CheckResult.FAIL,
                        reason="Dynamic network changes that increase emissions require human authorization in India (inference from institutional claims)",
                        evidence_ids=evidence_ids, legal_status=legal,
                        effective_from=eff, as_of_status=t_status,
                    )

    # Default: PASS for constraints we don't have specific logic for
    return ConstraintCheckDetail(
        constraint_id=cid, title=constraint.get("title", ""), type=ctype,
        result=CheckResult.PASS,
        reason="No violation detected for this action",
        evidence_ids=evidence_ids, legal_status=legal,
        effective_from=eff, as_of_status=t_status,
    )


def check_all_constraints(
    action: CandidateAction,
    state: SimulationState,
    as_of: str = "2026-10-07",
    constraints: list[dict] | None = None,
) -> list[ConstraintCheckDetail]:
    """Check all constraints against a single action."""
    if constraints is None:
        constraints = _load_constraints()
    results = []
    for con in constraints:
        results.append(check_constraint(con, action, state, as_of))
    return results


def has_hard_failure(checks: list[ConstraintCheckDetail]) -> bool:
    """Return True if any HARD constraint failed."""
    return any(
        c.type == ConstraintType.HARD and c.result == CheckResult.FAIL
        for c in checks
    )


def has_unknown_hard(checks: list[ConstraintCheckDetail]) -> bool:
    """Return True if any HARD constraint is UNKNOWN (precautionary)."""
    return any(
        c.type in (ConstraintType.HARD, ConstraintType.UNKNOWN)
        and c.result == CheckResult.UNKNOWN
        for c in checks
    )
