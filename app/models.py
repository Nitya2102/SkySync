"""Pydantic v2 models for the entire system."""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────
class ActionVerdict(str, Enum):
    ACCEPT = "ACCEPT"
    ACCEPT_PREFERRED = "ACCEPT_PREFERRED"
    ACCEPT_IF_MARGIN = "ACCEPT_IF_MARGIN"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


class ConstraintType(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"
    ADVISORY = "ADVISORY"
    PRECAUTIONARY = "PRECAUTIONARY"
    UNKNOWN = "UNKNOWN"
    INFORMATIONAL = "INFORMATIONAL"


class CheckResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class EvidenceStatusEnum(str, Enum):
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    PARTIAL = "partial"


# ── Simulation State ──────────────────────────────────────────────────
class CellState(BaseModel):
    id: str
    band: str
    carrier_mhz: list[float]
    prb_util_pct: float
    throughput_drop_pct: float
    tx_power_dbm_per_mhz: Optional[float] = None
    height_m: float
    distance_to_runway_threshold_m: float
    lateral_offset_m: float


class AircraftState(BaseModel):
    callsign: str
    phase: str
    height_agl_ft: float
    ra_tolerant: str = "unknown"
    approach: str = ""


class SimulationState(BaseModel):
    jurisdiction: str
    airport: str
    cell: CellState
    aircraft: AircraftState


# ── Candidate Action ──────────────────────────────────────────────────
class CandidateAction(BaseModel):
    id: str
    desc: str
    action_type: str = ""  # power_change, downtilt, traffic_steering, load_balancing, carrier_change, do_nothing
    parameters: dict[str, Any] = Field(default_factory=dict)
    # Filled by optimization/arbitration
    score: Optional[float] = None
    verdict: Optional[ActionVerdict] = None
    rejection_reasons: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    simulated_margin_db: Optional[float] = None
    margin_label: str = "SIMULATION"


# ── Evidence Item (compact, sent to LLM) ──────────────────────────────
class EvidenceItem(BaseModel):
    id: str
    text: str = Field(max_length=220)
    source_id: str = ""
    locator: str = ""
    jurisdiction: str = ""
    verification: str = ""
    legal_status: str = ""
    effective_from: Optional[str] = None
    status_flags: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)
    gap_ids: list[str] = Field(default_factory=list)
    numeric: dict[str, Any] = Field(default_factory=dict)


# ── Agent Report (per schema.json answer_contract) ────────────────────
class AgentReport(BaseModel):
    agent_name: str
    observation: str = ""
    assessment: str = ""
    chain_of_thought: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    candidate_actions: list[CandidateAction] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.5)
    uncertainty: str = ""
    evidence_status: EvidenceStatusEnum = EvidenceStatusEnum.SUFFICIENT
    warnings: list[str] = Field(default_factory=list)
    conflicts_cited: list[str] = Field(default_factory=list)
    error: Optional[str] = None


# ── Constraint Check Result ───────────────────────────────────────────
class ConstraintCheckDetail(BaseModel):
    constraint_id: str
    title: str = ""
    type: ConstraintType
    result: CheckResult
    reason: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    legal_status: str = ""
    effective_from: Optional[str] = None
    as_of_status: str = ""  # in_force, NOT_YET_IN_FORCE, voluntary, etc.


# ── Arbitration Report ────────────────────────────────────────────────
class ArbitrationReport(BaseModel):
    accepted_action: Optional[CandidateAction] = None
    rejected_actions: list[CandidateAction] = Field(default_factory=list)
    rejection_reasons: dict[str, list[str]] = Field(default_factory=dict)
    safety_status: str = ""
    spectrum_status: str = ""
    authorization_status: str = ""
    performance_status: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    conflicts_cited: list[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    rationale: str = ""
    constraint_checks: list[ConstraintCheckDetail] = Field(default_factory=list)


# ── Run Request / Result ──────────────────────────────────────────────
class RunRequest(BaseModel):
    scenario: Optional[dict[str, Any]] = None
    as_of: str = "2026-10-07"


class RunResult(BaseModel):
    run_id: str
    scenario_id: str = ""
    as_of: str = ""
    simulation_state: Optional[SimulationState] = None
    agent_reports: dict[str, AgentReport] = Field(default_factory=dict)
    arbitration: Optional[ArbitrationReport] = None
    candidate_actions: list[CandidateAction] = Field(default_factory=list)
    total_tokens: int = 0
    total_latency_s: float = 0.0
