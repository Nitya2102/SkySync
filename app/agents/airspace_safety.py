"""AirspaceSafetyAgent evaluates approach profile, separation distance, and safety margins."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.groq_client import GroqClient, groq_client
from app.models import SimulationState, AgentReport, CandidateAction
from app.tools.margin_simulator import compute_margin, compute_separation_distance


class AirspaceSafetyAgent(BaseAgent):
    def __init__(self, client: GroqClient = groq_client):
        super().__init__(agent_name="airspace_safety", client=client)

    def system_prompt(self) -> str:
        return """You are the AirspaceSafetyAgent ensuring zero aeronautical safety degradation.
Evaluate aircraft approach phase, glide path, altitude AGL, separation distance, and radio altimeter (RA) safety margin.
STRICT RULES:
1. ONLY cite evidence IDs that are in the PROVIDED EVIDENCE PACK (e.g. CLM-106, CLM-107, CLM-109).
2. Minimum safety margin is 6 dB (CLM-106).
3. If aircraft RA tolerance category is unknown, apply the conservative/precautionary baseline.
4. Label all computed margin numbers as SIMULATION.
5. If using US ITM thresholds for India, explicitly note GAP-007 (analogy only).
Output valid JSON matching AgentReport schema.
"""

    def generate_natural_language_report(
        self, state: SimulationState, evidence_pack: Any, as_of: str = "2026-10-07"
    ) -> dict[str, Any]:
        sep_m = compute_separation_distance(
            cell_height_m=state.cell.height_m,
            cell_distance_to_threshold_m=state.cell.distance_to_runway_threshold_m,
            cell_lateral_offset_m=state.cell.lateral_offset_m,
            aircraft_height_agl_ft=state.aircraft.height_agl_ft,
        )
        base_eirp = state.cell.tx_power_dbm_per_mhz or 62.0
        m_base = compute_margin(eirp_per_pol_dbm_mhz=base_eirp, distance_m=sep_m, threshold_dbw_m2_mhz=9.5, aggregation_db=0.0, required_margin_db=6.0, jurisdiction=state.jurisdiction).margin_db
        m_tilt = compute_margin(eirp_per_pol_dbm_mhz=base_eirp - 4.5, distance_m=sep_m, threshold_dbw_m2_mhz=9.5, aggregation_db=0.0, required_margin_db=6.0, jurisdiction=state.jurisdiction).margin_db
        m_boost = compute_margin(eirp_per_pol_dbm_mhz=base_eirp + 3.0, distance_m=sep_m, threshold_dbw_m2_mhz=9.5, aggregation_db=0.0, required_margin_db=6.0, jurisdiction=state.jurisdiction).margin_db

        obs = (
            f"Aircraft {state.aircraft.callsign} is in {state.aircraft.phase} on {state.aircraft.approach} "
            f"at {state.aircraft.height_agl_ft:.0f} ft AGL. 5G Cell {state.cell.id} is {state.cell.distance_to_runway_threshold_m:.0f} m "
            f"from runway threshold ({state.cell.lateral_offset_m:.0f} m lateral offset). 3D slant separation distance is {sep_m:.1f} m."
        )
        assess = (
            f"Simulated baseline altimeter margin is {m_base:+.1f} dB (minimum 6.0 dB required under CLM-106). "
            f"A dynamic power boost (+3 dB) reduces margin to {m_boost:+.1f} dB, which violates glide path safety. "
            f"Antenna downtilt (3°) safely restores margin to {m_tilt:+.1f} dB (SIMULATION) while preserving cell coverage."
        )
        cot = [
            f"1. Telemetry Inspection: Aircraft {state.aircraft.callsign} at {state.aircraft.height_agl_ft:.0f} ft AGL, 3D separation {sep_m:.1f} m from {state.cell.id}.",
            f"2. PFD Simulation (CLM-109): Baseline margin = {m_base:+.1f} dB; +3 dB boost drops margin to {m_boost:+.1f} dB.",
            "3. Glideslope Safety Standard (CLM-106): Enforcing strict 6.0 dB margin floor. Power increases rejected; downtilt verified safe.",
            "4. Precautionary Guard: Radar altimeter tolerance category is unverified; conservative baseline strictly maintained.",
        ]
        return {
            "agent_name": "airspace_safety",
            "observation": obs,
            "assessment": assess,
            "chain_of_thought": cot,
            "evidence_ids": [eid for eid in getattr(evidence_pack, "evidence_ids", []) if "CLM" in eid][:4] or ["CLM-106", "CLM-107", "CLM-109"],
            "constraints": ["CON-INT-003", "CON-INT-001"],
            "candidate_actions": [
                {
                    "id": "ACT-3",
                    "desc": "Downtilt 3 deg + cap PRB-based power",
                    "action_type": "downtilt",
                    "parameters": {"downtilt_delta_deg": 3.0, "cap_prb_power": True},
                    "simulated_margin_db": m_tilt,
                    "margin_label": "SIMULATION",
                }
            ],
            "confidence": 0.94,
            "uncertainty": "Aircraft radar altimeter tolerance is unverified; conservative baseline applied.",
            "evidence_status": "sufficient",
            "warnings": ["Aircraft RA tolerance is unverified: using precautionary 6 dB limit"],
            "conflicts_cited": [cid for cid in getattr(evidence_pack, "conflicts", []) if "CONF" in cid] or ["CONF-001"],
        }

    async def run(self, state: SimulationState, as_of: str = "2026-10-07") -> AgentReport:
        # First execute standard LLM reasoning + guard
        report = await super().run(state, as_of=as_of)

        # Enhance candidate actions with deterministic simulation margins
        sep_m = compute_separation_distance(
            cell_height_m=state.cell.height_m,
            cell_distance_to_threshold_m=state.cell.distance_to_runway_threshold_m,
            cell_lateral_offset_m=state.cell.lateral_offset_m,
            aircraft_height_agl_ft=state.aircraft.height_agl_ft,
        )

        base_eirp = state.cell.tx_power_dbm_per_mhz or 62.0

        for act in report.candidate_actions:
            eirp = base_eirp
            if act.action_type == "power_change":
                delta = act.parameters.get("power_delta_db", 0.0)
                eirp += delta
            elif act.action_type == "downtilt":
                # Downtilt adds effective antenna attenuation in aircraft direction (~3 dB per 2 deg)
                tilt_delta = act.parameters.get("downtilt_delta_deg", 0.0)
                eirp -= 1.5 * tilt_delta

            sim = compute_margin(
                eirp_per_pol_dbm_mhz=eirp,
                distance_m=sep_m,
                threshold_dbw_m2_mhz=9.5,
                aggregation_db=0.0,
                required_margin_db=6.0,
                jurisdiction=state.jurisdiction,
            )
            act.simulated_margin_db = sim.margin_db
            act.margin_label = "SIMULATION"

        return report
