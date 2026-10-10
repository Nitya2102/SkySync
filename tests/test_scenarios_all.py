"""Integration tests executing all 3 test demonstration scenarios."""
import asyncio
import json
from app.orchestrator import Orchestrator
from app.groq_client import GroqClient
from app.models import SimulationState, CandidateAction, ActionVerdict
from app.config import KB_DIR


def test_three_distinct_scenarios():
    scenarios_file = KB_DIR / "scenarios.json"
    assert scenarios_file.exists(), "kb/scenarios.json missing"
    scenarios = json.loads(scenarios_file.read_text(encoding="utf-8"))
    assert len(scenarios) >= 3, "Expected at least 3 scenarios"

    mock_client = GroqClient(mock_mode=True)
    orch = Orchestrator()
    orch.network_agent.client = mock_client
    orch.airspace_agent.client = mock_client
    orch.spectrum_agent.client = mock_client
    orch.policy_agent.client = mock_client
    orch.opt_agent.client = mock_client
    orch.arb_agent.client = mock_client

    results = []
    for sc in scenarios:
        state = SimulationState(**sc["simulation_state"])
        actions = [CandidateAction(**a) for a in sc["candidate_actions"]]
        res = asyncio.run(orch.run_pipeline(
            state=state,
            candidate_actions=actions,
            as_of=sc.get("as_of", "2026-10-07"),
            run_id=f"run_{sc['scenario_id'].lower()}",
        ))
        results.append((sc["scenario_id"], res))

    # Scenario 1 (DEMO-001): Off-Corridor Traffic Steering Accepted
    s1_id, s1_res = results[0]
    assert s1_res.arbitration.accepted_action.id == "ACT-2"
    assert s1_res.arbitration.accepted_action.verdict == ActionVerdict.ACCEPT_PREFERRED
    assert s1_res.arbitration.requires_human_approval is False

    # Scenario 2 (DEMO-002): Physical Antenna Downtilt Beam Shaping Accepted
    s2_id, s2_res = results[1]
    assert s2_res.arbitration.accepted_action.id == "ACT-3"
    assert s2_res.arbitration.accepted_action.verdict in (ActionVerdict.ACCEPT_IF_MARGIN, ActionVerdict.ACCEPT)
    assert s2_res.arbitration.requires_human_approval is False

    # Scenario 3 (DEMO-003): Non-Tolerant Altimeter CAT III Escalation
    s3_id, s3_res = results[2]
    assert s3_res.arbitration.accepted_action.id == "ACT-5"
    assert s3_res.arbitration.accepted_action.verdict == ActionVerdict.ESCALATE
    assert s3_res.arbitration.requires_human_approval is True
