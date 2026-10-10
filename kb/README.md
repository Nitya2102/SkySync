# 5G-Airspace Coexistence & Safety KB v3 (MVP demo)

Built 2026-10-07 from v2 + live research. Run `python3 validate.py` (integrity) and `python3 kb_retriever.py "<query>"` (retrieval).

| file | content |
|---|---|
| sources.csv | 53 sources with verification level, retrieval date, access notes |
| claims.jsonl | 89 claims (47 new quantitative/locator-bearing; 42 legacy existence-level, re-tagged) |
| rag_chunks.jsonl | status-stamped chunks (jurisdiction, claim IDs, agents) |
| constraints.json | 14 machine-checkable constraints (HARD/SOFT/ADVISORY/UNKNOWN) with legal_status + effective date |
| conflicts.json | 5 retained disagreements (ECC362 vs EASA/aviation, India DGCA framing, MSD, ITM altitude...) |
| graph.json | institutions + responsibility edges (incl. an explicitly undocumented DoT-WPC <-> DGCA interface) |
| policy_gaps.json | 10 gaps/ingestion limits |
| scenario_seed.json | SIMULATION fixture (never authoritative) for the end-to-end demo |
| KB_ASSESSMENT.md | v2 audit + v3 results |

Rules: FACT only from sources; INFERENCE exposes supporting IDs; SIMULATION kept out of claims; always compare `legal_status` / `effective_from` with `as_of`.
