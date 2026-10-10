"""RAG gold-set evaluation ensuring recall@6 >= 0.85."""
import json
from pathlib import Path
from app.rag.hybrid_retriever import hybrid_retriever


def test_rag_gold_evaluation():
    gold_path = Path(__file__).parent / "rag_gold.json"
    assert gold_path.exists(), "rag_gold.json not found"

    with open(gold_path, encoding="utf-8") as f:
        benchmarks = json.load(f)

    hybrid_retriever.load()
    hits = 0
    total = len(benchmarks)

    print("\n--- RAG Gold Set Evaluation ---")
    for b in benchmarks:
        query = b["query"]
        expected = set(b["expected_claims"])
        agent = b.get("agent")
        jurisdiction = b.get("jurisdiction")

        results = hybrid_retriever.search(
            query=query,
            agent=agent,
            jurisdiction=jurisdiction,
            top_k=6,
        )

        retrieved_ids = set()
        for r in results:
            retrieved_ids.add(r["id"])
            for eid in r.get("evidence_ids", []):
                retrieved_ids.add(eid)

        matched = expected & retrieved_ids
        if matched:
            hits += 1
            print(f"[PASS] Query: '{query[:40]}...' -> matched {matched}")
        else:
            print(f"[FAIL] Query: '{query[:40]}...' -> expected {expected}, retrieved {list(retrieved_ids)[:6]}")

    recall_at_6 = hits / total
    print(f"Recall@6: {recall_at_6:.2f} ({hits}/{total})")
    assert recall_at_6 >= 0.85, f"Recall@6 {recall_at_6:.2f} is below target 0.85"
