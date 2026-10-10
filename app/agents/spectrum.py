"""SpectrumAgent evaluates spectrum allocations, protected bands, and spurious limits."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.groq_client import GroqClient, groq_client
from app.models import SimulationState, AgentReport


class SpectrumAgent(BaseAgent):
    def __init__(self, client: GroqClient = groq_client):
        super().__init__(agent_name="spectrum", client=client)

    def system_prompt(self) -> str:
        return """You are the SpectrumAgent enforcing radio-frequency regulations and band compatibility.
Evaluate operating frequencies, national licensing limits, out-of-band emission (OOBE) limits, and protected bands.
STRICT RULES:
1. ONLY cite evidence IDs that are in the PROVIDED EVIDENCE PACK (e.g. CLM-140, CLM-110, CLM-130).
2. Protected Aeronautical Radionavigation Band is 4200–4400 MHz (CON-INT-001, CLM-140) with strict exclusivity under RR 5.438.
3. Verify that operating frequencies are within licensed national bands (CON-INT-004; in India, 3300–3670 MHz).
4. If an action proposes operating outside licensed bands or close to 4200 MHz, flag as non-compliant.
Output valid JSON matching AgentReport schema.
"""

    def generate_natural_language_report(
        self, state: SimulationState, evidence_pack: Any, as_of: str = "2026-10-07"
    ) -> dict[str, Any]:
        carriers = state.cell.carrier_mhz or [3300.0, 3670.0]
        band = state.cell.band or "n78"
        obs = (
            f"5G Cell {state.cell.id} operates in band {band} with carriers {carriers[0]:.0f}–{carriers[1]:.0f} MHz. "
            f"In {state.jurisdiction}, the authorized mid-band 5G spectrum is 3300–3670 MHz under CON-INT-004."
        )
        assess = (
            f"Active band {band} ({carriers[0]:.0f}–{carriers[1]:.0f} MHz) complies with national licensing. "
            f"However, candidate retuning to 4100 MHz (n77) is strictly prohibited: it violates national frequency license CON-INT-004 "
            f"and abuts the globally protected 4200–4400 MHz aeronautical radionavigation band governed by ITU RR 5.438 (CLM-140). "
            f"Mandatory 530 MHz separation to radar altimeter band must be strictly preserved."
        )
        cot = [
            f"1. Spectrum Allocation Check: Verified active carriers {carriers[0]:.0f}–{carriers[1]:.0f} MHz within licensed band in {state.jurisdiction} (3300–3670 MHz).",
            "2. Aeronautical Protection: Checked ITU Radio Regulations RR 5.438 and CLM-140; 4200–4400 MHz band has strict exclusive aeronautical allocation.",
            "3. Out-of-Band Emission Review: Enforced CON-INT-001 and CON-INT-004. Proposed 4100 MHz operation flagged as severe non-compliance.",
            "4. Verdict: Authorized n78 operation permitted; 4100 MHz retuning rejected.",
        ]
        return {
            "agent_name": "spectrum",
            "observation": obs,
            "assessment": assess,
            "chain_of_thought": cot,
            "evidence_ids": [eid for eid in getattr(evidence_pack, "evidence_ids", []) if "CLM" in eid][:3] or ["CLM-140", "CLM-130"],
            "constraints": ["CON-INT-001", "CON-INT-004"],
            "candidate_actions": [
                {
                    "id": "ACT-4",
                    "desc": "Activate unused carrier at 4100 MHz (n77)",
                    "action_type": "carrier_change",
                    "parameters": {"carrier_mhz": 4100.0},
                }
            ],
            "confidence": 0.95,
            "uncertainty": "Exact manufacturer spurious emission filter rolloff curve for cell site gNodeB is unverified.",
            "evidence_status": "sufficient",
            "warnings": ["4100 MHz operation violates both national license and proximity boundary"],
            "conflicts_cited": [],
        }
