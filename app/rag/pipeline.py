"""RAG pipeline integrating query planning, hybrid retrieval, and evidence packing."""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.models import SimulationState
from app.rag.evidence_pack import EvidencePack, build_evidence_pack
from app.rag.hybrid_retriever import hybrid_retriever

logger = logging.getLogger(__name__)


def plan_queries_for_agent(agent_name: str, state: SimulationState) -> list[str]:
    """Generate focused search queries based on agent domain and scenario state."""
    jur = state.jurisdiction
    band = state.cell.band
    carriers = " ".join(str(f) for f in state.cell.carrier_mhz)

    if agent_name == "network":
        return [
            f"5G NR {band} PRB utilization QoS throughput cell capacity",
            "traffic steering load balancing handover 3GPP",
            "gNodeB power control coverage optimization",
        ]
    elif agent_name == "airspace_safety":
        return [
            "radio altimeter interference safety margin PFD threshold",
            "approach glide path 500 ft AGL radar altimeter ITM tolerance",
            "FAA compatibility analysis 6 dB margin spurious emission",
        ]
    elif agent_name == "spectrum":
        return [
            f"radio altimeter band 4200 4400 MHz exclusivity {band}",
            f"{jur} spectrum allocation licensing {carriers} MHz",
            "out-of-band emissions spurious limit 5G guard band",
        ]
    elif agent_name == "policy_institutional":
        return [
            f"{jur} DGCA AIC circular airport restrictions",
            "human authorization requirement dynamic spectrum emission",
            "mandatory compliance effective date regulatory order",
        ]
    elif agent_name == "optimization":
        return [
            "coexistence interference mitigation Pareto trade-off",
            "antenna downtilt PRB capping traffic steering separation distance",
            "ECC 362 separation distance runway threshold",
        ]
    elif agent_name == "arbitration":
        return [
            "radio altimeter safety margin hard constraint",
            "conflict resolution precedence national authorization",
            "precautionary principle evidence gap",
        ]
    return ["5G coexistence airspace safety"]


class RAGPipeline:
    """End-to-end RAG orchestrator for agents."""

    def __init__(self):
        self.retriever = hybrid_retriever

    def get_evidence_for_agent(
        self,
        agent_name: str,
        state: SimulationState,
        top_k: int = 6,
    ) -> EvidencePack:
        """Run query planning, hybrid retrieval, and evidence packing for an agent."""
        queries = plan_queries_for_agent(agent_name, state)
        combined_query = " ".join(queries)

        retrieved = self.retriever.search(
            query=combined_query,
            agent=agent_name,
            jurisdiction=state.jurisdiction,
            top_k=top_k,
        )

        pack = build_evidence_pack(
            agent_name=agent_name,
            retrieval_results=retrieved,
            jurisdiction=state.jurisdiction,
        )
        return pack


# Global singleton
rag_pipeline = RAGPipeline()
