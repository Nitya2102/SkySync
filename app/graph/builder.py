"""Graph builder — assembles the LangGraph state machine from nodes and edges.

This is the core of the LangGraph migration:
  - Defines the execution graph topology
  - Configures fan-out for concurrent domain agents
  - Wires conditional edges for negotiation, retry, and human-in-the-loop
  - Compiles the graph with checkpointing for replay and audit

The compiled graph replaces the old procedural Orchestrator while keeping
every agent, tool, and KB component unchanged.
"""
from __future__ import annotations

import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.edges import (
    route_after_arbitration,
    route_after_constraints,
    route_after_cross_check,
)
from app.graph.nodes import (
    airspace_node,
    arbitrate_node,
    audit_node,
    constraint_node,
    cross_check_node,
    merge_domain_node,
    negotiate_node,
    network_node,
    optimize_node,
    policy_node,
    spectrum_node,
    validate_node,
)
from app.graph.state import SkyState

logger = logging.getLogger(__name__)


def build_graph(enable_human_gate: bool = True) -> StateGraph:
    """Build and compile the SkySync multi-agent state graph.

    Args:
        enable_human_gate: If True, the graph will pause (interrupt_before)
            at the human_gate node when human approval is required.
            Set to False for fully automated demo runs.

    Returns:
        Compiled LangGraph StateGraph ready for invocation.

    Graph topology:
        START
          → validate
          → [network, airspace, spectrum, policy]  (concurrent fan-out)
          → merge_domain
          → cross_check
          → (negotiate)? → optimize
          → constraint_check
          → (retry optimize)? or → arbitrate
          → (human_gate)? → audit
          → END
    """
    graph = StateGraph(SkyState)

    # ── Register all nodes ────────────────────────────────────────────
    graph.add_node("validate", validate_node)

    # Domain agents (will run concurrently via fan-out)
    graph.add_node("network", network_node)
    graph.add_node("airspace", airspace_node)
    graph.add_node("spectrum", spectrum_node)
    graph.add_node("policy", policy_node)

    # Synchronization + cross-check
    graph.add_node("merge_domain", merge_domain_node)
    graph.add_node("cross_check", cross_check_node)
    graph.add_node("negotiate", negotiate_node)

    # Optimization + constraints
    graph.add_node("optimize", optimize_node)
    graph.add_node("constraint_check", constraint_node)

    # Arbitration + human gate + audit
    graph.add_node("arbitrate", arbitrate_node)
    graph.add_node("human_gate", _human_gate_node)
    graph.add_node("audit", audit_node)

    # ── Wire edges ────────────────────────────────────────────────────

    # START → validate
    graph.add_edge(START, "validate")

    # validate → fan-out to 4 domain agents concurrently
    graph.add_edge("validate", "network")
    graph.add_edge("validate", "airspace")
    graph.add_edge("validate", "spectrum")
    graph.add_edge("validate", "policy")

    # All 4 domain agents → merge_domain (sync barrier)
    graph.add_edge("network", "merge_domain")
    graph.add_edge("airspace", "merge_domain")
    graph.add_edge("spectrum", "merge_domain")
    graph.add_edge("policy", "merge_domain")

    # merge_domain → cross_check
    graph.add_edge("merge_domain", "cross_check")

    # cross_check → negotiate (if conflicts) or optimize (if clean)
    graph.add_conditional_edges("cross_check", route_after_cross_check)

    # negotiate → optimize
    graph.add_edge("negotiate", "optimize")

    # optimize → constraint_check
    graph.add_edge("optimize", "constraint_check")

    # constraint_check → optimize (retry) or arbitrate
    graph.add_conditional_edges("constraint_check", route_after_constraints)

    # arbitrate → human_gate (if needed) or audit
    graph.add_conditional_edges("arbitrate", route_after_arbitration)

    # human_gate → audit
    graph.add_edge("human_gate", "audit")

    # audit → END
    graph.add_edge("audit", END)

    # ── Compile with checkpointer ─────────────────────────────────────
    checkpointer = MemorySaver()

    interrupt_nodes = []
    if enable_human_gate:
        interrupt_nodes.append("human_gate")

    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_nodes if interrupt_nodes else None,
    )

    logger.info("SkySync LangGraph compiled: %d nodes, human_gate=%s", 12, enable_human_gate)
    return compiled


async def _human_gate_node(state: SkyState) -> dict:
    """Human-in-the-loop gate.

    When `interrupt_before` is set on this node, LangGraph will pause execution
    here and wait for human input before continuing. The graph can be resumed
    by calling `graph.ainvoke(None, config)` after human review.

    If running without human gate (enable_human_gate=False), this is a pass-through.
    """
    from app.graph.nodes import _log_phase

    arb = state.get("arbitration")
    accepted = arb.accepted_action if arb else None

    logger.info(
        "HUMAN GATE: Requires approval for action %s (%s). Graph paused.",
        accepted.id if accepted else "NONE",
        accepted.desc if accepted else "No action",
    )

    return {
        "phase_log": _log_phase(
            state, "human_gate",
            f"Awaiting human approval for: {accepted.id if accepted else 'NONE'}"
        ),
    }


# ── Convenience: Pre-built graph instance ─────────────────────────────

def get_default_graph():
    """Get the default compiled graph (with human gate disabled for auto-demo)."""
    return build_graph(enable_human_gate=False)
