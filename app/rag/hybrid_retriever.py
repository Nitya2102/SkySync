"""Hybrid retriever combining BM25, semantic embeddings, and Reciprocal Rank Fusion (RRF).

Includes:
- BM25 ranker over rag_chunks and decision-relevant claims
- Dense semantic vector search via EmbeddingManager (when available)
- Reciprocal Rank Fusion (RRF) with configurable k (default 60)
- Metadata adjustments:
    * secondary_report weighted 0.6
    * legacy claims weighted 0.5
    * superseded claims weighted 0.3
    * authority tiers: tier 1 = 1.0, tier 2 = 0.9, tier 3 = 0.6
- Jurisdiction and agent domain filtering
"""
from __future__ import annotations

import collections
import json
import logging
import math
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np

from app.config import KB_DIR
from app.rag.embeddings import embedding_manager

logger = logging.getLogger(__name__)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9\.\-]+", text.lower())


class Document:
    def __init__(self, doc_id: str, kind: str, text: str, meta: dict[str, Any]):
        self.doc_id = doc_id
        self.kind = kind  # "chunk" or "claim"
        self.text = text
        self.meta = meta
        self.tokens = tokenize(text)


class HybridRetriever:
    """Indexed Knowledge Base with hybrid BM25 and dense vector retrieval."""

    def __init__(self, kb_dir: Path = KB_DIR):
        self.kb_dir = kb_dir
        self.docs: list[Document] = []
        self.claims_by_id: dict[str, dict[str, Any]] = {}
        self.chunks_by_id: dict[str, dict[str, Any]] = {}
        self.constraints: list[dict[str, Any]] = []
        self.conflicts: list[dict[str, Any]] = []
        self.gaps: list[dict[str, Any]] = []

        # BM25 stats
        self.doc_count = 0
        self.avg_doc_len = 0.0
        self.doc_freq: collections.Counter = collections.Counter()

        # Dense vectors
        self.doc_vectors: Optional[np.ndarray] = None
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return

        # 1. Load raw files
        chunks_file = self.kb_dir / "rag_chunks.jsonl"
        claims_file = self.kb_dir / "claims.jsonl"
        cons_file = self.kb_dir / "constraints.json"
        conf_file = self.kb_dir / "conflicts.json"
        gaps_file = self.kb_dir / "policy_gaps.json"

        raw_chunks = [json.loads(line) for line in open(chunks_file, encoding="utf-8")]
        raw_claims = [json.loads(line) for line in open(claims_file, encoding="utf-8")]

        self.chunks_by_id = {c["chunk_id"]: c for c in raw_chunks}
        self.claims_by_id = {c["claim_id"]: c for c in raw_claims}

        if cons_file.exists():
            self.constraints = json.loads(cons_file.read_text(encoding="utf-8"))["constraints"]
        if conf_file.exists():
            self.conflicts = json.loads(conf_file.read_text(encoding="utf-8"))
        if gaps_file.exists():
            self.gaps = json.loads(gaps_file.read_text(encoding="utf-8"))

        # 2. Build searchable documents
        # Chunks
        for c in raw_chunks:
            self.docs.append(Document(doc_id=c["chunk_id"], kind="chunk", text=c["text"], meta=c))

        # Claims (exclude pure legacy without substance if needed, or include with penalty)
        for c in raw_claims:
            claim_text = f"{c['claim']} {c.get('object', '')}"
            self.docs.append(Document(doc_id=c["claim_id"], kind="claim", text=claim_text, meta=c))

        # 3. Precompute BM25 statistics
        self.doc_count = len(self.docs)
        if self.doc_count > 0:
            total_tokens = sum(len(d.tokens) for d in self.docs)
            self.avg_doc_len = total_tokens / self.doc_count
            for d in self.docs:
                unique_tokens = set(d.tokens)
                for t in unique_tokens:
                    self.doc_freq[t] += 1

        self._loaded = True
        logger.info("HybridRetriever loaded %d documents (%d chunks, %d claims)", self.doc_count, len(raw_chunks), len(raw_claims))

    def _bm25_score(self, query_tokens: list[str], doc: Document, k1: float = 1.4, b: float = 0.75) -> float:
        tf = collections.Counter(doc.tokens)
        doc_len = len(doc.tokens)
        score = 0.0
        for token in query_tokens:
            if token in tf:
                df = self.doc_freq.get(token, 0)
                # Robertson-Spärck Jones IDF
                idf = math.log(1.0 + (self.doc_count - df + 0.5) / (df + 0.5))
                freq = tf[token]
                term_score = idf * (freq * (k1 + 1.0)) / (freq + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len)))
                score += term_score
        return score

    def _apply_metadata_weights(self, base_score: float, doc: Document) -> float:
        score = base_score
        meta = doc.meta

        # Legacy penalty
        if meta.get("legacy"):
            score *= 0.5

        # Superseded penalty
        if meta.get("superseded_by"):
            score *= 0.3

        # Claim verification penalty/boost
        if doc.kind == "claim":
            verification = meta.get("verification", "")
            if verification == "fetched_full_text_primary":
                score *= 1.15
            elif verification == "search_snippet_primary":
                score *= 1.0
            elif verification == "secondary_report":
                score *= 0.6
            else:
                score *= 0.9
        else:
            # Chunk authority tier
            tier = meta.get("authority_tier", 1)
            if tier == 1:
                score *= 1.0
            elif tier == 2:
                score *= 0.9
            elif tier == 3:
                score *= 0.6
            else:
                score *= 0.8

        return score

    def search(
        self,
        query: str,
        agent: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        top_k: int = 6,
        rrf_k: int = 60,
    ) -> list[dict[str, Any]]:
        """Perform hybrid retrieval using BM25 and semantic search with RRF."""
        if not self._loaded:
            self.load()

        q_tokens = tokenize(query)

        # 1. Candidate filtering & BM25 scoring
        bm25_candidates = []
        eligible_indices = []

        for i, doc in enumerate(self.docs):
            m = doc.meta

            # Agent filter
            if agent and m.get("agents"):
                if agent not in m["agents"]:
                    continue

            # Jurisdiction filter
            doc_jurisdiction = m.get("jurisdiction", "")
            if jurisdiction and doc_jurisdiction not in ("", "n/a"):
                j_lower = doc_jurisdiction.lower()
                target_j = jurisdiction.lower()
                if target_j not in j_lower and "international" not in j_lower:
                    continue

            eligible_indices.append(i)
            raw_bm25 = self._bm25_score(q_tokens, doc)
            if raw_bm25 > 0:
                weighted_bm25 = self._apply_metadata_weights(raw_bm25, doc)
                bm25_candidates.append((i, weighted_bm25))

        # Sort BM25 results
        bm25_candidates.sort(key=lambda x: x[1], reverse=True)
        bm25_ranks = {doc_idx: rank for rank, (doc_idx, _) in enumerate(bm25_candidates)}

        # 2. Semantic search (if embedding_manager is active)
        semantic_ranks = {}
        if embedding_manager.is_available and eligible_indices:
            q_vec = embedding_manager.encode_query(query)
            if q_vec is not None:
                # Precompute doc vectors if not yet built
                if self.doc_vectors is None:
                    texts = [self.docs[idx].text for idx in range(len(self.docs))]
                    encoded = embedding_manager.encode(texts)
                    if encoded is not None:
                        self.doc_vectors = encoded

                if self.doc_vectors is not None:
                    # Dot product / cosine similarity
                    sub_vectors = self.doc_vectors[eligible_indices]
                    sims = np.dot(sub_vectors, q_vec)
                    # Pair with original doc indices
                    semantic_scored = []
                    for sim, orig_idx in zip(sims, eligible_indices):
                        doc = self.docs[orig_idx]
                        w_sim = self._apply_metadata_weights(float(sim), doc)
                        semantic_scored.append((orig_idx, w_sim))
                    semantic_scored.sort(key=lambda x: x[1], reverse=True)
                    semantic_ranks = {doc_idx: rank for rank, (doc_idx, _) in enumerate(semantic_scored)}

        # 3. Reciprocal Rank Fusion (RRF)
        all_candidates = set(bm25_ranks.keys()) | set(semantic_ranks.keys())
        rrf_scores = []

        for doc_idx in all_candidates:
            score = 0.0
            if doc_idx in bm25_ranks:
                score += 1.0 / (rrf_k + bm25_ranks[doc_idx])
            if doc_idx in semantic_ranks:
                score += 1.0 / (rrf_k + semantic_ranks[doc_idx])
            rrf_scores.append((doc_idx, score))

        rrf_scores.sort(key=lambda x: x[1], reverse=True)

        # 4. Format results
        results = []
        seen_ids = set()

        for doc_idx, rrf_score in rrf_scores[:top_k]:
            doc = self.docs[doc_idx]
            if doc.doc_id in seen_ids:
                continue
            seen_ids.add(doc.doc_id)

            meta = doc.meta
            evidence_ids = meta.get("claim_ids", [doc.doc_id] if doc.kind == "claim" else [])

            # Associated constraints
            matched_constraints = [
                c["constraint_id"]
                for c in self.constraints
                if set(c.get("evidence_claims", [])) & set(evidence_ids)
            ]

            # Associated conflicts
            matched_conflicts = [
                c["conflict_id"]
                for c in self.conflicts
                if any(set(pos.get("claims", [])) & set(evidence_ids) for pos in c.get("positions", []))
            ]

            # Warnings
            warnings = []
            if meta.get("superseded_by"):
                warnings.append(f"SUPERSEDED by {meta['superseded_by']}")

            for cid in matched_constraints:
                con = next((c for c in self.constraints if c["constraint_id"] == cid), None)
                if con:
                    legal_status = con.get("legal_status", "")
                    if "not_yet" in legal_status.lower():
                        warnings.append(f"{cid} is NOT_YET_IN_FORCE (effective {con.get('effective_from')})")
                    elif legal_status in ("evidence_gap", "inference", "voluntary_non_binding"):
                        warnings.append(f"{cid} legal status is {legal_status}")

            results.append({
                "id": doc.doc_id,
                "kind": doc.kind,
                "score": round(rrf_score, 4),
                "text": doc.text[:220],
                "evidence_ids": evidence_ids,
                "constraints": matched_constraints,
                "conflicts": matched_conflicts,
                "warnings": warnings,
                "jurisdiction": meta.get("jurisdiction", ""),
                "legal_status": meta.get("legal_status", ""),
                "effective_from": meta.get("effective_from"),
                "numeric": meta.get("numeric", {}),
            })

        return results


# Global singleton
hybrid_retriever = HybridRetriever()
