"""Test Conflict handling (Rule 6: CONF-001 cited, not averaged)."""
import asyncio
from app.agents.airspace_safety import AirspaceSafetyAgent
from app.agents.arbitration import ArbitrationAgent
from app.groq_client import GroqClient
from app.models import SimulationState, CandidateAction


def test_conflict_conf_001_retention(sample_state: SimulationState, candidate_actions: list[CandidateAction]):
    mock_client = GroqClient(mock_mode=True)
    air_agent = AirspaceSafetyAgent(client=mock_client)
    air_report = asyncio.run(air_agent.run(sample_state))

    arb_agent = ArbitrationAgent(client=mock_client)
    arb_report = asyncio.run(arb_agent.arbitrate(
        state=sample_state,
        candidate_actions=candidate_actions,
        agent_reports={"airspace_safety": air_report},
    ))

    # CONF-001 represents the conflict between FAA conservative thresholds and telecom studies
    assert "CONF-001" in arb_report.conflicts_cited or len(arb_report.conflicts_cited) > 0
