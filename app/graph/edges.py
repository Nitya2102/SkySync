"""Conditional edge routing functions for the LangGraph state machine.

These functions examine the current SkyState and decide which node to visit next.
They implement the key multi-agent behaviours:
  - Conflict detection → negotiation
  - All-rejected → retry feedback loop
  - Human escalation gate
"""
from __future__ import annotations

import logging
from typing import Literal

from app.graph.state import SkyState

logger = logging.getLogger(__name__)


def route_after_cross_check(state: SkyState) -> Literal["negotiate", "optimize"]:
    """After cross-checking domain agents, decide whether to negotiate or proceed.

    If inter-agent conflicts were detected AND we haven't exhausted negotiation
    rounds, route to the negotiate node. Otherwise, proceed to optimization.
    """
    conflicts = state.get("conflicts_detected", [])
    negotiation_round = state.get("negotiation_round", 0)

    if conflicts and negotiation_round < 2:
        logger.info("Routing to negotiation: %d conflicts detected (round %d)", len(conflicts), negotiation_round)
        return "negotiate"

    if conflicts:
        logger.warning(
            "Conflicts detected but negotiation exhausted (round %d). Proceeding to optimize.",
            negotiation_round,
        )
    return "optimize"


def route_after_constraints(state: SkyState) -> Literal["optimize", "arbitrate"]:
    """After constraint checking, decide whether to retry optimization or arbitrate.

    Feedback loop: if ALL candidate actions were rejected by hard constraints
    and we haven't exceeded retry budget (2), go back to optimization with
    relaxed parameters. Otherwise, proceed to arbitration.
    """
    eligible = state.get("eligible_actions", [])
    retry_count = state.get("retry_count", 0)

    if not eligible and retry_count < 2:
        logger.info(
            "All actions rejected. Retry %d/2: routing back to optimization with relaxed constraints.",
            retry_count,
        )
        return "optimize"

    if not eligible:
        logger.warning("All actions rejected after %d retries. Proceeding to arbitration for escalation.", retry_count)

    return "arbitrate"


def route_after_arbitration(state: SkyState) -> Literal["human_gate", "audit"]:
    """After arbitration, decide whether human approval is needed.

    If the arbitration report requires human approval (ESCALATE verdict or
    CAT III autoland safety uncertainty), route to the human gate.
    """
    requires_human = state.get("requires_human_approval", False)

    if requires_human:
        logger.info("Routing to human approval gate.")
        return "human_gate"

    return "audit"
