"""Test EvidenceGuard (Rule 2: reject/drop fabricated claim IDs)."""
from app.agents.base import EvidenceGuard
from app.models import EvidenceItem, EvidenceStatusEnum
from app.rag.evidence_pack import EvidencePack


def test_evidence_guard_strips_fabricated_id():
    valid_ids = {"CLM-106", "CLM-109", "CLM-140"}
    guard = EvidenceGuard(valid_claim_ids=valid_ids)

    fake_report = {
        "agent_name": "airspace_safety",
        "observation": "Test observation",
        "assessment": "Test assessment",
        "evidence_ids": ["CLM-106", "CLM-999_HALLUCINATED", "CLM-888"],
        "confidence": 0.9,
        "uncertainty": "None",
        "candidate_actions": [],
        "warnings": [],
    }

    pack = EvidencePack(
        agent_name="airspace_safety",
        items=[
            EvidenceItem(id="CLM-106", text="6 dB safety margin"),
            EvidenceItem(id="CLM-109", text="FAA compatibility table"),
        ],
        status=EvidenceStatusEnum.SUFFICIENT,
    )

    cleaned = guard.verify_and_clean(fake_report, pack)

    # Fabricated IDs should be dropped
    assert "CLM-999_HALLUCINATED" not in cleaned.evidence_ids
    assert "CLM-888" not in cleaned.evidence_ids
    assert "CLM-106" in cleaned.evidence_ids

    # Warning must be added
    assert any("CLM-999_HALLUCINATED" in w for w in cleaned.warnings)
    assert any("CLM-888" in w for w in cleaned.warnings)
