"""Action effect model – simple parametric with documented assumptions.

No invented regulatory numbers; all effects are labelled SIMULATION.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models import CandidateAction, SimulationState


@dataclass
class ActionEffect:
    """Predicted effect of an action on network and safety metrics."""
    new_prb_util_pct: float
    new_throughput_drop_pct: float
    eirp_change_db: float
    description: str
    label: str = "SIMULATION"
    assumptions: str = ""


def estimate_effect(action: CandidateAction, state: SimulationState) -> ActionEffect:
    """Estimate the parametric effect of an action on the simulation state.

    Uses simple, documented models:
    - Power change: direct dB delta on EIRP; PRB utilization unchanged
    - Traffic steering: fraction of load moved reduces PRB util proportionally
    - Load balancing: similar to traffic steering with smaller fraction
    - Carrier change: PRB util resets based on new carrier capacity
    - Downtilt: modelled as a power reduction at the aircraft direction
    - Do-nothing: no change
    """
    prb = state.cell.prb_util_pct
    thr_drop = state.cell.throughput_drop_pct

    atype = action.action_type
    params = action.parameters

    if atype == "power_change":
        delta = params.get("power_delta_db", 0)
        return ActionEffect(
            new_prb_util_pct=prb,
            new_throughput_drop_pct=max(0, thr_drop - abs(delta) * 2) if delta > 0 else thr_drop,
            eirp_change_db=delta,
            description=f"Power change {delta:+.1f} dB",
            assumptions="Assumes linear relationship between power and throughput recovery",
        )

    if atype == "traffic_steering":
        fraction = params.get("fraction_moved", 0.3)
        new_prb = prb * (1.0 - fraction)
        new_drop = thr_drop * (1.0 - fraction * 0.5)
        return ActionEffect(
            new_prb_util_pct=round(new_prb, 1),
            new_throughput_drop_pct=round(new_drop, 1),
            eirp_change_db=0,
            description=f"Steer {fraction*100:.0f}% traffic to neighbour",
            assumptions="Assumes neighbour cell has capacity; fraction is configurable",
        )

    if atype == "load_balancing":
        fraction = params.get("fraction_moved", 0.15)
        new_prb = prb * (1.0 - fraction)
        return ActionEffect(
            new_prb_util_pct=round(new_prb, 1),
            new_throughput_drop_pct=round(thr_drop * 0.85, 1),
            eirp_change_db=0,
            description=f"Load balance {fraction*100:.0f}%",
            assumptions="Assumes even load distribution across carriers",
        )

    if atype == "downtilt":
        tilt_deg = params.get("tilt_degrees", 3)
        # Approximate: 3 deg downtilt ~ -2 dB towards aircraft above horizon
        eirp_reduction = tilt_deg * 0.67
        return ActionEffect(
            new_prb_util_pct=prb,
            new_throughput_drop_pct=thr_drop,
            eirp_change_db=-eirp_reduction,
            description=f"Downtilt {tilt_deg}° (SIMULATION: ~{eirp_reduction:.1f} dB reduction towards aircraft)",
            assumptions="Rough approximation; actual pattern depends on antenna. GAP-010: no KB evidence for tilt actuation.",
        )

    if atype == "carrier_change":
        return ActionEffect(
            new_prb_util_pct=50.0,  # Assume fresh carrier starts at moderate load
            new_throughput_drop_pct=0,
            eirp_change_db=0,
            description=f"Carrier change to {params.get('carrier_mhz', '?')} MHz",
            assumptions="Assumes new carrier has available capacity",
        )

    # do_nothing or unrecognized
    return ActionEffect(
        new_prb_util_pct=prb,
        new_throughput_drop_pct=thr_drop,
        eirp_change_db=0,
        description="No change (do-nothing)",
        assumptions="",
    )
