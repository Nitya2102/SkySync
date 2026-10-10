"""Graph runner — executes the compiled LangGraph and provides SSE streaming.

This module is the drop-in replacement for the old `orchestrator.py`.
It provides:
  1. `run_pipeline()` — synchronous full execution, returns RunResult
  2. `stream_pipeline()` — async generator yielding SSE events per node
  3. `run_with_human_gate()` — execution with pause/resume for human approval

The runner maps LangGraph's native streaming events into the SSE format
that the existing frontend expects.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Optional

from app.config import RUNS_DIR
from app.graph.builder import build_graph
from app.graph.state import SkyState
from app.models import (
    CandidateAction,
    RunResult,
    SimulationState,
)

logger = logging.getLogger(__name__)


class GraphRunner:
    """Executes the LangGraph pipeline and manages graph lifecycle."""

    def __init__(self, enable_human_gate: bool = False):
        self._graph = build_graph(enable_human_gate=enable_human_gate)
        self._enable_human_gate = enable_human_gate

    async def run_pipeline(
        self,
        state: SimulationState,
        candidate_actions: list[CandidateAction],
        as_of: str = "2026-10-07",
        run_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
    ) -> RunResult:
        """Execute the full pipeline synchronously. Returns RunResult."""
        run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        start_t = time.time()

        # Build initial state
        initial_state: SkyState = {
            "simulation_state": state,
            "candidate_actions": candidate_actions,
            "as_of": as_of,
            "run_id": run_id,
            "scenario_id": scenario_id or "",
            "agent_reports": {},
            "conflicts_detected": [],
            "negotiation_round": 0,
            "ranked_actions": [],
            "constraint_results": {},
            "eligible_actions": [],
            "rejected_actions": [],
            "rejection_reasons": {},
            "retry_count": 0,
            "arbitration": None,
            "requires_human_approval": False,
            "phase_log": [],
            "total_latency_s": 0.0,
            "error": None,
        }

        # Thread-level config for checkpointing
        config = {"configurable": {"thread_id": run_id}}

        # Execute the graph
        try:
            final_state = await self._graph.ainvoke(initial_state, config)
        except Exception as e:
            logger.error("Graph execution failed: %s", e)
            return RunResult(
                run_id=run_id,
                scenario_id=scenario_id or "",
                as_of=as_of,
                simulation_state=state,
                total_latency_s=time.time() - start_t,
            )

        total_latency = time.time() - start_t

        # Map LangGraph final state → RunResult
        result = RunResult(
            run_id=run_id,
            scenario_id=final_state.get("scenario_id", ""),
            as_of=as_of,
            simulation_state=state,
            agent_reports=final_state.get("agent_reports", {}),
            arbitration=final_state.get("arbitration"),
            candidate_actions=final_state.get("candidate_actions", []),
            total_latency_s=round(total_latency, 3),
        )

        return result

    async def stream_pipeline(
        self,
        state: SimulationState,
        candidate_actions: list[CandidateAction],
        as_of: str = "2026-10-07",
        run_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        delay: float = 1.5,
    ) -> AsyncGenerator[str, None]:
        """Stream SSE events during graph execution with optional pacing delay.

        Yields SSE-formatted strings compatible with the frontend.
        """
        run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        start_t = time.time()

        def sse(event: str, data: Any) -> str:
            payload = json.dumps(data, default=str)
            return f"event: {event}\ndata: {payload}\n\n"

        yield sse("run_started", {"run_id": run_id, "as_of": as_of, "engine": "langgraph"})

        initial_state: SkyState = {
            "simulation_state": state,
            "candidate_actions": candidate_actions,
            "as_of": as_of,
            "run_id": run_id,
            "scenario_id": scenario_id or "",
            "agent_reports": {},
            "conflicts_detected": [],
            "negotiation_round": 0,
            "ranked_actions": [],
            "constraint_results": {},
            "eligible_actions": [],
            "rejected_actions": [],
            "rejection_reasons": {},
            "retry_count": 0,
            "arbitration": None,
            "requires_human_approval": False,
            "phase_log": [],
            "total_latency_s": 0.0,
            "error": None,
        }

        config = {"configurable": {"thread_id": run_id}}

        # Phase descriptions for SSE
        phase_map = {
            "validate": (0, "Validating scenario input & flight telemetry"),
            "network": (1, "Network Agent analyzing PRB congestion & QoS"),
            "airspace": (1, "Airspace Safety Agent computing PFD margin"),
            "spectrum": (1, "Spectrum Agent verifying ITU RR 5.438 compliance"),
            "policy": (1, "Policy Agent auditing DGCA circulars & human gate"),
            "merge_domain": (1, "Merging domain agent action proposals"),
            "cross_check": (1, "Cross-checking inter-agent conflict points"),
            "negotiate": (1, "Negotiating conflicting QoS vs Safety mandates"),
            "optimize": (2, "Optimization Agent ranking Pareto trade-offs"),
            "constraint_check": (2, "Deterministic constraint verification"),
            "arbitrate": (3, "Arbitration Agent synthesizing decision ledger"),
            "human_gate": (3, "Human approval gate"),
            "audit": (3, "Writing cryptographically timestamped audit log"),
        }

        reported_agents = set()
        last_phase = -1

        try:
            async for event in self._graph.astream(initial_state, config, stream_mode="updates"):
                for node_name, node_output in event.items():
                    # Emit phase_started SSE if phase changed
                    if node_name in phase_map:
                        phase_num, description = phase_map[node_name]
                        if phase_num > last_phase:
                            last_phase = phase_num
                            yield sse("phase_started", {
                                "phase": phase_num,
                                "description": description,
                            })
                            if delay > 0:
                                await asyncio.sleep(delay * 0.6)

                    # Emit node-level events
                    yield sse("node_started", {
                        "node": node_name,
                        "description": phase_map.get(node_name, (0, node_name))[1],
                    })

                    # Emit agent_completed for domain agents
                    agent_reports = node_output.get("agent_reports", {})
                    for agent_name, report in agent_reports.items():
                        if agent_name not in reported_agents:
                            reported_agents.add(agent_name)
                            yield sse("agent_completed", {
                                "agent_name": agent_name,
                                "report": report.model_dump(),
                            })
                            if delay > 0:
                                await asyncio.sleep(delay)

                    # Emit conflict detection events
                    conflicts = node_output.get("conflicts_detected")
                    if conflicts:
                        yield sse("conflicts_detected", {
                            "conflicts": conflicts,
                            "negotiation_round": node_output.get("negotiation_round", 0),
                        })
                        if delay > 0:
                            await asyncio.sleep(delay * 0.8)

                    # Emit constraint results
                    if "eligible_actions" in node_output:
                        eligible = node_output.get("eligible_actions", [])
                        rejected = node_output.get("rejected_actions", [])
                        yield sse("constraint_results", {
                            "eligible_count": len(eligible),
                            "rejected_count": len(rejected),
                            "retry_count": node_output.get("retry_count", 0),
                            "rejection_reasons": node_output.get("rejection_reasons", {}),
                        })
                        if delay > 0:
                            await asyncio.sleep(delay * 0.8)

                    # Emit arbitration result
                    arb = node_output.get("arbitration")
                    if arb is not None:
                        yield sse("arbitration_completed", {
                            "arbitration": arb.model_dump(),
                        })
                        if delay > 0:
                            await asyncio.sleep(delay * 1.0)

                    yield sse("node_completed", {"node": node_name})

        except Exception as e:
            logger.error("Stream pipeline error: %s", e)
            yield sse("error", {"message": str(e)})

        # Final: build and emit the complete RunResult
        total_latency = time.time() - start_t

        # Get final state from checkpointer
        try:
            final_snapshot = await self._graph.aget_state(config)
            final_state = final_snapshot.values if final_snapshot else initial_state
        except Exception:
            final_state = initial_state

        result = RunResult(
            run_id=run_id,
            scenario_id=final_state.get("scenario_id", ""),
            as_of=as_of,
            simulation_state=state,
            agent_reports=final_state.get("agent_reports", {}),
            arbitration=final_state.get("arbitration"),
            candidate_actions=final_state.get("candidate_actions", []),
            total_latency_s=round(total_latency, 3),
        )

        yield sse("run_finished", {"run_result": result.model_dump()})


# ── Global singleton ──────────────────────────────────────────────────
graph_runner = GraphRunner(enable_human_gate=False)
