"""Tests for the LangGraph multi-agent pipeline."""
import asyncio
import pytest
from app.graph.runner import GraphRunner
from app.graph.builder import build_graph
from app.models import SimulationState, CandidateAction, RunResult


def test_langgraph_builder_compiles():
    """Verify that build_graph creates and compiles a valid StateGraph."""
    graph = build_graph()
    assert graph is not None


def test_langgraph_run_pipeline(sample_state: SimulationState, candidate_actions: list[CandidateAction]):
    """Verify synchronous execution through the LangGraph pipeline."""
    async def _test():
        runner = GraphRunner()
        result = await runner.run_pipeline(
            state=sample_state,
            candidate_actions=candidate_actions,
            as_of="2026-10-07",
            run_id="test_lg_run",
        )

        assert isinstance(result, RunResult)
        assert result.run_id == "test_lg_run"
        assert result.arbitration is not None
        assert len(result.agent_reports) >= 4
        for agent_name in ["network", "airspace_safety", "spectrum", "policy_institutional"]:
            assert agent_name in result.agent_reports

        assert result.arbitration.accepted_action is not None
        assert result.arbitration.accepted_action.id in ["ACT-2", "ACT-3"]

    asyncio.run(_test())


def test_langgraph_stream_pipeline(sample_state: SimulationState, candidate_actions: list[CandidateAction]):
    """Verify streaming SSE generator through LangGraph."""
    async def _test():
        runner = GraphRunner()
        events = []
        async for sse_chunk in runner.stream_pipeline(
            state=sample_state,
            candidate_actions=candidate_actions,
            as_of="2026-10-07",
            run_id="test_lg_stream",
        ):
            events.append(sse_chunk)

        assert len(events) > 0
        full_stream = "".join(events)
        assert "event: run_started" in full_stream
        assert "event: agent_completed" in full_stream
        assert "event: arbitration_completed" in full_stream
        assert "event: run_finished" in full_stream

    asyncio.run(_test())
