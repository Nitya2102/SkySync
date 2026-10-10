"""Test Tier-3 evidence handling (Rule 4: warning, not HARD rejection)."""
from app.agents.base import EvidenceGuard
from app.models import EvidenceItem, EvidenceStatusEnum
from app.rag.evidence_pack import EvidencePack


def test_tier3_evidence_produces_warning_not_hard_rejection():
    valid_ids = {"CLM-151", "CLM-136"}
    guard = EvidenceGuard(valid_claim_ids=valid_ids)

    # CLM-136 is COAI proposed timeline (secondary report / Tier-3)
    pack = EvidencePack(
        agent_name="policy_institutional",
        items=[
            EvidenceItem(
                id="CLM-136",
                text="COAI industry proposed 18 months",
                verification="secondary_report",
            )
        ],
        status=EvidenceStatusEnum.SUFFICIENT,
    )

    report_dict = {
        "agent_name": "policy_institutional",
        "observation": "Industry association proposed transition timeline",
        "assessment": "COAI requested 18 months for airport modifications",
        "evidence_ids": ["CLM-136"],
        "confidence": 0.75,
        "candidate_actions": [],
    }

    cleaned = guard.verify_and_clean(report_dict, pack)

    # Must preserve the valid ID
    assert "CLM-136" in cleaned.evidence_ids

    # Must generate warning regarding Tier-3 / secondary evidence
    assert any("Tier-3" in w or "secondary" in w for w in cleaned.warnings)

    # Error must be None (not a hard failure)
    assert cleaned.error is None
