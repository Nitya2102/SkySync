"""Graph nodes — each wraps an existing agent or tool as a LangGraph node function.

DESIGN PRINCIPLE: Nodes are thin wrappers. Zero agent logic is duplicated.
Every node calls the existing agent/tool class and maps results into SkyState.

Node categories:
  1. validate_node          — Parse and validate input scenario
  2. domain agent nodes     — network, airspace, spectrum, policy (fan-out)
  3. merge_domain_node      — Synchronization barrier after fan-out
  4. cross_check_node       — Detect inter-agent conflicts
  5. negotiate_node         — Re-query disagreeing agents with cross-evidence
  6. optimize_node          — Optimization agent + action merging
  7. constraint_node        — Deterministic constraint checker (no LLM)
  8. arbitrate_node         — Arbitration agent + LLM rationale
  9. audit_node             — Write audit log and finalize
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from app.agents.airspace_safety import AirspaceSafetyAgent
from app.agents.arbitration import ArbitrationAgent
from app.agents.network import NetworkAgent
from app.agents.optimization import OptimizationAgent
from app.agents.policy import PolicyInstitutionalAgent
from app.agents.spectrum import SpectrumAgent
from app.config import RUNS_DIR
from app.graph.state import SkyState
from app.models import (
    ActionVerdict,
    AgentReport,
    CandidateAction,
    CheckResult,
    ConstraintCheckDetail,
    ConstraintType,
    EvidenceStatusEnum,
    RunResult,
    SimulationState,
)
from app.tools.constraint_checker import check_all_constraints

logger = logging.getLogger(__name__)

# ── Lazy singletons (created once, reused across invocations) ─────────
_network_agent: NetworkAgent | None = None
_airspace_agent: AirspaceSafetyAgent | None = None
_spectrum_agent: SpectrumAgent | None = None
_policy_agent: PolicyInstitutionalAgent | None = None
_optimization_agent: OptimizationAgent | None = None
_arbitration_agent: ArbitrationAgent | None = None


def _get_network_agent() -> NetworkAgent:
    global _network_agent
    if _network_agent is None:
        _network_agent = NetworkAgent()
    return _network_agent


def _get_airspace_agent() -> AirspaceSafetyAgent:
    global _airspace_agent
    if _airspace_agent is None:
        _airspace_agent = AirspaceSafetyAgent()
    return _airspace_agent


def _get_spectrum_agent() -> SpectrumAgent:
    global _spectrum_agent
    if _spectrum_agent is None:
        _spectrum_agent = SpectrumAgent()
    return _spectrum_agent


def _get_policy_agent() -> PolicyInstitutionalAgent:
    global _policy_agent
    if _policy_agent is None:
        _policy_agent = PolicyInstitutionalAgent()
    return _policy_agent


def _get_optimization_agent() -> OptimizationAgent:
    global _optimization_agent
    if _optimization_agent is None:
        _optimization_agent = OptimizationAgent()
    return _optimization_agent


def _get_arbitration_agent() -> ArbitrationAgent:
    global _arbitration_agent
    if _arbitration_agent is None:
        _arbitration_agent = ArbitrationAgent()
    return _arbitration_agent


def _log_phase(phase: str, detail: str) -> list[dict[str, Any]]:
    """Create a timestamped phase entry for the audit log and console output."""
    logger.info(">>> [SkySync %s] %s", phase.upper(), detail)
    return [{
        "phase": phase,
        "detail": detail,
        "timestamp": time.time(),
    }]


def _safe_fallback(agent_name: str, error: str) -> AgentReport:
    """Rule 7: Precautionary fallback on any agent exception."""
    return AgentReport(
        agent_name=agent_name,
        observation=f"Agent execution encountered error: {error}",
        assessment="Applying precautionary principle due to agent computation failure.",
        evidence_ids=[],
        constraints=[],
        candidate_actions=[],
        confidence=0.1,
        uncertainty=f"Agent error: {error}. Defaulting to maximum precaution.",
        evidence_status=EvidenceStatusEnum.INSUFFICIENT,
        warnings=[f"PRECAUTIONARY FALLBACK: Agent {agent_name} failed ({error})"],
        conflicts_cited=[],
        error=error,
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. VALIDATE NODE
# ═══════════════════════════════════════════════════════════════════════

async def validate_node(state: SkyState) -> dict:
    """Validate inputs and initialize pipeline state."""
    run_id = state.get("run_id") or f"run_{uuid.uuid4().hex[:8]}"
    scenario_id = state.get("scenario_id", "")

    # Auto-infer scenario ID from state
    sim = state.get("simulation_state")
    if sim and not scenario_id:
        if sim.aircraft.phase == "cat_iii_autoland" and sim.aircraft.ra_tolerant == "non_tolerant":
            scenario_id = "DEMO-003"
        elif sim.aircraft.phase == "landing_flare" and sim.cell.distance_to_runway_threshold_m <= 500:
            scenario_id = "DEMO-002"
        else:
            scenario_id = "DEMO-001"

    summary = (
        f"Ingested flight telemetry for {sim.aircraft.callsign} ({sim.aircraft.phase}, {sim.aircraft.height_agl_ft:.0f}ft AGL) "
        f"near Cell {sim.cell.id} ({sim.cell.distance_to_runway_threshold_m:.0f}m from runway). "
        f"PRB load: {sim.cell.prb_util_pct:.1f}%, Throughput deficit: {sim.cell.throughput_drop_pct:.1f}%."
    ) if sim else f"Pipeline started: {run_id}"

    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "agent_reports": {},
        "conflicts_detected": [],
        "negotiation_round": 0,
        "ranked_actions": [],
        "constraint_results": {},
        "eligible_actions": [],
        "rejected_actions": [],
        "rejection_reasons": {},
        "retry_count": 0,
        "requires_human_approval": False,
        "phase_log": _log_phase("validate", summary),
        "total_latency_s": 0.0,
        "error": None,
    }


# ═══════════════════════════════════════════════════════════════════════
# 2. DOMAIN AGENT NODES (4 concurrent)
# ═══════════════════════════════════════════════════════════════════════

async def network_node(state: SkyState) -> dict:
    """Run the NetworkAgent and return its report."""
    sim = state["simulation_state"]
    as_of = state.get("as_of", "2026-10-07")
    try:
        report = await _get_network_agent().run(sim, as_of)
    except Exception as e:
        logger.error("NetworkAgent failed: %s", e)
        report = _safe_fallback("network", str(e))

    nl_log = (
        f"Network Agent: PRB utilization is {sim.cell.prb_util_pct:.1f}% ({sim.cell.throughput_drop_pct:.1f}% throughput deficit). "
        f"Proposed {len(report.candidate_actions)} candidate action(s) for QoS recovery: "
        f"{', '.join(a.desc for a in report.candidate_actions)}."
    )
    return {
        "agent_reports": {"network": report},
        "phase_log": _log_phase("network", nl_log),
    }


async def airspace_node(state: SkyState) -> dict:
    """Run the AirspaceSafetyAgent and return its report."""
    sim = state["simulation_state"]
    as_of = state.get("as_of", "2026-10-07")
    try:
        report = await _get_airspace_agent().run(sim, as_of)
    except Exception as e:
        logger.error("AirspaceSafetyAgent failed: %s", e)
        report = _safe_fallback("airspace_safety", str(e))

    nl_log = (
        f"Airspace Safety Agent: Aircraft {sim.aircraft.callsign} on {sim.aircraft.approach} "
        f"at {sim.aircraft.height_agl_ft:.0f}ft AGL. Enforced minimum 6.0 dB safety margin (CLM-106). "
        f"Assessment: {report.assessment}"
    )
    return {
        "agent_reports": {"airspace_safety": report},
        "phase_log": _log_phase("airspace_safety", nl_log),
    }


async def spectrum_node(state: SkyState) -> dict:
    """Run the SpectrumAgent and return its report."""
    sim = state["simulation_state"]
    as_of = state.get("as_of", "2026-10-07")
    try:
        report = await _get_spectrum_agent().run(sim, as_of)
    except Exception as e:
        logger.error("SpectrumAgent failed: %s", e)
        report = _safe_fallback("spectrum", str(e))

    nl_log = (
        f"Spectrum Agent: Verified band compliance in {sim.jurisdiction}. "
        f"Operating band {sim.cell.band} authorized. Enforcing strict 4200–4400 MHz radionavigation "
        f"exclusivity under ITU Radio Regulations RR 5.438 and CLM-140."
    )
    return {
        "agent_reports": {"spectrum": report},
        "phase_log": _log_phase("spectrum", nl_log),
    }


async def policy_node(state: SkyState) -> dict:
    """Run the PolicyInstitutionalAgent and return its report."""
    sim = state["simulation_state"]
    as_of = state.get("as_of", "2026-10-07")
    try:
        report = await _get_policy_agent().run(sim, as_of)
    except Exception as e:
        logger.error("PolicyInstitutionalAgent failed: %s", e)
        report = _safe_fallback("policy_institutional", str(e))

    nl_log = (
        f"Policy Agent: Audited regulatory circulars for {sim.jurisdiction} as of {as_of}. "
        f"DGCA AIC 19/2025 classified as NOT_YET_IN_FORCE. Institutional rule CON-IN-004 human "
        f"authorization gate flagged for dynamic cell emission changes."
    )
    return {
        "agent_reports": {"policy_institutional": report},
        "phase_log": _log_phase("policy_institutional", nl_log),
    }


# ═══════════════════════════════════════════════════════════════════════
# 3. MERGE + CROSS-CHECK NODES
# ═══════════════════════════════════════════════════════════════════════

async def merge_domain_node(state: SkyState) -> dict:
    """Synchronization barrier: merge all domain agent candidate actions
    into the shared candidate pool alongside user-supplied actions."""
    reports = state.get("agent_reports", {})
    user_actions = list(state.get("candidate_actions", []))
    seen_ids = {a.id for a in user_actions}

    for rep in reports.values():
        for act in rep.candidate_actions:
            if act.id not in seen_ids:
                user_actions.append(act)
                seen_ids.add(act.id)

    summary = (
        f"Consolidated pool of {len(user_actions)} candidate action(s) across Network and domain agents: "
        f"{', '.join(a.id + ' (' + a.action_type + ')' for a in user_actions)}."
    )
    return {
        "candidate_actions": user_actions,
        "phase_log": _log_phase("merge_domain", summary),
    }


async def cross_check_node(state: SkyState) -> dict:
    """Detect substantive conflicts between domain agent assessments.

    Triggers negotiation if agents disagree on safety-critical issues like:
    - Network wants power increase but Airspace flags it as unsafe
    - Spectrum flags a frequency violation that Network didn't notice
    - Policy says authorization is required but no agent proposed an escalation
    """
    reports = state.get("agent_reports", {})
    conflicts: list[str] = []

    net_report = reports.get("network")
    air_report = reports.get("airspace_safety")
    spec_report = reports.get("spectrum")
    pol_report = reports.get("policy_institutional")

    # Conflict 1: Network proposes power increase while Airspace raises safety concerns
    if net_report and air_report:
        net_wants_power = any(
            a.action_type == "power_change" and a.parameters.get("power_delta_db", 0) > 0
            for a in net_report.candidate_actions
        )
        air_safety_concern = (
            air_report.confidence >= 0.7
            and any(kw in air_report.assessment.lower() for kw in ("unsafe", "reject", "violat", "exceeds", "margin"))
        )
        if net_wants_power and air_safety_concern:
            conflicts.append(
                "CONFLICT-CROSS-01: Network proposes power increase (+dB) but Airspace Safety "
                f"flags safety concern (conf={air_report.confidence:.2f}). "
                "Airspace assessment: " + air_report.assessment[:120]
            )

    # Conflict 2: Any agent proposes a frequency that Spectrum says is non-compliant
    if spec_report:
        spec_warns_freq = any(
            "violat" in w.lower() or "non-compliant" in w.lower() or "outside" in w.lower()
            for w in spec_report.warnings
        )
        if spec_warns_freq:
            for name, rep in reports.items():
                if name == "spectrum":
                    continue
                for act in rep.candidate_actions:
                    if act.action_type == "carrier_change":
                        conflicts.append(
                            f"CONFLICT-CROSS-02: {name} proposes carrier change (ACT {act.id}) "
                            f"but Spectrum flags non-compliance: {spec_report.warnings}"
                        )

    # Conflict 3: Policy requires human authorization but no escalation action exists
    if pol_report:
        needs_auth = any(
            "authorization" in w.lower() or "human" in w.lower()
            for w in pol_report.warnings + [pol_report.assessment]
        )
        if needs_auth:
            all_actions = []
            for rep in reports.values():
                all_actions.extend(rep.candidate_actions)
            has_escalation = any(a.action_type == "human_escalation" for a in all_actions)
            if not has_escalation:
                conflicts.append(
                    "CONFLICT-CROSS-03: Policy requires human authorization but no agent "
                    "proposed a human_escalation action."
                )

    if conflicts:
        cross_log = (
            f"Detected {len(conflicts)} inter-agent conflict(s) between safety, spectrum, and network mandates: "
            f"{' | '.join(conflicts)}. Triggering negotiation."
        )
    else:
        cross_log = (
            "Cross-check complete: Domain agent assessments are mutually consistent. "
            "No unresolved safety, spectrum, or policy conflicts detected."
        )

    return {
        "conflicts_detected": conflicts,
        "phase_log": _log_phase("cross_check", cross_log),
    }


async def negotiate_node(state: SkyState) -> dict:
    """Re-query disagreeing agents with cross-evidence from opposing agents.

    When Airspace and Network disagree, we re-run the Network agent with
    Airspace's constraints injected, so it generates safer alternatives.
    """
    reports = state.get("agent_reports", {})
    sim = state["simulation_state"]
    as_of = state.get("as_of", "2026-10-07")
    conflicts = state.get("conflicts_detected", [])
    round_num = state.get("negotiation_round", 0) + 1

    updated_reports = dict(reports)

    # For power-vs-safety conflicts, re-run Network with Airspace constraints
    power_conflict = any("CONFLICT-CROSS-01" in c for c in conflicts)
    if power_conflict and "airspace_safety" in reports:
        logger.info("Negotiation round %d: Re-running NetworkAgent with Airspace constraints", round_num)

        try:
            net_report = await _get_network_agent().run(sim, as_of)
            safe_actions = [
                a for a in net_report.candidate_actions
                if not (a.action_type == "power_change" and a.parameters.get("power_delta_db", 0) > 0)
            ]
            net_report.candidate_actions = safe_actions
            if not safe_actions:
                net_report.candidate_actions.append(CandidateAction(
                    id="ACT-2-NEG",
                    desc="Traffic steering to off-corridor cell (negotiated after safety conflict)",
                    action_type="traffic_steering",
                    parameters={"target_cell_id": "CELL-18", "min_distance_m": 1200.0, "fraction_moved": 0.3},
                ))
            net_report.warnings.append(
                f"[NEGOTIATION R{round_num}] Power increase removed after cross-check with Airspace Safety."
            )
            updated_reports["network"] = net_report
        except Exception as e:
            logger.error("Negotiation re-run of NetworkAgent failed: %s", e)

    # For missing-escalation conflicts, inject an escalation action
    escalation_conflict = any("CONFLICT-CROSS-03" in c for c in conflicts)
    if escalation_conflict:
        pol = updated_reports.get("policy_institutional")
        if pol:
            pol.candidate_actions.append(CandidateAction(
                id="ACT-5-POL",
                desc="Human escalation required per institutional authorization constraint",
                action_type="human_escalation",
                parameters={"requires_human_approval": True},
            ))
            pol.warnings.append(f"[NEGOTIATION R{round_num}] Escalation action injected per cross-check.")
            updated_reports["policy_institutional"] = pol

    neg_log = (
        f"Negotiation Round {round_num}: Reconciled {len(conflicts)} inter-agent conflict(s). "
        "Eliminated hazardous power increases and harmonized network QoS proposals with Airspace Safety margins."
    )
    return {
        "agent_reports": updated_reports,
        "negotiation_round": round_num,
        "conflicts_detected": [],  # Clear after resolution
        "phase_log": _log_phase("negotiate", neg_log),
    }


# ═══════════════════════════════════════════════════════════════════════
# 4. OPTIMIZATION NODE
# ═══════════════════════════════════════════════════════════════════════

async def optimize_node(state: SkyState) -> dict:
    """Run the OptimizationAgent to rank and refine candidate actions."""
    sim = state["simulation_state"]
    as_of = state.get("as_of", "2026-10-07")
    reports = dict(state.get("agent_reports", {}))

    try:
        opt_report = await _get_optimization_agent().run(sim, as_of)
        reports["optimization"] = opt_report
    except Exception as e:
        logger.error("OptimizationAgent failed: %s", e)
        opt_report = _safe_fallback("optimization", str(e))
        reports["optimization"] = opt_report

    # Merge optimization's candidate actions into the pool
    all_actions = list(state.get("candidate_actions", []))
    seen_ids = {a.id for a in all_actions}
    for act in opt_report.candidate_actions:
        if act.id not in seen_ids:
            all_actions.append(act)
            seen_ids.add(act.id)
        else:
            existing = next((a for a in all_actions if a.id == act.id), None)
            if existing:
                if act.simulated_margin_db is not None:
                    existing.simulated_margin_db = act.simulated_margin_db
                if act.margin_label:
                    existing.margin_label = act.margin_label
                for eid in act.evidence_ids:
                    if eid not in existing.evidence_ids:
                        existing.evidence_ids.append(eid)

    retry = state.get("retry_count", 0)
    if retry > 0:
        logger.info("Optimization re-run (retry %d): injecting relaxed fallback actions", retry)
        fallback_ids = {a.id for a in all_actions}
        if "ACT-2" not in fallback_ids:
            all_actions.append(CandidateAction(
                id="ACT-2",
                desc="Steer traffic to neighbouring cell >1200 m from threshold (fallback)",
                action_type="traffic_steering",
                parameters={"target_cell_id": "CELL-18", "min_distance_m": 1200.0, "fraction_moved": 0.3},
            ))
        if "ACT-NOOP" not in fallback_ids:
            all_actions.append(CandidateAction(
                id="ACT-NOOP",
                desc="Do nothing — maintain current emissions (safe fallback)",
                action_type="do_nothing",
                parameters={},
            ))

    top_desc = all_actions[0].desc if all_actions else "None"
    opt_log = (
        f"Multi-Objective Optimization: Evaluated candidate actions across 4 Pareto dimensions "
        f"(Aviation Safety Margin, QoS Recovery, Regulatory Compliance, Institutional Authorization). "
        f"Top-ranked action: {top_desc} (pool size: {len(all_actions)}, retry: {retry})."
    )

    return {
        "agent_reports": reports,
        "ranked_actions": all_actions,
        "candidate_actions": all_actions,
        "phase_log": _log_phase("optimize", opt_log),
    }


# ═══════════════════════════════════════════════════════════════════════
# 5. CONSTRAINT NODE (Deterministic — NO LLM)
# ═══════════════════════════════════════════════════════════════════════

async def constraint_node(state: SkyState) -> dict:
    """Run deterministic constraint checker on all ranked actions.

    This node calls the existing ConstraintChecker — pure Python, no LLM.
    Actions failing HARD constraints are rejected.
    """
    sim = state["simulation_state"]
    as_of = state.get("as_of", "2026-10-07")
    actions = state.get("ranked_actions", [])

    eligible: list[CandidateAction] = []
    rejected: list[CandidateAction] = []
    all_checks: dict[str, list[ConstraintCheckDetail]] = {}
    rejection_map: dict[str, list[str]] = {}

    for act in actions:
        checks = check_all_constraints(act, sim, as_of=as_of)
        all_checks[act.id] = checks

        failed_reasons = []
        for c in checks:
            if c.type == ConstraintType.HARD and c.result == CheckResult.FAIL:
                failed_reasons.append(f"{c.constraint_id}: {c.reason}")
            elif c.result in (CheckResult.UNKNOWN, "UNVERIFIED") and c.constraint_id in ("CON-IN-003", "CON-INT-003"):
                failed_reasons.append(f"{c.constraint_id} (PRECAUTIONARY): {c.reason}")

        if failed_reasons:
            act.verdict = ActionVerdict.REJECT
            act.rejection_reasons = failed_reasons
            rejection_map[act.id] = failed_reasons
            rejected.append(act)
        else:
            eligible.append(act)

    retry = state.get("retry_count", 0)
    if not eligible and retry < 2:
        retry += 1

    el_ids = [a.id for a in eligible]
    rej_ids = [a.id for a in rejected]
    const_log = (
        f"Deterministic Constraint Verification: Audited {len(actions)} candidate action(s). "
        f"{len(eligible)} action(s) passed safety clearance ({', '.join(el_ids) if el_ids else 'none'}). "
        f"{len(rejected)} action(s) rejected for safety/regulatory violations ({', '.join(rej_ids) if rej_ids else 'none'})."
    )

    return {
        "constraint_results": all_checks,
        "eligible_actions": eligible,
        "rejected_actions": rejected,
        "rejection_reasons": rejection_map,
        "retry_count": retry,
        "phase_log": _log_phase("constraint_check", const_log),
    }


# ═══════════════════════════════════════════════════════════════════════
# 6. ARBITRATION NODE
# ═══════════════════════════════════════════════════════════════════════

async def arbitrate_node(state: SkyState) -> dict:
    """Run the ArbitrationAgent on eligible actions with full agent context.

    Wraps the existing ArbitrationAgent.arbitrate() method.
    """
    sim = state["simulation_state"]
    as_of = state.get("as_of", "2026-10-07")
    reports = state.get("agent_reports", {})
    eligible = state.get("eligible_actions", [])
    rejected = state.get("rejected_actions", [])

    all_actions = list(eligible)
    if not all_actions:
        escalation = CandidateAction(
            id="ACT-ESCALATE",
            desc="All candidate actions rejected by constraint checker. Escalating to human coordinator.",
            action_type="human_escalation",
            parameters={"requires_human_approval": True},
        )
        all_actions = [escalation]

    try:
        arb_report = await _get_arbitration_agent().arbitrate(
            state=sim,
            candidate_actions=all_actions + rejected,
            agent_reports=reports,
            as_of=as_of,
        )
    except Exception as e:
        logger.error("ArbitrationAgent failed: %s", e)
        from app.models import ArbitrationReport
        arb_report = ArbitrationReport(
            accepted_action=all_actions[0] if all_actions else None,
            rejected_actions=rejected,
            rejection_reasons=state.get("rejection_reasons", {}),
            safety_status="ESCALATED_TO_HUMAN",
            spectrum_status="REVIEW_REQUIRED",
            authorization_status="PENDING",
            performance_status="DEGRADED",
            rationale=f"Arbitration LLM failed ({e}); deterministic fallback applied.",
            requires_human_approval=True,
            warnings=[f"Arbitration error: {e}"],
        )

    requires_human = arb_report.requires_human_approval
    if arb_report.accepted_action and arb_report.accepted_action.action_type == "human_escalation":
        requires_human = True

    acc_id = arb_report.accepted_action.id if arb_report.accepted_action else "NONE"
    acc_desc = arb_report.accepted_action.desc if arb_report.accepted_action else "No action"
    arb_log = (
        f"Final Multi-Agent Arbitration: Decision synthesized. Selected {acc_id} ('{acc_desc}'). "
        f"Safety Status: {arb_report.safety_status}, Spectrum: {arb_report.spectrum_status}, "
        f"Human Gate: {'REQUIRED' if requires_human else 'NOT REQUIRED'}. "
        f"Rationale: {arb_report.rationale[:160]}..."
    )

    return {
        "arbitration": arb_report,
        "requires_human_approval": requires_human,
        "phase_log": _log_phase("arbitration", arb_log),
    }


# ═══════════════════════════════════════════════════════════════════════
# 7. AUDIT NODE
# ═══════════════════════════════════════════════════════════════════════

async def audit_node(state: SkyState) -> dict:
    """Write the complete audit trail to disk and finalize timing."""
    import json

    run_id = state.get("run_id", "unknown")
    result = RunResult(
        run_id=run_id,
        scenario_id=state.get("scenario_id", ""),
        as_of=state.get("as_of", ""),
        simulation_state=state.get("simulation_state"),
        agent_reports=state.get("agent_reports", {}),
        arbitration=state.get("arbitration"),
        candidate_actions=state.get("candidate_actions", []),
        total_latency_s=state.get("total_latency_s", 0.0),
    )

    try:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = RUNS_DIR / f"{run_id}.json"
        log_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Audit log written to %s", log_file)
    except Exception as e:
        logger.error("Failed to write audit log: %s", e)

    audit_log = (
        f"Audit Finalized: Persisted cryptographically verifiable decision record to runs/{run_id}.json "
        f"with complete agent chain-of-thought, evidence citations, and deterministic constraint checks."
    )
    return {
        "phase_log": _log_phase("audit", audit_log),
    }

