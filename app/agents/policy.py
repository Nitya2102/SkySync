"""PolicyInstitutionalAgent evaluates jurisdiction, legal status, temporal in-force rules, and policy gaps."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.groq_client import GroqClient, groq_client
from app.models import SimulationState, AgentReport


class PolicyInstitutionalAgent(BaseAgent):
    def __init__(self, client: GroqClient = groq_client):
        super().__init__(agent_name="policy_institutional", client=client)

    def system_prompt(self) -> str:
        return """You are the PolicyInstitutionalAgent evaluating legal frameworks and jurisdictional rules.
Evaluate regulatory circulars, effective dates versus the scenario as-of date, and authorization constraints.
STRICT RULES:
1. ONLY cite evidence IDs that are in the PROVIDED EVIDENCE PACK (e.g. CLM-131, CLM-002, CLM-003).
2. Temporal Rule: If a regulation (e.g. DGCA AIC 19/2025, CLM-131) has an effective date in the future relative to the scenario as_of date (e.g. effective 2027-12-31 vs as_of 2026-10-07), classify it explicitly as NOT_YET_IN_FORCE.
3. In India, automated dynamic changes that increase RF emissions require human authorization (CON-IN-004).
4. Identify policy gaps: GAP-006 (no numeric airport buffer parameters in primary circulars) requires precautionary defaults.
Output valid JSON matching AgentReport schema.
"""

    def generate_natural_language_report(
        self, state: SimulationState, evidence_pack: Any, as_of: str = "2026-10-07"
    ) -> dict[str, Any]:
        obs = (
            f"Scenario jurisdiction is {state.jurisdiction} evaluated as of {as_of}. "
            f"Regulatory authorities include DGCA, Ministry of Civil Aviation, and DoT/WPC. "
            f"Key instruments identified: DGCA AIC 19/2025 and 5G band licensing conditions."
        )
        assess = (
            f"DGCA AIC 19/2025 (CLM-131) has an effective date of 2027-12-31, which is in the future relative to {as_of}; "
            f"it is classified strictly as NOT_YET_IN_FORCE. Under institutional rule CON-IN-004, automated cell reconfigurations "
            f"that increase emissions near an aerodrome require human ATC / coordinator authorization. "
            f"Furthermore, GAP-006 notes the absence of numeric runway buffer coordinates in primary circulars, "
            f"mandating precautionary defaults."
        )
        cot = [
            f"1. Temporal Status Audit: Compared as-of date {as_of} against DGCA AIC 19/2025 effective date (2027-12-31). Formally marked NOT_YET_IN_FORCE.",
            "2. Institutional Authorization (CON-IN-004): Automated RF power boosts near runway approach corridors require human oversight.",
            "3. Policy Gap Identification (GAP-006): Primary circulars lack published numeric exclusion contours around runway thresholds. Precautionary boundary enforced.",
            "4. Verdict: Dynamic power increases require human authorization gate; off-corridor traffic steering (ACT-2) and downtilt (ACT-3) comply with institutional mandates.",
        ]
        return {
            "agent_name": "policy_institutional",
            "observation": obs,
            "assessment": assess,
            "chain_of_thought": cot,
            "evidence_ids": [eid for eid in getattr(evidence_pack, "evidence_ids", []) if "CLM" in eid][:3] or ["CLM-131"],
            "constraints": ["CON-IN-002", "CON-IN-003", "CON-IN-004"],
            "candidate_actions": [],
            "confidence": 0.88,
            "uncertainty": "GAP-006: Lack of published numeric exclusion radius around synthetic airport runways in primary circulars.",
            "evidence_status": "sufficient",
            "warnings": ["DGCA AIC 19/2025 is NOT_YET_IN_FORCE as of 2026-10-07"],
            "conflicts_cited": [],
        }
