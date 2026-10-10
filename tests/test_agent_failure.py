"""Test Agent failure handling (Rule 7: precautionary fallback)."""
import asyncio
from app.agents.base import BaseAgent
from app.models import SimulationState, EvidenceStatusEnum


class FailingAgent(BaseAgent):
    """An agent simulating a timeout or unrecoverable API error."""
    async def run(self, state: SimulationState, as_of: str = "2026-10-07"):
        evidence_pack = self.rag.get_evidence_for_agent(self.agent_name, state)
        return self._precautionary_fallback("Simulated LLM network timeout (504)", evidence_pack)


def test_agent_failure_precautionary_fallback(sample_state: SimulationState):
    agent = FailingAgent(agent_name="airspace_safety")
    report = asyncio.run(agent.run(sample_state))

    assert report.agent_name == "airspace_safety"
    assert report.confidence <= 0.2
    assert report.evidence_status == EvidenceStatusEnum.INSUFFICIENT
    assert any("PRECAUTIONARY FALLBACK" in w for w in report.warnings)
    assert report.candidate_actions == []
    assert report.error is not None
