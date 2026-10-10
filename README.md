# SkySync: A Policy-Grounded Safety Gateway for 5G and Aerodrome-Corridor Coexistence
[Team SNR proposal](https://docs.google.com/document/d/1R2OOkgjofgddBhkbVAP43HQoeG9p73uM/edit?usp=sharing&ouid=113427882934277576490&rtpof=true&sd=true)
[Demo video](https://drive.google.com/file/d/1vowyXtQ0W5zpVqmdMmZQT2trbwVQg_aH/view?usp=sharing)
[Knowledge base description](https://docs.google.com/document/d/1OKRAIhRJaPcJHHKCQFy9cDT35K6sCphDkspXb6X5k7g/edit?usp=sharing)


**ITU AI for Good Sandbox Build-a-thon 5.0**  
**Host Country:** India | **Track:** Telecommunications (5G and Aviation Spectrum Coexistence)  

> **System Notice**: All scenario, airport, aircraft, and cell telemetry data used within this system are strictly synthetic and generated for sandbox evaluation purposes. Every safety margin and propagation calculation is explicitly labelled `[SIMULATION]`.

---

## 1. Executive Summary

### 1.1 Problem Statement
Modern dense 5G cellular deployments (specifically C-band / n78 / n77) operating in proximity to aerodrome arrival and departure corridors face severe operational tensions. Consider a 5G gNodeB cell adjacent to an aerodrome: physical resource block (PRB) utilization reaches 94%, leading to a 38% collapse in user throughput. The standard radio resource management (RRM) mitigation is to boost transmission power.

However, in the airspace corridor directly above that base station, an incoming aircraft on final approach relies on its radio altimeter operating in the aeronautical radionavigation band (4200–4400 MHz). This instrument provides direct height-above-ground measurements feeding flight-critical avionics: CAT II/III autoland systems, the Ground Proximity Warning System (GPWS/TAWS), and Traffic Alert and Collision Avoidance Systems (TCAS). Corrupted altimeter readings or undetected front-end overload can produce silent catastrophic failures during low-visibility approach operations. 

Currently, no machine-readable interface connects cellular network operations (RAN OAM) to aerodrome air traffic management (ATM), dynamic spectrum rules, or regulatory civil aviation authorities. When network congestion occurs near an airport, cellular controllers lack aeronautical context, while aviation safety buffers remain static and rigid.

### 1.2 The SkySync Solution
SkySync is a deterministic, policy-grounded decision-support gateway positioned between cellular network optimization requests and live base station actuators. Rather than delegating critical decisions to an opaque model, SkySync employs a multi-agent domain swarm with deterministic gatekeeping:
- Four specialized domain agents (**Network**, **Airspace Safety**, **Spectrum**, and **Policy & Institutional**) evaluate the live situational snapshot concurrently from their respective regulatory mandates.
- An **Optimization Agent** performs multi-objective Pareto ranking across candidate mitigation actions (evaluating safety margin, QoS retention, actuation latency, and regulatory overhead).
- A **Deterministic Constraint Engine** (the Policy Node) checks each candidate action against formal machine-encoded legal, physical, and regulatory rules.
- The system returns one of four formal verdicts: `ACCEPT`, `REJECT`, `PENDING`, or `ESCALATE`.
- Every evaluated parameter, agent rationale, citation identifier, and constraint verdict is cryptographically hashed and recorded into an immutable audit ledger.

### 1.3 Technical Defensibility
Safety in SkySync is enforced by deterministic code, never by probabilistic neural generation. Large Language Models (LLMs) are restricted to unstructured information retrieval, synthetic scenario reasoning, and human-readable explanation generation. Crucially:
1. An LLM can never overrule a failed deterministic constraint.
2. If any telemetry parameter or regulatory variable is missing or ambiguous (e.g., unknown base station EIRP), the system evaluates the parameter as `UNKNOWN`.
3. Under the Precautionary Principle, `UNKNOWN` triggers a deterministic safety block (`REJECT` or `ESCALATE`).
4. Removing all language models leaves the gateway functioning identically as a rule-based safety interlock.

### 1.4 Hierarchical Authority Model
SkySync categorizes all regulatory rules into explicit legal authority tiers:
- **In Force**: Binding statutory regulations and published airworthiness directives currently active.
- **Published / Not Yet in Force**: Regulatory circulars with defined future compliance dates (e.g., DGCA AIC 19/2025, which takes mandatory effect on 31 December 2027).
- **Voluntary / Non-Binding**: Operator commitments, manufacturer advisories, or consultative guidelines.
- **Analysis Parameter**: Engineering baselines and technical study recommendations (e.g., the international 6 dB safety buffer from ICAO Doc 9718).

SkySync evaluates every rule against a temporal scenario parameter (`as_of_date`). It enforces law as law, treats future rules according to their active timeline, and never elevates non-binding guidance into statutory mandates.

---

## 2. Team & Project Information

- **Nitya P Mohare** (Team Leader), Department of Computer Science & Engineering, R V College of Engineering
- **Shrirang Pai**, Department of Computer Science & Engineering, R V College of Engineering
- **Faculty Mentor**: Dr. K A Nethravathi, Department of Computer Science & Engineering, R V College of Engineering

### Submission Artifacts
- **Code Repository**: [https://github.com/Nitya2102/SkySync](https://github.com/Nitya2102/SkySync)
- **Structured Knowledge Base**: [https://github.com/Nitya2102/SkySync/tree/main/kb](https://github.com/Nitya2102/SkySync/tree/main/kb)
- **Contact**: `nityapmohare.cs23@rvce.edu.in`, `paishrirang@gmail.com`

---

## 3. Compliance with Judging Criteria

| Judging Criterion | Architectural Evidence & Implementation | Reference Section |
| :--- | :--- | :--- |
| **Knowledge Base Quality** | 53 authoritative sources, 89 atomic claims, 17 formal constraints, 5 retained conflicts, and 10 catalogued gaps. Every claim indexes primary source locators, authority tiers, and legal status. | Section 7 |
| **Agent Swarm Capability** | Four domain-specific agents, a multi-objective Pareto optimizer, and deterministic arbitration. Validated across three complex operational scenarios (`DEMO-001`, `DEMO-002`, `DEMO-003`). | Section 5, Section 10 |
| **Policy & Standards Gaps** | Identification of 4 Standards Gaps (SG-1 to SG-4) and 3 Policy Gaps (PG-1 to PG-3), mapped against international precedents in the US, Europe, Canada, and ICAO. | Section 8 |
| **Auditability & Traceability** | Per-execution JSON audit ledger capturing raw telemetry snapshots, retrieved claim identifiers, agent assessments, constraint evaluation tables, and final verdicts. | Section 6.3 |
| **Alignment with ITU Standards** | Formal structural mapping to ITU-T Recommendation Y.3172; verified coverage across 5 core ITU AI Readiness dimensions. | Section 5, Section 9 |

---

## 4. Problem Formulation & Operational Baseline

### 4.1 Operational Scenario
A congested base station and an incoming aircraft occupy overlapping physical and electromagnetic environments:
- The telecommunications operator requires capacity relief to maintain Quality of Service (QoS).
- The aircraft requires an uncorrupted radio altimeter band (4200–4400 MHz) with its protective interference threshold intact.
- The fundamental engineering problem is determining which dynamic cellular reconfiguration delivers optimal throughput while maintaining provable, compliance-verified aeronautical safety.

Existing telecommunication management systems operate in isolation from civil aviation infrastructure. Spectrum managers rely on static administrative buffers, which creates an efficiency dilemma: safe actions are unnecessarily blocked, while hazardous reconfigurations cannot be dynamically flagged.

### 4.2 State of the Art Comparison

| Paradigm | Operational Capability | Remaining Vulnerability / Gap |
| :--- | :--- | :--- |
| **Static Exclusion Zones (US FAA / FCC)** | Enforces geographical buffer zones and fixed EIRP caps around runways. | Inelastic: cannot adapt to real-time aircraft presence, actual flight altitude, landing category, or temporary cell load. |
| **Avionics Retrofit Mandates (FAA ADs, DGCA AIC 19/2025)** | Requires airlines to install band-pass RF filters and hardened radio altimeters. | Solves only the receiver side. India's AIC 19/2025 defines tolerance qualitatively with enforcement delayed until 31 Dec 2027. |
| **Coexistence Studies (CEPT ECC Report 362)** | Quantifies power flux density (PFD) thresholds and guard-band requirements. | Purely analytical study output; provides no real-time actuation or network gateway protocol. |
| **Unconstrained LLM Prompting** | Evaluates situational text and suggests network parameter changes in natural language. | Prone to hallucinations, invents safety margins, conflates guidance with law, and provides zero deterministic guarantees. |

### 4.3 Verdict Taxonomy: The Case for Escalation
SkySync rejects binary accept/reject models. An optimization action that cannot be immediately proven safe may still represent a viable operational alternative under supervisory oversight:

- **`[ACCEPT]`**: All deterministic hard constraints pass with verified mathematical headroom. Safe for automated simulation actuation.
- **`[PENDING]`**: Conditionally acceptable, but an operational precondition (e.g., active base station antenna calibration) has expired and must be refreshed.
- **`[ESCALATE]`**: Requires explicit human authorization. Triggered during CAT III blind landing conditions, regulatory policy gaps, or missing telemetry.
- **`[REJECT]`**: A fundamental physical or statutory constraint has failed (e.g., transmission outside licensed spectrum bounds). The action is aborted with no internal override pathway.

---

## 5. System Architecture: ITU-T Y.3172 Alignment

SkySync implements the functional architecture specified in **ITU-T Recommendation Y.3172** ("Architectural framework for machine learning in future networks including IMT-2020").

```
  +---------------------------------------------------------------------------------+
  |                             ITU-T Y.3172 PIPELINE                               |
  |                                                                                 |
  |  [SRC] --------> [C] --------> [PP] --------> [M] --------> [P] ------> [D]    |
  |  Sources      Collection   Preprocess     Model Swarm     Policy     Actuation  |
  |                                                    ^        |           |       |
  |                                                    |        v           v       |
  |                                            Knowledge Base (KB)       [SINK]     |
  |                                            Deterministic Engine      Ledger     |
  +---------------------------------------------------------------------------------+
```

### 5.1 ITU-T Y.3172 Node Mapping

| Y.3172 Logical Node | Standard Definition | SkySync Implementation |
| :--- | :--- | :--- |
| **Intent** | Operational objective driving the pipeline | Congestion mitigation without degrading aeronautical radionavigation safety buffers. |
| **SRC (Data Sources)** | Raw data generation endpoints | Synthetic ADS-B telemetry, runway state, cell PRB/EIRP state, regulatory KB corpus. |
| **C (Collection)** | Ingestion and transport layer | Real-time Server-Sent Events (SSE) telemetry streamer and local KB index loader. |
| **PP (Preprocessing)** | Data normalization and cleaning | Temporal alignment of aircraft 3D position, slant range, PRB load, and antenna azimuth into a unified state snapshot. |
| **M (Model)** | AI/ML processing components | LangGraph multi-agent swarm: Network, Airspace Safety, Spectrum, Policy, Optimization, and Arbitration. |
| **P (Policy Node)** | Rule-based governance and constraints | Deterministic Constraint Engine and Mathematical Margin Simulator (Pure Python, zero LLM dependency). |
| **D (Distribution)** | Actuator delivery interface | Mitigation actuation pipeline (simulated in MVP) attaching verified Claim IDs and ledger signatures. |
| **SINK** | Output target system | JSON Audit Ledger and interactive human-in-the-loop Operator Console. |
| **Inference Target** | Execution environment | Backend orchestration runtime (Python 3.11 / FastAPI). |
| **Sandbox Pipeline** | Offline evaluation sandbox | Isolated simulation sandbox incorporating synthetic aircraft trajectories and propagation models. |

### 5.2 Multi-Phase Decision Flow
1. **Phase 0 (Ingestion & Normalization)**: Ingests aircraft 3D vectors $(x, y, z)$, velocity, landing category, and gNodeB cell parameters into a normalized snapshot.
2. **Phase 1 (Parallel Swarm Assessment)**: Four domain agents evaluate the snapshot simultaneously in isolated execution environments to prevent premature consensus bias.
3. **Phase 2 (Multi-Objective Optimization)**: The Optimization Agent ranks proposed candidate actions via Pareto trade-off analysis across four dimensions: safety margin (dB), QoS retention (%), actuation latency (ms), and regulatory risk.
4. **Phase 2.5 (Deterministic Policy Evaluation)**: The Policy Node executes formal constraint checks against all candidate actions. Every applicable constraint yields `PASS`, `FAIL`, or `UNKNOWN`.
5. **Phase 3 (Arbitration & Audit Logging)**: The Arbitration Node finalizes the execution verdict. While the LLM synthesizes natural-language explanations, it is architecturally incapable of overriding any constraint failure. The transaction is written to disk in the audit ledger.

---

## 6. The Policy Node & Safety Engineering

### 6.1 Design Principles
1. **Zero Neural Logic in Safety Gates**: Safety decisions evaluate explicit Python boolean expressions over cited quantitative thresholds. The identical input state will deterministically yield the identical verdict across all runs.
2. **Deterministic Identifier Grounding**: Every rule and constraint explicitly references immutable Knowledge Base claim identifiers (e.g., `CON-RAD-001` references `CLM-106` and `CLM-109`). Citations cannot drift based on semantic phrasing.
3. **The Precautionary Principle**: If an input variable is absent or telemetry is corrupted, the system evaluates the parameter as `UNKNOWN`. In SkySync's policy logic, `UNKNOWN` triggers a fail-safe stop (`REJECT` or `ESCALATE`).

### 6.2 The Evidence Guard
The Evidence Guard operates as an active safety filter:
- **Hallucination Interception**: Any claim identifier cited by an LLM that does not exist in the authoritative Knowledge Base is stripped and logged as an integrity violation.
- **Temporal Validity Checking**: Claims or regulations whose `effective_from` timestamp is subsequent to the scenario `as_of_date` are flagged as `NOT_YET_IN_FORCE` and prevented from triggering hard statutory blocks.
- **Authority Tier Downgrades**: Secondary literature or trade press (Tier 3) can generate advisory warnings, but can never satisfy the evidentiary threshold required for a hard constraint rejection.
- **Conflict Preservation**: If authoritative sources diverge (e.g., `CONF-001`), the guard surfaces both positions rather than synthesizing an artificial arithmetic average.

### 6.3 Mathematical Safety Margin Computation
The Margin Simulator evaluates conservative line-of-sight free-space Power Flux Density (PFD) at the 3D slant range:

$$\text{PFD} \, (\text{dBW/m}^2/\text{MHz}) = (\text{EIRP}_{\text{per\_pol}} - 30) - 10 \cdot \log_{10}(4\pi d^2)$$

$$\text{Margin} \, (\text{dB}) = \text{Threshold} - (\text{PFD} + \text{Aggregation})$$

$$\text{Constraint CON-RAD-001}: \text{Margin} \ge 6 \, \text{dB}$$

Where:
- $d$ is the 3D Euclidean slant distance between the gNodeB antenna phase center and the aircraft radio altimeter antenna.
- $\text{EIRP}_{\text{per\_pol}}$ represents equivalent isotropically radiated power per polarization in dBm/MHz (e.g., a 65 dBm/MHz dual-polarized array corresponds to 62 dBm/MHz per polarization).
- The 6 dB margin is applied strictly as an external pass/fail constraint, not embedded as a hidden offset inside the physical equation.
- Aircraft interference tolerance thresholds are loaded from KB masks: **9.5 dBW/m²/MHz** for adjacent-band C-band energy and **-82 dBW/m²/MHz** for in-band spurious emissions into 4200–4400 MHz (derived from FAA Interference Tolerance Mask specifications).

*Validation*: Benchmarked against the FAA final rule example (35 ft / 10.67 m separation distance), the simulation computes an adjacent-band PFD of 0.38 dBW/m²/MHz (reproducing the FAA published benchmark of ~0.4 dBW/m²/MHz within 0.02 dB).

---

## 7. Authoritative Knowledge Base

SkySync's Knowledge Base is a version-controlled, relational knowledge graph and retrieval corpus designed to eliminate unstructured hallucination.

```
  [SOURCES: 53] ---> [CLAIMS: 89] ---> [CONSTRAINTS: 17]
         |                  |                    |
         v                  v                    v
  [CHUNKS: 30]       [CONFLICTS: 5]        [GAPS: 10]
                            |
                            v
                     [GRAPH: 13 Nodes]
```

### 7.1 Schema Composition

| Entity Layer | Cardinality | Structural Description |
| :--- | :--- | :--- |
| **Sources** | 53 records | Authoritative documents catalogued with publishing body, authority tier (1 to 3), jurisdiction, official URL, and verification level. |
| **Claims** | 89 records | Atomic, falsifiable factual assertions. Each claim records primary locators (section/table), legal status, effective dates, and numeric parameters. |
| **Chunks** | 30 records | Text passages for hybrid retrieval, bound to verified claim IDs. Superseded and legacy chunks carry mathematical down-weighting. |
| **Constraints** | 17 records | Formal programmatic rules classified as `HARD`, `SOFT`, `ADVISORY`, `INFORMATIONAL`, or `PRECAUTIONARY`. |
| **Conflicts** | 5 records | Documented disagreements between standard bodies (e.g., CEPT ECC vs. RTCA), preserved without averaging. |
| **Gaps** | 10 records | Specific omissions in current national policies and telecommunication standards. |
| **Graph** | 13 nodes | Entity-relationship graph mapping international and Indian regulatory bodies and coordination interfaces. |

### 7.2 Evidence Verification Breakdown

| Verification Level | Claim Count | Description |
| :--- | :--- | :--- |
| **Full Primary Text** | 25 | Ingested and verified against complete official statutory or technical publications. |
| **Primary Search Snippet** | 19 | Verified against official document snippets directly retrieved from authoritative repositories. |
| **Secondary / Press** | 3 | Sourced from credible technical journalism; restricted to advisory status. |
| **Legacy Baseline** | 40 | Catalogued foundational claims preserved from baseline coexistence analyses. |

### 7.3 Hybrid Retrieval Architecture
SkySync utilizes Reciprocal Rank Fusion (RRF) combining sparse BM25 lexical search with dense semantic retrieval (`sentence-transformers/bge-small-en-v1.5`). Search results are filtered by agent domain and jurisdiction, and weighted by authority tier:
- Tier 1 Primary Full Text: Multiplier 1.15
- Tier 2 Official Working Papers: Multiplier 1.00
- Tier 3 Secondary Reports: Multiplier 0.60
- Legacy Claims: Multiplier 0.50
- Superseded Guidance: Multiplier 0.30

---

## 8. Policy & Standards Gaps Analysis

Through synthesis of Indian, North American, European, and ICAO regulatory frameworks, SkySync identifies 7 critical structural gaps:

### 8.1 Telecommunications Standards Gaps

| Identifier | Gap Title | Operational Consequence | Proposed Standard Direction |
| :--- | :--- | :--- | :--- |
| **SG-1** (GAP-001) | Absence of Real-Time RAN-to-ATM Interface | Neither DoT-WPC nor civil aviation bodies offer a machine-readable coordination API; base station managers cannot query active runway corridors. | Standardize an open, low-latency coordination interface between 3GPP RAN OAM and ATM systems. |
| **SG-2** (GAP-002) | Missing Authorization Hooks in 3GPP Specifications | 3GPP TS 28.541 specifies antenna management objects but lacks hooks for aeronautical safety interlocks or exclusion boundary triggers. | Introduce safety-gate profiles into 3GPP 28-series specifications for cells within defined aerodrome buffers. |
| **SG-3** (GAP-007) | Qualitative Rather Than Quantitative National Masks | DGCA AIC 19/2025 provides qualitative descriptions of altimeter tolerance without publishing numeric spectral masks. | Publish explicit Power Flux Density tolerance curves aligned with ITU-R M.2059. |
| **SG-4** (GAP-010) | Uncharacterized Beam-Adjustment Control Latency | Actuation latency for dynamic downtilt and beamforming adjustments near aerodromes is undocumented in public profiles. | Standardize and benchmark maximum control loop actuation latencies in 3GPP operational profiles. |

### 8.2 National & International Policy Gaps

| Identifier | Gap Title | Operational Consequence | Proposed Policy Direction |
| :--- | :--- | :--- | :--- |
| **PG-1** (GAP-003) | Divergent International Compliance Timelines | US mandates take effect between 2030 and 2034; India's AIC 19/2025 takes effect 31 Dec 2027; Europe relies on voluntary measures. | Harmonize altimeter tolerance timelines through ICAO Assembly resolutions. |
| **PG-2** (GAP-006) | Uncodified Geographic Exclusion Zone Coordinates | Interim aerodrome exclusion zones in India are referenced in press releases without published boundary polygons in official gazettes. | Formally gazette exact latitude/longitude coordinate boundaries and vertical profiles for all civil aerodromes. |
| **PG-3** | Undefined Liability for Autonomous Spectrum Actions | When an automated AI controller triggers a power or spectrum shift impacting an airspace corridor, legal accountability is undefined. | Mandate human-in-the-loop sign-off for dynamic power increases in aerodrome buffers, backed by immutable audit trails. |

*Institutional Finding*: In India, the Department of Telecommunications (DoT-WPC) and the Directorate General of Civil Aviation (DGCA) govern separate halves of this boundary. The institutional coordination interface between them remains uncodified (`graph.json` edge: `COORDINATION_INTERFACE_UNDOCUMENTED`).

### 8.3 Global Policy Benchmarking

| Jurisdiction | Regulatory Instrument | Key Provisions | Comparative Assessment |
| :--- | :--- | :--- | :--- |
| **United States** | FAA Final Rule (FR 2026-15585) | Mandates altimeter retrofit tolerance by 2030 (Part 121) and 2034. Regulates aircraft airworthiness, not telecom emissions. | Solves the receiver side through legal mandate; establishes explicit tolerance mask baselines. |
| **United States** | FCC Upper C-Band Order | Limits 3980–4140 MHz emissions to 65 dBm/MHz; enforces spurious cap of -28.4 dBm/MHz EIRP. | Provides clear network-side emission limits missing in qualitative regulatory regimes. |
| **Europe** | CEPT ECC Report 362 & EASA | Determines 6 dB margin is preserved beyond 1200 m from runway thresholds. EASA does not mandate fleet retrofits. | Demonstrates policy divergence: aviation stakeholders dispute findings, recorded as conflict `CONF-001`. |
| **Canada** | Transport Canada AD CF-2025-54 | Imposes operational restrictions and airworthiness directives on non-retrofitted aircraft. | Demonstrates bilateral coordination between national airworthiness authority and spectrum regulators. |
| **International** | ICAO Doc 9718, Annex 10 Vol V | Recommends 6 to 10 dB safety margins for radionavigation services against commercial wireless systems. | Authoritative technical guidance; serves as SkySync's primary mathematical constraint parameter. |

---

## 9. Alignment with ITU AI Readiness Dimensions

SkySync's architecture explicitly demonstrates compliance across five dimensions of the **ITU AI Readiness Framework**:

1. **Dimension 4: Contextualization and Regional Impact**: SkySync is anchored in India's national regulatory framework (DoT NFAP 2025, DGCA AIC 19/2025, Telecommunications Act 2023) while retaining modular portability. Swapping the Knowledge Base allows the gateway to operate under FCC, CEPT, or ICAO jurisdictions without rewriting code.
2. **Dimension 8: Human-in-the-Loop & Collaboration**: Automated autonomy is bounded. Dynamic power increases within airport protection zones, operations during CAT III low-visibility conditions, and unresolved policy gaps deterministically require human sign-off (`requires_human_approval = true`).
3. **Dimension 6: Generative AI Guardrails**: Strict schema validation and deterministic fail-safes prevent ungrounded model output from propagating to network controllers. LLMs are prohibited from executing safety evaluations, and ambiguous inputs deterministically yield precautionary blocks.
4. **Dimension 3: Data, Model & Provenance Integrity**: Every safety decision is mapped to verified, citation-backed claim records. Each record specifies the source document, locator section, verification tier, and confidence rating.
5. **Dimension 12: Standards, Openness & Interoperability**: Implements open JSONL/CSV schemas, strictly aligns with ITU-T Y.3172 node topology, and provides automated integrity test suites for cross-platform validation.

---

## 10. Scenario Evaluation & Results

```
+------------------------------------------------------------------------------------------------------+
| SCENARIO DEMO-001 EVALUATION SUMMARY                                                                 |
| Aircraft: CAT II Final Approach at 450 ft AGL | Cell: 94% PRB Load, 38% Throughput Collapse           |
+------------------------------------------------------------------------------------------------------+
| Candidate Action        | Deterministic Check   | Verdict    | Operational Rationale                 |
|-------------------------|-----------------------|------------|---------------------------------------|
| ACT-1 (+3 dB Power)     | Margin Unprovable     | [REJECT]   | Transmit power unknown; fails 6 dB.   |
| ACT-4 (Retune 4100 MHz) | Outside NFAP 2025     | [REJECT]   | 4100 MHz is not licensed in India.    |
| ACT-2 (Traffic Steer)   | Margin: +42.1 dB      | [ACCEPT]   | Steers traffic >1200m; 91% QoS kept.  |
| ACT-3 (Tilt + Cap)      | Stale Calibration     | [PENDING]  | Site calibration expired; refresh req.|
+------------------------------------------------------------------------------------------------------+
```

### 10.1 Primary Scenario Breakdown

- **DEMO-001 (Congested Cell Under Arrival Path - India)**:
  - *Context*: Cell at 94% PRB load near aerodrome; aircraft at 450 ft AGL on CAT II ILS approach; aircraft altimeter tolerance status is unverified; base station transmit power is uncalibrated.
  - *Pipeline Execution*: Network Agent requests ACT-1 (+3 dB power). Airspace Safety Agent evaluates slant range and flags unverified power as `UNKNOWN`, violating `CON-RAD-001`. Spectrum Agent rejects ACT-4 (retuning to 4100 MHz) via `CON-IN-001` (outside licensed 3300–3670 MHz band). Policy Agent flags that DGCA AIC 19/2025 is `NOT_YET_IN_FORCE` and enforces mandatory human approval (`CON-IN-004`). Optimization Agent ranks traffic steering (ACT-2) highest.
  - *Result*: ACT-2 is **ACCEPTED** (+42.1 dB simulated margin, 91% QoS retention). ACT-1 and ACT-4 are **REJECTED**. ACT-3 is set to **PENDING** pending antenna tilt calibration.
- **DEMO-002 (Low-Altitude Touchdown Flare at 50 ft AGL)**:
  - *Context*: Aircraft in final flare at 50 ft AGL; base station located 350 m from runway centerline; cell at 82% load; aircraft verified as interference-tolerant.
  - *Result*: ACT-3 (4° electrical downtilt with 20% power cap) is **ACCEPTED** once margin simulation confirms $\ge 6$ dB protection. ACT-1 and ACT-4 are **REJECTED**.
- **DEMO-003 (Dense Fog CAT III Autoland with Legacy Avionics)**:
  - *Context*: Zero-visibility CAT III autoland at 100 ft AGL; aircraft carries legacy, non-tolerant altimeter; cell at 98% load operating at maximum licensed power (65 dBm/MHz).
  - *Result*: System issues an emergency **`[ESCALATE]`** verdict. Dynamic power boosts and carrier adjustments are rejected; execution halts for human air traffic and spectrum authority oversight.

### 10.2 Dynamic Re-Planning Matrix

| Scenario Twist | Perturbation Injected | Autonomous System Re-Planning Behaviour |
| :--- | :--- | :--- |
| **Twist S2** | Clear airspace; no aircraft within 10 km corridor. | Prioritizes QoS throughput recovery; power increase proposals still route through human authorization gate. |
| **Twist S3** | Proposed action relies on expired antenna calibration. | Issues `PENDING` verdict; blocks actuation until calibration telemetry is updated. |
| **Twist S4** | Second aircraft enters corridor on blind CAT III autoland. | Re-evaluates PFD margin against the most vulnerable airframe; locks safety gate to `ESCALATE`. |
| **Twist S5** | Operator attempts retuning outside national allocation. | Deterministic rejection on `CON-IN-001`; optimizer synthesizes within-band carrier aggregation alternative. |
| **Twist S6** | Scenario `as_of_date` advanced past 2027-12-31. | DGCA AIC 19/2025 automatically transitions from advisory risk finding to binding mandatory law without code modification. |

### 10.3 Evaluation Metrics

| Metric Category | Target Value | Measured System Result |
| :--- | :--- | :--- |
| **Unsafe-Accept Rate** | 0.0% (Zero Tolerance) | **0.0%** (100% of hard constraint violations blocked) |
| **Constraint Coverage** | 100% of applicable rules | **100%** across test suites (17/17 constraints tested) |
| **Evidence Grounding Ratio** | 100% citations backed by KB | **100%** (Unverified citations stripped by Evidence Guard) |
| **Temporal Consistency** | 100% as-of date accuracy | **100%** (Accurate transition on 2027-12-31 boundary) |
| **Mean Evaluation Latency** | < 2500 ms | **1420 ms** (Synchronous end-to-end swarm execution) |
| **QoS Retained (DEMO-001)** | > 85% | **91.0%** (Via non-interfering traffic steering) |

---

## 11. Primary Regulatory References

1. **Federal Aviation Administration (FAA)**: *Requirements for Interference-Tolerant Radio Altimeter Systems*, Final Rule, Federal Register 2026-15585. [https://public-inspection.federalregister.gov/2026-15585.pdf](https://public-inspection.federalregister.gov/2026-15585.pdf)
2. **Directorate General of Civil Aviation (DGCA / AAI, India)**: *Aeronautical Information Circular (AIC) 19/2025: Radio Altimeter Tolerance Requirements*. [https://aim-india.aai.aero/eaip/eaip-v2-08-2026/pdf/Official%20AIC/AIC2025/AIC_19_2025.pdf](https://aim-india.aai.aero/eaip/eaip-v2-08-2026/pdf/Official%20AIC/AIC2025/AIC_19_2025.pdf)
3. **Department of Telecommunications (DoT, India)**: *National Frequency Allocation Plan (NFAP) 2025*. [https://www.dot.gov.in/static/uploads/2026/02/b110cdc386d3a4e41c8483d7ffd7c410.pdf](https://www.dot.gov.in/static/uploads/2026/02/b110cdc386d3a4e41c8483d7ffd7c410.pdf)
4. **Ministry of Law and Justice, India**: *The Telecommunications Act, 2023 (Act No. 44 of 2023)*. [https://www.indiacode.nic.in/bitstream/123456789/20101/1/a2023-44.pdf](https://www.indiacode.nic.in/bitstream/123456789/20101/1/a2023-44.pdf)
5. **Electronic Communications Committee (CEPT / ECC)**: *ECC Report 362: Compatibility between 5G MFCN and Radio Altimeters in 4200–4400 MHz*. [https://docdb.cept.org/download/4582](https://docdb.cept.org/download/4582)
6. **International Telecommunication Union (ITU-R)**: *Radio Regulations, Footnote 5.438 (Allocation to Aeronautical Radionavigation Service in 4200–4400 MHz)*. [https://rfpi.comreg.ie/content-item/801,5438](https://rfpi.comreg.ie/content-item/801,5438)
7. **International Telecommunication Union (ITU-R)**: *Recommendation ITU-R M.2059: Operational and technical characteristics of radio altimeters*. [https://itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2059-0-201402-I!!PDF-S.pdf](https://itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2059-0-201402-I!!PDF-S.pdf)
8. **International Civil Aviation Organization (ICAO)**: *Doc 9718: Handbook on RF Spectrum Requirements for Civil Aviation, Vol. I*. [https://www.icao.int/sites/default/files/FSMP/Doc9718_VolI_4th_Edition_2026_Advance_Unedited_Version.pdf](https://www.icao.int/sites/default/files/FSMP/Doc9718_VolI_4th_Edition_2026_Advance_Unedited_Version.pdf)
9. **3rd Generation Partnership Project (3GPP)**: *Technical Specifications TS 28.541, TS 28.552, and TS 38.104*. [https://portal.3gpp.org/](https://portal.3gpp.org/)
10. **International Telecommunication Union (ITU-T)**: *Recommendation ITU-T Y.3172: Architectural framework for machine learning in future networks including IMT-2020*. [https://www.itu.int/rec/T-REC-Y.3172/en](https://www.itu.int/rec/T-REC-Y.3172/en)

---

## 12. Reproduction & Verification

### 12.1 Environment Setup
```bash
# Clone the repository
git clone https://github.com/Nitya2102/SkySync.git
cd SkySync

# Initialize Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
cp .env.example .env
```

### 12.2 Knowledge Base Validation & Retrieval
```bash
# Verify Knowledge Base relational integrity and reference completeness
python kb/validate.py

# Query the hybrid retrieval engine with temporal and authority filters
python kb/kb_retriever.py "radio altimeter margin"
```

### 12.3 Automated Test Suites
```bash
# Execute comprehensive unit, integration, and scenario tests
pytest tests/ -v
```

### 12.4 Running the Application & Operator Console
```bash
# Launch the FastAPI backend and telemetry orchestrator
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Navigate to `http://localhost:8000` to access the interactive operator console and real-time execution ledger.

---

## 13. Repository Structure & Open Source License

```
SkySync/
├── app/                      # Backend application runtime
│   ├── agents/               # Six LangGraph domain agents
│   ├── graph/                # State graph runner and arbitration edges
│   ├── rag/                  # Hybrid RRF retriever and evidence guard
│   ├── tools/                # Margin simulator and constraint checker
│   ├── main.py               # FastAPI web server and SSE streams
│   └── models.py             # Pydantic data models and schemas
├── frontend/                 # Interactive React / Vite operator console
├── kb/                       # Version-controlled Knowledge Base
│   ├── sources.csv           # 53 authoritative sources index
│   ├── claims.jsonl          # 89 atomic structured claims
│   ├── constraints.json      # 17 machine-checkable constraints
│   ├── conflicts.json        # 5 documented regulatory conflicts
│   ├── policy_gaps.json      # 10 policy and standards gaps
│   ├── graph.json            # Institutional entity-relationship graph
│   ├── schema.json           # Formal JSON schema validation
│   ├── validate.py           # KB validation script
│   └── kb_retriever.py       # Standalone KB retrieval tester
├── runs/                     # Persisted JSON audit ledger logs
├── tests/                    # Pytest verification suites
├── .gitignore                # Environment and secret protection
├── requirements.txt          # Python runtime dependencies
└── README.md                 # System technical report
```

**License**: Distributed under the **Apache-2.0 License**. All scenario models, aircraft vectors, and telemetry feeds represent synthetic sandbox simulations.
