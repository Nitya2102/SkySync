"""Pytest configuration and common fixtures."""
import sys
import json
from pathlib import Path
import pytest

# Ensure root directory is on PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models import (
    SimulationState,
    CellState,
    AircraftState,
    CandidateAction,
    ActionVerdict,
    ConstraintType,
    CheckResult,
)
from app.config import KB_DIR


@pytest.fixture
def sample_state() -> SimulationState:
    """Standard simulation state fixture matching scenario_seed.json."""
    return SimulationState(
        jurisdiction="India",
        airport="SYNTHETIC-AIRPORT-A",
        cell=CellState(
            id="CELL-17",
            band="n78",
            carrier_mhz=[3300.0, 3670.0],
            prb_util_pct=94.0,
            throughput_drop_pct=38.0,
            tx_power_dbm_per_mhz=None,
            height_m=30.0,
            distance_to_runway_threshold_m=900.0,
            lateral_offset_m=300.0,
        ),
        aircraft=AircraftState(
            callsign="SYN123",
            phase="final_approach",
            height_agl_ft=450.0,
            ra_tolerant="unknown",
            approach="ILS CAT II",
        ),
    )


@pytest.fixture
def candidate_actions() -> list[CandidateAction]:
    return [
        CandidateAction(
            id="ACT-1",
            desc="Raise cell power +3 dB",
            action_type="power_change",
            parameters={"power_delta_db": 3.0, "new_eirp_dbm_mhz": 65.0},
        ),
        CandidateAction(
            id="ACT-2",
            desc="Steer traffic to neighbouring cell >1200 m from threshold",
            action_type="traffic_steering",
            parameters={"target_cell_id": "CELL-18", "min_distance_m": 1200.0},
        ),
        CandidateAction(
            id="ACT-3",
            desc="Downtilt 3 deg + cap PRB-based power",
            action_type="downtilt",
            parameters={"downtilt_delta_deg": 3.0, "cap_prb_power": True},
        ),
        CandidateAction(
            id="ACT-4",
            desc="Activate unused carrier at 4100 MHz (n77)",
            action_type="carrier_change",
            parameters={"carrier_mhz": 4100.0},
        ),
    ]


@pytest.fixture
def scenario_seed() -> dict:
    seed_path = KB_DIR / "scenario_seed.json"
    with open(seed_path, encoding="utf-8") as f:
        return json.load(f)
