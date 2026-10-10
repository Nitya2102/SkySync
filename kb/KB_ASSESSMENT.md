# KB Assessment (as of 2026-10-07)

## v2 audit (uploaded package)
| dimension | finding | score /5 |
|---|---|---|
| Structure & schema | Strong: hybrid graph+RAG design, reliability classes, answer contract, sim/authority separation | 4.5 |
| Source selection | Good: 36 tier-1 sources matching the brief | 4 |
| Content depth | Weak: 42 claims are mostly "document X exists / covers Y". **Zero numeric thresholds** (no dBm, MHz limits, margins, distances, dates) | 1.5 |
| Provenance | Weak: no section/page, no retrieval date, no verification flag; 12 of 36 sources cited by no claim; 14 one-sentence chunks | 2 |
| Temporal correctness | Defect: India AIC 19/2025 limitations stated without effective date (2027-12-31, i.e. NOT yet in force) | 1.5 |
| Conflict handling | Declared in rules but no conflicts stored | 2 |
| Agent usability | Arbitration/Spectrum/Airspace could not compute or rule on anything; no constraints | 1.5 |
| Edition hygiene | Annex 10 Vol V: URL says Amendment 90, claim says 91 | flagged |
**Verdict:** excellent skeleton, too thin to demo decision-making. Not wrong, mostly *empty*, plus one temporal error.

## v3 changes
- +47 claims with locators (FAA final rule full text, AIC 19/2025 Appendices A/B full text, ECC 362 conclusions, ITU RR 5.438/4.10, 3GPP bands & 28.541/28.552 objects).
- Every new claim carries verification level; tier-3 press claims are marked and cannot back HARD constraints.
- 14 constraints, 5 retained conflicts, institution graph, 10 gaps, demo scenario, BM25 retriever, validator.
- Stale v2 chunk CHK-006 down-ranked and flagged as superseded.

## Honest limits (do not over-claim in the demo)
1. ICAO documents (guidance MID-Doc-015, NACC papers) are bot-blocked: only slide/snippet-level ICAO evidence. 
2. FCC Upper C-band R&O not fetched; its numbers come via the FAA rule (primary-by-citation).
3. FAA rule fetch truncated in section IV.E: later sections, regulatory text and cost analysis unread.
4. India: no primary text for airport-area 5G restrictions, NFAP-2025 band table, or Telecom Act sections beyond v2 metadata. India's 3300-3670 MHz band rests on tier-3 press -> verify.
5. 3GPP items come from mirrors/CR drafts; TS 23.501/23.502 content not ingested; no tilt/beam actuation evidence.
6. Retrieval is lexical BM25 (no embeddings) - fine for ~120 documents; swap in a vector index for scale.
7. The US ITM numbers are a benchmark only; they are not an Indian legal requirement (GAP-007).
