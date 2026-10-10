"""Tests for temporal logic (Rule 3: as_of vs effective_from)."""
import pytest
from app.tools.constraint_checker import temporal_status, check_constraint
from app.models import CandidateAction, SimulationState


def test_temporal_status_future():
    # effective in 2027, as_of is 2026 -> NOT_YET_IN_FORCE
    status = temporal_status(
        legal_status="published_order",
        effective_from="2027-12-31",
        as_of="2026-10-07",
    )
    assert status == "NOT_YET_IN_FORCE"


def test_temporal_status_past():
    # effective in 2025, as_of is 2026 -> IN_FORCE (or original status)
    status = temporal_status(
        legal_status="in_force",
        effective_from="2025-01-01",
        as_of="2026-10-07",
    )
    assert status == "IN_FORCE"


def test_temporal_status_voluntary():
    status = temporal_status(
        legal_status="voluntary_commitment",
        effective_from="2024-01-01",
        as_of="2026-10-07",
    )
    assert status == "VOLUNTARY_NON_BINDING"


def test_temporal_status_embedded_date():
    status = temporal_status(
        legal_status="published_effective_2027-12-31",
        effective_from=None,
        as_of="2026-10-07",
    )
    assert status == "NOT_YET_IN_FORCE"


def test_dgca_aic_19_2025_temporal(sample_state: SimulationState):
    """DGCA AIC 19/2025 has effective date 2027-12-31 (CON-IN-002).
    As of 2026-10-07, it should be recognized as NOT_YET_IN_FORCE.
    """
    constraint = {
        "constraint_id": "CON-IN-002",
        "title": "DGCA AIC 19/2025 mandatory compliance",
        "type": "HARD",
        "legal_status": "published_order",
        "effective_from": "2027-12-31",
        "parameters": {},
        "evidence_claims": ["CLM-131"],
    }
    action = CandidateAction(
        id="ACT-1",
        desc="Test action",
        action_type="power_change",
        parameters={"power_delta_db": 1.0},
    )
    detail = check_constraint(constraint, action, sample_state, as_of="2026-10-07")
    assert detail.as_of_status == "NOT_YET_IN_FORCE"
