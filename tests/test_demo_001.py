"""End-to-end integration test on DEMO-001 benchmark."""
import asyncio
from app.orchestrator import Orchestrator
from app.groq_client import GroqClient
from app.models import SimulationState, CandidateAction, ActionVerdict
from app.config import RUNS_DIR


def test_demo_001_actions_and_arbitration(sample_state: SimulationState, candidate_actions: list[CandidateAction]):
    # Setup orchestrator with mock client
    mock_client = GroqClient(mock_mode=True)
    orch = Orchestrator()
    orch.network_agent.client = mock_client
    orch.airspace_agent.client = mock_client
    orch.spectrum_agent.client = mock_client
    orch.policy_agent.client = mock_client
    orch.opt_agent.client = mock_client
    orch.arb_agent.client = mock_client

    result = asyncio.run(orch.run_pipeline(
        state=sample_state,
        candidate_actions=candidate_actions,
        as_of="2026-10-07",
        run_id="test_demo_001",
    ))

    arb = result.arbitration
    assert arb is not None, "Arbitration report is missing"

    # 1. ACT-1 must be REJECTED
    rejected_ids = [a.id for a in arb.rejected_actions]
    assert "ACT-1" in rejected_ids, f"ACT-1 was not rejected! Rejected: {rejected_ids}"

    # 2. ACT-4 must be REJECTED
    assert "ACT-4" in rejected_ids, f"ACT-4 was not rejected! Rejected: {rejected_ids}"

    # 3. ACT-2 must be ACCEPTED as preferred mitigation
    assert arb.accepted_action is not None, "No action was accepted!"
    assert arb.accepted_action.id == "ACT-2", f"Expected ACT-2, got {arb.accepted_action.id}"
    assert arb.accepted_action.verdict in (ActionVerdict.ACCEPT_PREFERRED, ActionVerdict.ACCEPT)

    # 4. Check policy agent reports NOT_YET_IN_FORCE
    policy_rep = result.agent_reports.get("policy_institutional")
    assert policy_rep is not None
    assert any("NOT_YET_IN_FORCE" in w for w in policy_rep.warnings) or "NOT_YET_IN_FORCE" in policy_rep.assessment

    # 5. Check audit log was written
    log_file = RUNS_DIR / "test_demo_001.json"
    assert log_file.exists(), f"Audit log file {log_file} does not exist"
