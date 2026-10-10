"""Unit tests for RAG pipeline, hybrid retriever, and Groq client."""
import pytest
from app.rag.hybrid_retriever import hybrid_retriever
from app.rag.pipeline import rag_pipeline
from app.groq_client import GroqClient
from app.models import SimulationState, EvidenceStatusEnum


def test_hybrid_retriever_load():
    hybrid_retriever.load()
    assert hybrid_retriever.doc_count >= 100
    assert len(hybrid_retriever.claims_by_id) >= 80
    assert len(hybrid_retriever.chunks_by_id) >= 30


def test_agent_domain_filtering(sample_state: SimulationState):
    pack = rag_pipeline.get_evidence_for_agent("airspace_safety", sample_state, top_k=6)
    assert len(pack.items) > 0
    assert pack.status in (EvidenceStatusEnum.SUFFICIENT, EvidenceStatusEnum.PARTIAL)
    # Check that returned evidence contains airspace-relevant claims
    evidence_ids = pack.evidence_ids
    assert any(eid in ("CLM-106", "CLM-107", "CLM-109", "CLM-140") for eid in evidence_ids)


def test_policy_agent_evidence(sample_state: SimulationState):
    pack = rag_pipeline.get_evidence_for_agent("policy_institutional", sample_state, top_k=6)
    assert len(pack.items) > 0
    # Must retrieve DGCA / Indian regulatory claims
    evidence_ids = pack.evidence_ids
    assert any(eid in ("CLM-130", "CLM-131", "CLM-136", "CLM-002", "CLM-003", "CLM-010") for eid in evidence_ids)


def test_evidence_pack_prompt_context(sample_state: SimulationState):
    pack = rag_pipeline.get_evidence_for_agent("spectrum", sample_state, top_k=4)
    ctx = pack.to_prompt_context()
    assert len(ctx) > 0
    assert "[" in ctx and "]" in ctx


def test_groq_client_mock():
    import asyncio

    async def _run():
        client = GroqClient(mock_mode=True)
        await client.initialize()
        resp = await client.generate_json(
            prompt="Analyze spectrum compliance",
            agent_name="spectrum",
            context={"evidence_ids": ["CLM-140"], "constraints": ["CON-INT-001"]},
        )
        assert resp["agent_name"] == "spectrum"
        assert "candidate_actions" in resp
        assert resp["confidence"] > 0

    asyncio.run(_run())

