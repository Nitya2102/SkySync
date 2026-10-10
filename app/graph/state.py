"""SkyState – the shared typed state that flows through every LangGraph node.

This is the single source of truth for the entire multi-agent pipeline.
Each node reads from and writes back to this state, enabling:
  - Agent communication (every agent sees every other agent's output)
  - Feedback loops (retry_count tracks re-optimization passes)
  - Conflict negotiation (conflicts_detected triggers re-query)
  - Human-in-the-loop (requires_human_approval gates arbitration)
  - Full audit trail (every field is checkpointed at every step)
"""
from __future__ import annotations

from typing import Annotated, Any, Optional
from typing_extensions import TypedDict

from app.models import (
    AgentReport,
    ArbitrationReport,
    CandidateAction,
    ConstraintCheckDetail,
    SimulationState,
)


def merge_reports(
    existing: Optional[dict[str, AgentReport]],
    new_val: Optional[dict[str, AgentReport]],
) -> dict[str, AgentReport]:
    """Reducer for agent_reports: merges reports from concurrent fan-out nodes."""
    res = dict(existing or {})
    if new_val:
        res.update(new_val)
    return res


def merge_phase_log(
    existing: Optional[list[dict[str, Any]]],
    new_val: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Reducer for phase_log: accumulates log entries from all steps."""
    res = list(existing or [])
    if new_val:
        res.extend(new_val)
    return res


class SkyState(TypedDict, total=False):
    """Typed state dictionary for the LangGraph coexistence pipeline.

    Fields are accumulated and mutated by graph nodes.
    `total=False` means all fields are optional (nodes only set what they need).
    """

    # ── Input (set by validate_node) ──────────────────────────────────
    simulation_state: SimulationState
    candidate_actions: list[CandidateAction]
    as_of: str
    run_id: str
    scenario_id: str

    # ── Phase 1: Domain Agent Reports (accumulated via reducer) ──────
    agent_reports: Annotated[dict[str, AgentReport], merge_reports]

    # ── Cross-Check / Negotiation ─────────────────────────────────────
    conflicts_detected: list[str]
    negotiation_round: int

    # ── Phase 2: Optimization ─────────────────────────────────────────
    ranked_actions: list[CandidateAction]

    # ── Phase 3: Deterministic Constraint Results ─────────────────────
    constraint_results: dict[str, list[ConstraintCheckDetail]]
    eligible_actions: list[CandidateAction]
    rejected_actions: list[CandidateAction]
    rejection_reasons: dict[str, list[str]]
    retry_count: int

    # ── Phase 4: Arbitration ──────────────────────────────────────────
    arbitration: Optional[ArbitrationReport]
    requires_human_approval: bool

    # ── Audit / Observability (accumulated via reducer) ───────────────
    phase_log: Annotated[list[dict[str, Any]], merge_phase_log]
    total_latency_s: float
    error: Optional[str]
