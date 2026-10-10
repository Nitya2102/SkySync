"""Test KB integrity using validate.py rules."""
import csv
import json
import os
from pathlib import Path
from app.config import KB_DIR


def test_kb_sources_exist():
    src_file = KB_DIR / "sources.csv"
    assert src_file.exists(), "sources.csv missing"
    with open(src_file, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) > 0, "sources.csv is empty"
    source_ids = {r["source_id"] for r in reader}
    assert "SRC-FAA-FR-2026-15585" in source_ids


def test_kb_claims_validity():
    src_file = KB_DIR / "sources.csv"
    with open(src_file, encoding="utf-8") as f:
        src = {r["source_id"]: r for r in csv.DictReader(f)}

    claims_file = KB_DIR / "claims.jsonl"
    assert claims_file.exists(), "claims.jsonl missing"

    claims = [json.loads(line) for line in open(claims_file, encoding="utf-8")]
    assert len(claims) >= 80, f"Expected at least 80 claims, found {len(claims)}"

    ids = {c["claim_id"] for c in claims}
    assert len(ids) == len(claims), "Duplicate claim IDs found in claims.jsonl"

    for c in claims:
        assert c["source_id"] in src, f"Unknown source {c['source_id']} in claim {c['claim_id']}"
        if not c.get("legacy"):
            for f in ("locator", "verification", "legal_status", "jurisdiction"):
                assert c.get(f), f"Claim {c['claim_id']} missing required field {f}"
            assert len(c["claim"].split()) >= 8, f"Claim {c['claim_id']} too short"


def test_kb_agent_coverage():
    claims_file = KB_DIR / "claims.jsonl"
    claims = [json.loads(line) for line in open(claims_file, encoding="utf-8")]

    required_agents = [
        "network",
        "airspace_safety",
        "spectrum",
        "policy_institutional",
        "optimization",
        "arbitration",
    ]
    for agent in required_agents:
        non_legacy = sum(1 for c in claims if agent in c.get("agents", []) and not c.get("legacy"))
        assert non_legacy >= 5, f"Agent {agent} has insufficient non-legacy claims: {non_legacy}"
