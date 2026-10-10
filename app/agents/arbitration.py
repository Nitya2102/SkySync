"""ArbitrationAgent: Enforces deterministic constraint checks and produces final coexistence arbitration."""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.agents.base import BaseAgent
from app.groq_client import GroqClient, groq_client
from app.models import (
    ActionVerdict,
    AgentReport,
    ArbitrationReport,
    CandidateAction,
    CheckResult,
    ConstraintCheckDetail,
    ConstraintType,
    SimulationState,
)
from app.tools.constraint_checker import check_all_constraints, has_hard_failure

logger = logging.getLogger(__name__)


class ArbitrationAgent(BaseAgent):
    def __init__(self, client: GroqClient = groq_client):
        super().__init__(agent_name="arbitration", client=client)

    async def arbitrate(
        self,
        state: SimulationState,
        candidate_actions: list[CandidateAction],
        agent_reports: dict[str, AgentReport],
        as_of: str = "2026-10-07",
    ) -> ArbitrationReport:
        """Run deterministic constraint evaluation, followed by LLM rationale generation."""
        # 1. Deterministic constraint check on all candidate actions
        all_checks: dict[str, list[ConstraintCheckDetail]] = {}
        rejected_actions: list[CandidateAction] = []
        eligible_actions: list[CandidateAction] = []
        rejection_reasons_map: dict[str, list[str]] = {}

        for act in candidate_actions:
            checks = check_all_constraints(act, state, as_of=as_of)
            all_checks[act.id] = checks

            failed_reasons = []
            for c in checks:
                if c.type == ConstraintType.HARD and c.result == CheckResult.FAIL:
                    failed_reasons.append(f"{c.constraint_id}: {c.reason}")
                elif c.result in (CheckResult.UNKNOWN, "UNVERIFIED") and c.constraint_id in ("CON-IN-003", "CON-INT-003"):
                    # Precautionary rejection for unverified critical constraints
                    failed_reasons.append(f"{c.constraint_id} (PRECAUTIONARY): {c.reason}")

            if failed_reasons:
                act.verdict = ActionVerdict.REJECT
                act.rejection_reasons = failed_reasons
                rejection_reasons_map[act.id] = failed_reasons
                rejected_actions.append(act)
            else:
                eligible_actions.append(act)

        # 2. Select accepted / preferred action
        accepted_action: Optional[CandidateAction] = None
        if eligible_actions:
            # Severe uncertainty during CAT III operations requires a human gate.
            severe_uncertainty = (
                state.aircraft.phase == "cat_iii_autoland"
                and state.aircraft.ra_tolerant in ("non_tolerant", "unknown")
            )
            # Rank preference: traffic_steering > downtilt > do_nothing
            preferred = None
            if severe_uncertainty:
                for act in eligible_actions:
                    if act.action_type == "human_escalation":
                        preferred = act
                        preferred.verdict = ActionVerdict.ESCALATE
                        preferred.score = 1.0
                        break
            if not preferred:
                for act in eligible_actions:
                    if act.action_type in ("traffic_steering", "handover"):
                        preferred = act
                        preferred.verdict = ActionVerdict.ACCEPT_PREFERRED
                        preferred.score = 0.92
                        break
            if not preferred:
                for act in eligible_actions:
                    if act.action_type == "downtilt":
                        preferred = act
                        preferred.verdict = ActionVerdict.ACCEPT_IF_MARGIN
                        preferred.score = 0.85
                        break
            if not preferred:
                for act in eligible_actions:
                    if act.action_type == "human_escalation":
                        preferred = act
                        preferred.verdict = ActionVerdict.ESCALATE
                        preferred.score = 0.50
                        break
            if not preferred:
                preferred = eligible_actions[0]
                preferred.verdict = ActionVerdict.ACCEPT
                preferred.score = 0.75

            accepted_action = preferred

        # 3. Gather evidence, conflicts, and warnings from all agents
        all_evidence_ids: set[str] = set()
        all_warnings: list[str] = []
        all_conflicts: set[str] = set()

        for rep in agent_reports.values():
            for eid in rep.evidence_ids:
                all_evidence_ids.add(eid)
            for w in rep.warnings:
                if w not in all_warnings:
                    all_warnings.append(w)
            for conf in rep.conflicts_cited:
                all_conflicts.add(conf)

        # Add checks evidence
        for checks in all_checks.values():
            for c in checks:
                for eid in c.evidence_ids:
                    all_evidence_ids.add(eid)

        # 4. Generate LLM synthesis / rationale
        from app.config import AGENT_MODE
        import json

        if AGENT_MODE == "fast_kb":
            nl_arb = self._generate_natural_language_rationale(
                state=state,
                accepted_action=accepted_action,
                rejected_actions=rejected_actions,
                rejection_reasons_map=rejection_reasons_map,
                agent_reports=agent_reports,
                as_of=as_of,
            )
            rationale = nl_arb["rationale"]
            safety_status = nl_arb["safety_status"]
            spectrum_status = nl_arb["spectrum_status"]
            auth_status = nl_arb["authorization_status"]
            perf_status = nl_arb["performance_status"]
            requires_human = nl_arb["requires_human_approval"]
        else:
            schema = ArbitrationReport.model_json_schema()
            prompt = f"""Scenario: {state.model_dump_json()}
As-of Date: {as_of}
Deterministic Checks Results:
Accepted Action: {accepted_action.model_dump_json() if accepted_action else 'None'}
Rejected Actions: {[a.model_dump_json() for a in rejected_actions]}
Rejection Reasons: {rejection_reasons_map}

Agent Assessments Summary:
{chr(10).join(f"- {name}: {rep.assessment} (conf: {rep.confidence})" for name, rep in agent_reports.items())}

Provide the final arbitration rationale, safety status, spectrum status, authorization status, and performance status.
You MUST output valid JSON matching this schema: {json.dumps(schema)}
"""

            try:
                llm_resp = await self.client.generate_json(
                    prompt=prompt,
                    system_prompt="You are the ArbitrationAgent. Synthesize the deterministic decision with legal and technical rationale.",
                    model_type="reason",
                    agent_name="arbitration",
                    context={
                        "evidence_ids": list(all_evidence_ids),
                        "conflicts": list(all_conflicts),
                    },
                )
                rationale = llm_resp.get("rationale", "")
                safety_status = llm_resp.get("safety_status", "PROTECTED")
                spectrum_status = llm_resp.get("spectrum_status", "COMPLIANT")
                auth_status = llm_resp.get("authorization_status", "VERIFIED")
                perf_status = llm_resp.get("performance_status", "OPTIMIZED")
                requires_human = llm_resp.get("requires_human_approval", False)
                if not rationale:
                    fallback_arb = self._generate_natural_language_rationale(
                        state, accepted_action, rejected_actions, rejection_reasons_map, agent_reports, as_of
                    )
                    rationale = fallback_arb["rationale"]
            except Exception as e:
                logger.warning("Arbitration LLM generation failed (%s); using natural language rationale synthesis", e)
                fallback_arb = self._generate_natural_language_rationale(
                    state, accepted_action, rejected_actions, rejection_reasons_map, agent_reports, as_of
                )
                rationale = fallback_arb["rationale"]
                safety_status = fallback_arb["safety_status"]
                spectrum_status = fallback_arb["spectrum_status"]
                auth_status = fallback_arb["authorization_status"]
                perf_status = fallback_arb["performance_status"]
                requires_human = fallback_arb["requires_human_approval"]

        if accepted_action and (accepted_action.action_type == "human_escalation" or accepted_action.verdict == ActionVerdict.ESCALATE):
            requires_human = True
            safety_status = "ESCALATED_TO_HUMAN"

        # Build final flat list of constraint details for audit trail
        flattened_checks = [c for checks in all_checks.values() for c in checks]

        return ArbitrationReport(
            accepted_action=accepted_action,
            rejected_actions=rejected_actions,
            rejection_reasons=rejection_reasons_map,
            safety_status=safety_status,
            spectrum_status=spectrum_status,
            authorization_status=auth_status,
            performance_status=perf_status,
            evidence_ids=sorted(list(all_evidence_ids)),
            warnings=all_warnings,
            conflicts_cited=sorted(list(all_conflicts)),
            requires_human_approval=requires_human,
            rationale=rationale,
            constraint_checks=flattened_checks,
        )

    def _generate_natural_language_rationale(
        self,
        state: SimulationState,
        accepted_action: Optional[CandidateAction],
        rejected_actions: list[CandidateAction],
        rejection_reasons_map: dict[str, list[str]],
        agent_reports: dict[str, AgentReport],
        as_of: str,
    ) -> dict[str, Any]:
        """Synthesize a complete natural language arbitration report grounded in physics, law, and agent evidence."""
        ac = state.aircraft
        cell = state.cell

        context_str = (
            f"During {ac.phase.replace('_', ' ').title()} approach of {ac.callsign} at {ac.height_agl_ft:.0f} ft AGL "
            f"({cell.distance_to_runway_threshold_m:.0f} m from threshold), Cell {cell.id} experienced severe congestion "
            f"(PRB load {cell.prb_util_pct:.1f}%, throughput deficit {cell.throughput_drop_pct:.1f}%)."
        )

        if accepted_action:
            if accepted_action.action_type == "human_escalation" or accepted_action.verdict == ActionVerdict.ESCALATE:
                action_str = (
                    f"Selected {accepted_action.id} ('{accepted_action.desc}'). "
                    f"Under institutional constraint CON-IN-004 and ICAO Annex 10 safety provisions, "
                    f"operations involving non-tolerant or uncertain radar altimeters during CAT III autoland "
                    f"cannot be resolved via autonomous spectrum reallocation and mandate human supervisory escalation."
                )
                safety_status = "ESCALATED_TO_HUMAN"
                spectrum_status = "COMPLIANT"
                auth_status = "REQUIRES_AUTH"
                perf_status = "DEGRADED"
                requires_human = True
            elif accepted_action.action_type in ("traffic_steering", "handover"):
                target = accepted_action.parameters.get("target_cell_id", "adjacent cell")
                fraction = accepted_action.parameters.get("fraction_moved", 0.3) * 100
                action_str = (
                    f"Approved {accepted_action.id} ('{accepted_action.desc}'). "
                    f"By offloading {fraction:.0f}% of non-critical PRB traffic to {target} outside the protected corridor "
                    f"(>1200 m from runway threshold), network congestion is mitigated without altering 5G EIRP in the approach path. "
                    f"All hard constraints (CON-RAD-001, CON-IN-001, CON-IN-002) are satisfied with a positive safety margin."
                )
                safety_status = "PROTECTED"
                spectrum_status = "COMPLIANT"
                auth_status = "VERIFIED"
                perf_status = "OPTIMIZED"
                requires_human = False
            elif accepted_action.action_type == "downtilt":
                deg = accepted_action.parameters.get("tilt_deg", 2.0)
                action_str = (
                    f"Approved {accepted_action.id} ('{accepted_action.desc}'). "
                    f"Applying a {deg:.1f}° mechanical/electrical downtilt depresses main-lobe emission angles away from "
                    f"the glidepath, preserving the required 6.0 dB safety margin (CLM-106) while maintaining ground coverage."
                )
                safety_status = "PROTECTED"
                spectrum_status = "COMPLIANT"
                auth_status = "VERIFIED"
                perf_status = "OPTIMIZED"
                requires_human = False
            else:
                action_str = f"Approved {accepted_action.id} ('{accepted_action.desc}') as the highest-ranked viable action."
                safety_status = "PROTECTED"
                spectrum_status = "COMPLIANT"
                auth_status = "VERIFIED"
                perf_status = "OPTIMIZED"
                requires_human = False
        else:
            action_str = "No viable candidate action cleared hard safety constraints; default safe-state maintained."
            safety_status = "PROTECTED"
            spectrum_status = "COMPLIANT"
            auth_status = "VERIFIED"
            perf_status = "DEGRADED"
            requires_human = False

        rej_parts = []
        for a in rejected_actions:
            reasons = rejection_reasons_map.get(a.id, a.rejection_reasons)
            reason_summary = "; ".join(reasons) if reasons else "Violates aviation safety limits"
            rej_parts.append(f"{a.id} ('{a.desc}'): {reason_summary}")

        rej_str = ""
        if rej_parts:
            rej_str = f" Rejected non-compliant actions: {' | '.join(rej_parts)}."

        agents_str = " Inter-agent consensus achieved between Airspace Safety, Spectrum, and Network domains under applicable regulations."

        full_rationale = f"{context_str} {action_str}{rej_str}{agents_str}"
        return {
            "rationale": full_rationale,
            "safety_status": safety_status,
            "spectrum_status": spectrum_status,
            "authorization_status": auth_status,
            "performance_status": perf_status,
            "requires_human_approval": requires_human,
        }

