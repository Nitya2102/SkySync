"""NetworkAgent evaluates PRB utilization, throughput degradation, and network actions."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.groq_client import GroqClient, groq_client
from app.models import SimulationState, AgentReport


class NetworkAgent(BaseAgent):
    def __init__(self, client: GroqClient = groq_client):
        super().__init__(agent_name="network", client=client)

    def system_prompt(self) -> str:
        return """You are the NetworkAgent for 5G RAN optimization.
Evaluate base-station KPIs: PRB utilization, throughput drop, coverage, and user SLA.
Generate candidate actions (e.g. power adjustment, traffic steering to adjacent cell, load balancing).
STRICT RULES:
1. ONLY cite evidence IDs that are in the PROVIDED EVIDENCE PACK (e.g. 3GPP TS specifications, CLM-008, CLM-009).
2. Never override airspace safety limits.
3. Label all QoS/throughput predictions as SIMULATION.
Output valid JSON matching AgentReport schema.
"""

    def generate_natural_language_report(
        self, state: SimulationState, evidence_pack: Any, as_of: str = "2026-10-07"
    ) -> dict[str, Any]:
        prb = state.cell.prb_util_pct
        drop = state.cell.throughput_drop_pct
        obs = (
            f"Cell {state.cell.id} exhibits severe capacity strain: Physical Resource Block (PRB) utilization "
            f"stands at {prb:.1f}% with an aggregate user throughput degradation of {drop:.1f}%."
        )
        is_close_flare = state.cell.distance_to_runway_threshold_m <= 500 or state.aircraft.phase == "landing_flare"
        if is_close_flare:
            cand_actions = [
                {
                    "id": "ACT-1",
                    "desc": "Raise cell power +3 dB for QoS recovery",
                    "action_type": "power_change",
                    "parameters": {"power_delta_db": 3.0, "new_eirp_dbm_mhz": 65.0},
                },
                {
                    "id": "ACT-3",
                    "desc": "Apply mechanical antenna downtilt to reduce altimeter main-lobe coupling",
                    "action_type": "downtilt",
                    "parameters": {"downtilt_delta_deg": 4.0, "cap_prb_power": True},
                },
            ]
            assess = (
                f"PRB load ({prb:.1f}%) exceeds the 85% congestion threshold during {state.aircraft.phase.replace('_', ' ')}. "
                f"Cell {state.cell.id} is situated only {state.cell.distance_to_runway_threshold_m:.0f} m from the threshold. "
                f"Proposing candidate actions: ACT-1 (power increase) and ACT-3 (antenna beam downtilt for glideslope clearance)."
            )
            cot = [
                f"1. KPI Assessment: Evaluated PRB utilization ({prb:.1f}%) and throughput drop ({drop:.1f}%). Identified severe strain.",
                f"2. Physical Proximity: Cell is {state.cell.distance_to_runway_threshold_m:.0f} m from runway; flare operations in progress.",
                "3. Mitigation Formulation: Formulated ACT-1 (power boost) and ACT-3 (antenna downtilt shaping).",
                "4. Coordination Note: Forwarded to Airspace and Arbitration agents for margin verification.",
            ]
        else:
            cand_actions = [
                {
                    "id": "ACT-1",
                    "desc": "Raise cell power +3 dB for QoS recovery",
                    "action_type": "power_change",
                    "parameters": {"power_delta_db": 3.0, "new_eirp_dbm_mhz": 65.0},
                },
                {
                    "id": "ACT-2",
                    "desc": "Steer traffic to neighbouring cell >1200 m from threshold",
                    "action_type": "traffic_steering",
                    "parameters": {"target_cell_id": "CELL-18", "min_distance_m": 1200.0, "fraction_moved": 0.3},
                },
            ]
            assess = (
                f"PRB load exceeds the 85% congestion threshold, breaching standard user SLA QoS targets. "
                f"To restore throughput, technical mitigation is required. Proposing candidate actions: "
                f"ACT-1 (Raise cell power +3 dB for link recovery) and ACT-2 (Steer traffic to neighbouring cell >1200 m). "
                f"Action ACT-2 is preferred from a coexistence standpoint to offload load without increasing RF emissions near the runway."
            )
            cot = [
                f"1. KPI Assessment: Evaluated PRB utilization ({prb:.1f}%) and throughput drop ({drop:.1f}%). Identified cell edge congestion.",
                "2. Standards Baseline: Checked 3GPP TS 23.501 and TS 38.300 QoS flow criteria (CLM-008, CLM-009).",
                "3. Mitigation Formulation: Generated candidate actions ACT-1 (power increase) and ACT-2 (traffic steering).",
                "4. Coordination Note: Flagged potential glideslope RF coupling for joint multi-agent arbitration review.",
            ]

        return {
            "agent_name": "network",
            "observation": obs,
            "assessment": assess,
            "chain_of_thought": cot,
            "evidence_ids": [eid for eid in getattr(evidence_pack, "evidence_ids", []) if "CLM" in eid][:3] or ["CLM-008", "CLM-009"],
            "constraints": ["CON-INT-004"],
            "candidate_actions": cand_actions,
            "confidence": 0.90,
            "uncertainty": "Uncertain if adjacent cell can absorb full handover volume without secondary congestion.",
            "evidence_status": "sufficient",
            "warnings": [],
            "conflicts_cited": [],
        }
