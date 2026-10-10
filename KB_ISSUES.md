# 5G–Airspace Knowledge Base: Gaps, Conflicts & Assessment

This document summarizes known policy gaps, structural limitations, and evidence conflicts identified in `5g_airspace_kb_v3`.

---

## 1. Documented Policy Gaps

### GAP-006: Lack of Published Numeric Airport Buffer Limits in India
- **Impacted Regulation**: DGCA AIC 19/2025 and related DoT circulars.
- **Description**: While Indian regulatory circulars stipulate airport-area restrictions on 5G C-band emissions, primary public circulars omit explicit numeric exclusion distance buffers and maximum EIRP masks around runway approach corridors.
- **System Handling**: Handled via precautionary default (`CheckResult.UNKNOWN` on `CON-IN-003`). Any unverified emission increase near synthetic airports defaults to a precautionary rejection until human or official clarification is provided.

### GAP-007: Absence of National Radar Altimeter Tolerance Standard in India
- **Impacted Authority**: DGCA India.
- **Description**: DGCA circulars reference civil aviation safety but do not define domestic radio altimeter interference tolerance masks (ITMs).
- **System Handling**: The system utilizes US FAA ITM threshold curves as an analogy (`analogy_note: US ITM thresholds used as analogy for India`), tagged explicitly in all calculations to avoid misrepresenting US regulatory thresholds as Indian statute.

---

## 2. Documented Conflicts

### CONF-001: FAA Conservative ITM Envelope vs. Telecom Industry Interference Models
- **Position A (Aviation - FAA / RTCA DO-377A)**:
  - Assumes worst-case radar altimeter antenna gain pattern, minimum separation distance of 35 ft over runway threshold, and stringent 6 dB safety margin buffer. Recommends severe power restrictions within runway approach cones.
- **Position B (Telecom - COAI / CTIA / 3GPP)**:
  - Emphasizes real-world base station antenna downtilt attenuation, fuselage shielding, clutter losses, and spurious filtering. Argues that normal commercial deployments outside runway boundaries present zero risk.
- **System Resolution (Rule 6)**:
  - The system **never averages or resolves away** this conflict. Both positions and `CONF-001` are cited in reports, and conservative safety envelopes are maintained in approach areas while off-corridor traffic steering is prioritized to resolve telecom capacity needs without conflict.

---

## 3. Structural & Formatting Observations in KB Data

1. **Heterogeneous Field Formats in `claims.jsonl`**:
   - Most numeric claims supply a key-value dictionary (e.g. `CLM-109`).
   - Claim `CLM-160` provided a list `["network", "optimization"]` in the `"numeric"` field rather than a dictionary. Handled gracefully by `EvidenceItem` parser with type-defensive guards.
2. **Temporal Dates**:
   - DGCA AIC 19/2025 carries an effective date of `2027-12-31`. For scenario queries dated before this deadline (e.g. `as_of = 2026-10-07`), the rule is correctly classified as `NOT_YET_IN_FORCE`.
