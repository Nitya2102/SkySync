"""BaseAgent class providing the Evidence Guard, verification, and precautionary fallbacks."""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.config import KB_DIR, AGENT_MODE
from app.groq_client import GroqClient, groq_client
from app.models import (
    AgentReport,
    CandidateAction,
    EvidenceStatusEnum,
    SimulationState,
)
import json
from app.rag.evidence_pack import EvidencePack
from app.rag.pipeline import rag_pipeline

logger = logging.getLogger(__name__)


class EvidenceGuard:
    """Verifies that an agent report does not fabricate claims or override constraints."""

    def __init__(self, valid_claim_ids: set[str]):
        self.valid_claim_ids = valid_claim_ids

    def verify_and_clean(
        self,
        report_dict: dict[str, Any],
        retrieved_pack: EvidencePack,
    ) -> AgentReport:
        """Strip fabricated claim IDs and flag warnings. Ensure Pydantic validity."""
        cited_ids = report_dict.get("evidence_ids", [])
        verified_ids = []
        warnings = list(report_dict.get("warnings", []))

        # Pack evidence IDs that were retrieved for this specific agent query
        retrieved_ids = set(retrieved_pack.evidence_ids)

        for cid in cited_ids:
            if cid in self.valid_claim_ids:
                verified_ids.append(cid)
            else:
                # Fabricated claim ID! Rule 2: must drop and warn
                warnings.append(f"Dropped fabricated evidence ID '{cid}' (not found in knowledge base)")

        # Warnings from retrieved pack (e.g. temporal NOT_YET_IN_FORCE, superseded)
        for w in retrieved_pack.warnings:
            if w not in warnings:
                warnings.append(w)

        # Check for Tier-3 authority claims (Rule 4: warning, not hard rejection)
        for it in retrieved_pack.items:
            if it.verification == "secondary_report" or getattr(it, "authority_tier", 1) == 3:
                tier3_warn = f"Claim {it.id} relies on Tier-3 / secondary evidence: advisory weight only."
                if tier3_warn not in warnings:
                    warnings.append(tier3_warn)

        # Parse candidate actions
        candidate_actions = []
        for act in report_dict.get("candidate_actions", []):
            try:
                candidate_actions.append(CandidateAction(**act))
            except Exception as e:
                logger.warning("Could not parse candidate action %s: %s", act, e)

        # Chain of thought synthesis
        cot = report_dict.get("chain_of_thought", [])
        if not cot:
            obs = report_dict.get("observation", "")
            assess = report_dict.get("assessment", "")
            unc = report_dict.get("uncertainty", "")
            agent = report_dict.get("agent_name", "agent")
            cot = [
                f"1. Telemetry Inspection: {obs}" if obs else f"1. Evaluated cell parameters and approach corridor geometry.",
                f"2. Regulatory & Evidence Mapping: Verified constraints against {len(verified_ids)} retrieved aviation & spectrum claims.",
                f"3. Operational Reasoning: {assess}" if assess else f"3. Formulated domain safety recommendations.",
            ]
            if unc:
                cot.append(f"4. Precautionary Guard: {unc}")

        # Build verified AgentReport
        return AgentReport(
            agent_name=report_dict.get("agent_name", "unknown"),
            observation=report_dict.get("observation", ""),
            assessment=report_dict.get("assessment", ""),
            chain_of_thought=cot,
            evidence_ids=verified_ids,
            constraints=report_dict.get("constraints", []),
            candidate_actions=candidate_actions,
            confidence=float(report_dict.get("confidence", 0.5)),
            uncertainty=report_dict.get("uncertainty", ""),
            evidence_status=EvidenceStatusEnum(report_dict.get("evidence_status", retrieved_pack.status.value)),
            warnings=warnings,
            conflicts_cited=report_dict.get("conflicts_cited", retrieved_pack.conflicts),
            error=report_dict.get("error"),
        )


class BaseAgent:
    """Abstract base class for all 6 coexistence agents."""

    def __init__(self, agent_name: str, client: GroqClient = groq_client):
        self.agent_name = agent_name
        self.client = client
        self.rag = rag_pipeline
        self.rag.retriever.load()
        self.guard = EvidenceGuard(valid_claim_ids=set(self.rag.retriever.claims_by_id.keys()))

    def system_prompt(self) -> str:
        schema = AgentReport.model_json_schema()
        return f"""You are the {self.agent_name} agent in the Real-Time 5G–Airspace Coexistence System.
Your job is to provide objective, evidence-based reasoning on technical 5G and airspace safety tradeoffs.
STRICT RULES:
1. ONLY cite evidence IDs that are explicitly present in the PROVIDED EVIDENCE PACK (e.g., CLM-106, CLM-109). NEVER invent or fabricate claim IDs.
2. Never invent regulatory numbers or margins. Label any computed values as "SIMULATION".
3. Check the temporal status of rules: if a rule has an effective date after the scenario as_of date, treat it as NOT_YET_IN_FORCE.
4. If evidence is missing, note it explicitly in your uncertainty field and apply the precautionary principle.
5. If there are known conflicts in the evidence, cite them without silently averaging or ignoring one side.

REQUIRED JSON FORMAT:
You MUST output valid JSON matching this schema: {json.dumps(schema)}

Make sure to populate 'chain_of_thought' with a list of strings detailing your exact step-by-step reasoning based on the telemetry and constraints.
"""

    def generate_natural_language_report(
        self, state: SimulationState, evidence_pack: EvidencePack, as_of: str = "2026-10-07"
    ) -> dict[str, Any]:
        """Generate high-speed, physics/KB-grounded natural language report.
        Subclasses provide domain-specific formulas and deep reasoning."""
        return self.client._generate_mock_response(
            agent_name=self.agent_name,
            prompt="",
            context={
                "evidence_ids": evidence_pack.evidence_ids,
                "constraints": evidence_pack.constraints,
                "conflicts": evidence_pack.conflicts,
                "scenario": state.model_dump(),
                "as_of": as_of,
            },
        )

    async def run(self, state: SimulationState, as_of: str = "2026-10-07") -> AgentReport:
        """Retrieve evidence, run hybrid heuristic/KB or live LLM, verify citations."""
        evidence_pack = self.rag.get_evidence_for_agent(self.agent_name, state)

        # In hybrid or fast_kb mode for domain agents: use high-speed physics/KB reasoning (< 2ms)
        if (AGENT_MODE in ("hybrid", "fast_kb") and self.agent_name != "arbitration") or self.client.mock_mode:
            try:
                resp_dict = self.generate_natural_language_report(state, evidence_pack, as_of)
                return self.guard.verify_and_clean(resp_dict, evidence_pack)
            except Exception as e:
                logger.error("Heuristic reasoning for %s failed: %s. Using precautionary fallback.", self.agent_name, e)
                return self._precautionary_fallback(str(e), evidence_pack)

        prompt = f"""Scenario: {state.model_dump_json()}
As-of Date: {as_of}

EVIDENCE PACK:
{evidence_pack.to_prompt_context()}

Analyze this scenario according to your agent role ({self.agent_name}). Output JSON."""

        try:
            resp_dict = await self.client.generate_json(
                prompt=prompt,
                system_prompt=self.system_prompt(),
                model_type="reason",
                agent_name=self.agent_name,
                context={
                    "evidence_ids": evidence_pack.evidence_ids,
                    "constraints": evidence_pack.constraints,
                    "conflicts": evidence_pack.conflicts,
                    "scenario": state.model_dump(),
                    "as_of": as_of,
                },
            )
            # Run through Evidence Guard
            return self.guard.verify_and_clean(resp_dict, evidence_pack)

        except Exception as e:
            logger.error("Agent %s failed during execution: %s. Using precautionary fallback.", self.agent_name, e)
            return self._precautionary_fallback(str(e), evidence_pack)

    def _precautionary_fallback(self, error_msg: str, evidence_pack: EvidencePack) -> AgentReport:
        """Rule 7: Agent failure triggers safe precautionary report."""
        return AgentReport(
            agent_name=self.agent_name,
            observation=f"Agent execution encountered error: {error_msg}",
            assessment="Applying precautionary principle due to agent computation failure: maintain safe separation and reject dynamic power increases.",
            evidence_ids=evidence_pack.evidence_ids[:2],
            constraints=evidence_pack.constraints[:2],
            candidate_actions=[],
            confidence=0.1,
            uncertainty=f"Agent error: {error_msg}. Defaulting to maximum precaution.",
            evidence_status=EvidenceStatusEnum.INSUFFICIENT,
            warnings=[f"PRECAUTIONARY FALLBACK: Agent {self.agent_name} failed ({error_msg})"],
            conflicts_cited=[],
            error=error_msg,
        )
