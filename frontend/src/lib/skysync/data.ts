// Fallback mock data so the UI renders before the backend is connected.

export type Tier = "Primary Standard" | "Regulatory" | "Industry Study" | "Operational" | "Derived";
export interface DictEntry {
  code: string;
  title: string;
  explanation: string;
  source: string;
  tier: Tier | string;
  value?: string;
  kind: "claim" | "constraint" | "conflict" | "gap" | "action";
}

export const mockDictionary: Record<string, DictEntry> = Object.fromEntries(
  ([
    // Core Claims
    { code: "CLM-101", kind: "claim", title: "FAA Part 25 Radio Altimeter Interference Tolerance Rule", explanation: "Mandates radio altimeter tolerance limits against neighboring-band C-Band transmissions for transport aircraft.", source: "FAA 14 CFR Part 25", tier: "Primary Standard", value: "Part 25.1309" },
    { code: "CLM-102", kind: "claim", title: "Group 4 Tolerance Category Profile", explanation: "Highest tolerance class of radar altimeters equipped with advanced micro-strip front-end filtering.", source: "FAA Final Rule", tier: "Regulatory", value: "Class 4 Filter" },
    { code: "CLM-103", kind: "claim", title: "Group 3 Retrofit Altimeter Tolerance Standard", explanation: "Modified airline altimeters retrofitted with point-tuned bandpass filters satisfying AD compliance.", source: "FAA SAIB", tier: "Regulatory", value: "Class 3" },
    { code: "CLM-104", kind: "claim", title: "Group 2 Legacy Altimeter Interference Limit", explanation: "Unmodified legacy altimeters prone to front-end desensitization under high aggregate PFD.", source: "RTCA SC-239", tier: "Industry Study" },
    { code: "CLM-105", kind: "claim", title: "Group 1 Susceptible Altimeter Operational Restriction", explanation: "Highly susceptible legacy altimeters requiring strict 2 NM exclusion zones around precision runways.", source: "FAA AD 2023-11-07", tier: "Regulatory" },
    { code: "CLM-106", kind: "claim", title: "ICAO 6 dB Radar Altimeter Safety Buffer", explanation: "International Civil Aviation Organization standard requiring a minimum 6 dB buffer between maximum predicted interference and altimeter receiver tolerance.", source: "ICAO Doc 9718 / Annex 10", tier: "Primary Standard", value: "Buffer: 6.0 dB" },
    { code: "CLM-109", kind: "claim", title: "ITM Propagation Glide Path Margin Formulation", explanation: "Mathematical determination of incident Power Flux Density along 3-degree glide slope using Irregular Terrain Model.", source: "ITU-R P.528 / NTIA", tier: "Derived", value: "ITM PFD Calc" },
    { code: "CLM-112", kind: "claim", title: "Radar Altimeter Band Allocation", explanation: "Radio altimeters operate in the 4200–4400 MHz band, adjacent to C-band 5G deployments.", source: "ITU Radio Regulations", tier: "Primary Standard", value: "4200–4400 MHz" },
    { code: "CLM-115", kind: "claim", title: "CAT II Decision Height and Flare Envelope", explanation: "Critical low-altitude approach window between 100 ft and 50 ft where radio altimeter feeds autoland flare computers.", source: "ICAO Doc 9365", tier: "Primary Standard", value: "DH: 100 ft" },
    { code: "CLM-118", kind: "claim", title: "Altimeter Interference Tolerance Threshold", explanation: "Maximum tolerable PFD at the altimeter antenna before measurable error for the most susceptible receiver class.", source: "RTCA DO-155 / SC-239", tier: "Industry Study", value: "−80.6 dBW/m²/MHz" },
    { code: "CLM-120", kind: "claim", title: "Approach Azimuth Radar Beam Cleared Corridor", explanation: "Lateral buffer of 300 m on either side of runway center line where spurious emissions must be suppressed.", source: "ICAO Annex 14", tier: "Regulatory", value: "Buffer: 300 m" },
    { code: "CLM-121", kind: "claim", title: "ILS CAT II Precision Approach Profile", explanation: "Category II precision approaches require reliable radar altimeter readings down to 100 ft decision height.", source: "ICAO Doc 9365", tier: "Primary Standard", value: "DH: 100 ft" },
    { code: "CLM-130", kind: "claim", title: "DGCA AIC 19/2025 Altimeter Precautionary Advisory", explanation: "Indian aviation regulator advisory defining radio altimeter tolerance baselines and operational limits.", source: "DGCA India AIC 19/2025", tier: "Regulatory", value: "AIC 19/2025" },
    { code: "CLM-131", kind: "claim", title: "DGCA Altimeter Retrofit Timeline (2027 Mandate)", explanation: "Mandates airline retrofits for Indian airspace operations by December 31, 2027.", source: "DGCA India", tier: "Regulatory", value: "Deadline: 2027-12-31" },
    { code: "CLM-132", kind: "claim", title: "DoT C-Band Spectrum Allocation (3300–3670 MHz)", explanation: "Department of Telecommunications India allocation for 5G terrestrial communications.", source: "DoT NFAP 2025", tier: "Regulatory", value: "3300–3670 MHz" },
    { code: "CLM-134", kind: "claim", title: "Aerodrome Exclusion Zone Guidance", explanation: "Base stations within the approach corridor should apply power limits or antenna down-tilt inside defined buffer distances.", source: "FAA AD 2023-11-07", tier: "Regulatory", value: "Corridor: 1200 m" },
    { code: "CLM-135", kind: "claim", title: "Indian Civil Aviation Glideslope Baseline Protection", explanation: "Press and interim directives requiring precautionary power capping near airport runways.", source: "DGCA / DoT Coordination", tier: "Advisory" },
    { code: "CLM-136", kind: "claim", title: "Inter-Ministerial DoT/DGCA Coordination Mandate", explanation: "Requirement for inter-agency consultation before authorizing power alterations in airport vicinity.", source: "DoT-WPC Mandate", tier: "Regulatory" },
    { code: "CLM-140", kind: "claim", title: "C-Band Spectrum Separation & Guard Band", explanation: "Spectrum separation between 5G carrier edges and protected 4200–4400 MHz altimeter band.", source: "ITU RR / FCC 20-22", tier: "Regulatory", value: "Guard: 530+ MHz" },
    
    // Core Constraints
    { code: "CON-RAD-001", kind: "constraint", title: "Radar Altimeter Minimum Safety Margin (≥ 6 dB)", explanation: "Hard deterministic constraint: predicted interference margin at the altimeter receiver must exceed 6.0 dB under worst-case geometry.", source: "ICAO Doc 9718 / Annex 10", tier: "Primary Standard", value: "≥ 6.0 dB" },
    { code: "CON-RAD-002", kind: "constraint", title: "Glidepath Approach Corridor Protection", explanation: "Base station EIRP may not increase for cells whose main beam intersects the runway approach corridor within 1200 m.", source: "FAA AD 2023-11-07 / ICAO", tier: "Regulatory", value: "Corridor: 1200 m" },
    { code: "CON-3GPP-001", kind: "constraint", title: "Cellular QoS & PRB Load Floor", explanation: "Mitigations must preserve at least 70% of subscriber throughput and avoid indefinite resource-block starvation.", source: "3GPP TS 23.501", tier: "Operational", value: "≥ 70%" },
    { code: "CON-3GPP-002", kind: "constraint", title: "3GPP Out-of-Band Emission Mask", explanation: "Base station spurious and out-of-band emissions must remain below defined 3GPP spectral mask limits.", source: "3GPP TS 38.104", tier: "Operational" },
    { code: "CON-INT-001", kind: "constraint", title: "RA Band Exclusivity (4200–4400 MHz)", explanation: "No 5G carrier, channel edge or intentional emission may be placed inside 4200–4400 MHz.", source: "ITU Radio Regulations", tier: "Primary Standard", value: "4200–4400 MHz" },
    { code: "CON-INT-002", kind: "constraint", title: "Safety Services Special Protection (RR 4.10)", explanation: "Any network action that raises emissions near aviation-sensitive areas requires an interference assessment.", source: "ITU RR 4.10", tier: "Primary Standard" },
    { code: "CON-INT-003", kind: "constraint", title: "Minimum Safety Margin (≥ 6 dB)", explanation: "Predicted interference at the radio altimeter must remain at least 6 dB below the tolerance level.", source: "ICAO Doc 9718", tier: "Regulatory", value: "≥ 6.0 dB" },
    { code: "CON-INT-004", kind: "constraint", title: "Carrier Frequency License Bound", explanation: "Carrier frequencies must strictly respect national allocation boundaries (e.g. 3300–3670 MHz in India).", source: "National Spectrum Policy", tier: "Regulatory" },
    { code: "CON-IN-001", kind: "constraint", title: "NFAP 2025 5G Allocation (3300–3670 MHz)", explanation: "5G transmissions in India are legally restricted to the licensed 3300–3670 MHz frequency block.", source: "India NFAP 2025", tier: "Regulatory", value: "3300–3670 MHz" },
    { code: "CON-IN-002", kind: "constraint", title: "India AIC 19/2025 Altimeter Compliance Mandate", explanation: "Aircraft operating in Indian airspace are subject to altimeter filter compliance requirements.", source: "DGCA AIC 19/2025", tier: "Regulatory" },
    { code: "CON-IN-003", kind: "constraint", title: "Airport-Area 5G Interim Restrictions", explanation: "Precautionary power limits and exclusion distances applicable around Indian aerodromes.", source: "DGCA / DoT Guidance", tier: "Precautionary" },
    { code: "CON-IN-004", kind: "constraint", title: "Dynamic Power/Beam Coordination Requirement", explanation: "Dynamic power or beam alterations near airport runways require human-in-the-loop authorization.", source: "DoT-WPC / DGCA Mandate", tier: "Regulatory" },
    
    // Legacy Constraints
    { code: "CON-201", kind: "constraint", title: "Minimum Safety Margin ≥ 6 dB", explanation: "Hard deterministic constraint: computed margin must exceed the ICAO buffer under worst-case geometry.", source: "Derived from CLM-106", tier: "Derived", value: "≥ 6.0 dB" },
    { code: "CON-204", kind: "constraint", title: "No Power Increase Inside Corridor", explanation: "Base station EIRP may not increase for cells whose main lobe intersects the approach corridor.", source: "FAA AD 2023-11-07", tier: "Regulatory" },
    { code: "CON-207", kind: "constraint", title: "Upper C-Band Activation Freeze", explanation: "Carriers above 4000 MHz may not be activated within 2 NM of an active CAT II/III runway.", source: "National Spectrum Policy", tier: "Regulatory", value: "Radius: 2 NM" },
    { code: "CON-210", kind: "constraint", title: "Network QoS Floor", explanation: "Mitigations must preserve at least 85% of subscriber throughput in the affected sector.", source: "Operator SLA", tier: "Operational", value: "≥ 85%" },
    { code: "CON-213", kind: "constraint", title: "Retrofit Filter Status Disclosure", explanation: "Aircraft altimeter retrofit status must be verified to relax any spectrum constraint.", source: "FAA SAIB", tier: "Regulatory" },

    // Conflicts
    { code: "CONF-001", kind: "conflict", title: "Capacity Recovery vs. Corridor Power Freeze", explanation: "Network agent proposes power boost to recover 94% PRB load, colliding with airspace safety corridor freeze.", source: "Agent Arbitration", tier: "Derived" },
    { code: "CONF-002", kind: "conflict", title: "Spectrum Expansion vs. Protected Altimeter Band", explanation: "Spectrum retuning to 4100 MHz abuts protected 4200–4400 MHz altimeter frequencies.", source: "Agent Arbitration", tier: "Derived" },
    { code: "CONF-301", kind: "conflict", title: "Capacity vs. Corridor Power Limits", explanation: "Network Agent wants higher power for congestion relief; Airspace Safety Agent requires power to hold.", source: "Agent arbitration", tier: "Derived" },
    { code: "CONF-302", kind: "conflict", title: "Spectrum Expansion vs. Activation Freeze", explanation: "Spectrum Agent proposes 4100 MHz carrier which collides with activation freeze near active runway.", source: "Agent arbitration", tier: "Derived" },

    // Gaps
    { code: "GAP-001", kind: "gap", title: "Dynamic Spectrum Sharing API Interface Gap", explanation: "No machine-readable API exists between cellular base station controllers and air traffic management.", source: "Knowledge base gap", tier: "Derived" },
    { code: "GAP-002", kind: "gap", title: "Real-Time ADS-B Approach Geometry Feed Gap", explanation: "Slant range is calculated from periodic telemetry rather than continuous millisecond ADS-B feed.", source: "Knowledge base gap", tier: "Derived" },
    { code: "GAP-003", kind: "gap", title: "Antenna Downtilt Telemetry Survey Gap", explanation: "Mechanical downtilt angle requires verified physical site calibration survey younger than 180 days.", source: "Site Registry", tier: "Operational" },
    { code: "GAP-006", kind: "gap", title: "Unverified Local Airport Power Restriction Gap", explanation: "Interim airport power restrictions lack published primary coordinate bounds; default to precaution.", source: "Precautionary Gap", tier: "Derived" },
    { code: "GAP-401", kind: "gap", title: "Unverified Altimeter Retrofit Fleet Share", explanation: "Share of arriving aircraft with retrofitted filters is not documented; precautionary assumption applied.", source: "Knowledge base gap", tier: "Derived" },
    { code: "GAP-402", kind: "gap", title: "Missing Antenna Down-tilt Log", explanation: "Latest site survey for BS-17 down-tilt is older than 180 days.", source: "Site registry", tier: "Operational" },

    // Actions
    { code: "ACT-1", kind: "action", title: "Transmit Power Boost (+3 dB)", explanation: "Raise sector EIRP to relieve congestion near the terminal.", source: "Network Agent", tier: "Operational", value: "+3 dB EIRP" },
    { code: "ACT-2", kind: "action", title: "Off-Corridor Traffic Steering > 1200 m", explanation: "Steer user traffic to cells located more than 1200 m from the approach centreline.", source: "Optimization Agent", tier: "Operational", value: "Offset: 1200 m" },
    { code: "ACT-3", kind: "action", title: "Antenna Down-tilt +2° + Power Capping", explanation: "Mechanically tilt the BS-17 antenna downward to reduce skyward lobe energy.", source: "Airspace Safety Agent", tier: "Operational", value: "+2°" },
    { code: "ACT-4", kind: "action", title: "Activate 4100 MHz Carrier", explanation: "Bring an upper C-band carrier online to increase capacity.", source: "Spectrum Agent", tier: "Operational", value: "4100 MHz" },
  ] as DictEntry[]).map((e) => [e.code, e]),
);

export const telemetry = {
  runway: "09L",
  approach: "ILS CAT II",
  altitudeFt: 450,
  horizontalM: 980,
  pfd: -38.6,
  margin: 42.1,
  threshold: 6,
  baseStation: "BS-17",
  frequency: "3.80 GHz",
};

export type Verdict = "accepted" | "rejected" | "pending";
export interface CandidateAction {
  code: string;
  verdict: Verdict;
  plain: string;
  rationale: string;
  violates?: string[];
  cites: string[];
  safety: number;
  qos: number;
}

export const candidateActions: CandidateAction[] = [
  { code: "ACT-2", verdict: "accepted", plain: "Move phone traffic away from the landing path by handing users over to towers more than 1.2 km from the runway centreline.", rationale: "Keeps the altimeter safety margin at +42.1 dB, well above the 6 dB ICAO buffer, while preserving 91% of network throughput. No hard constraint is breached.", cites: ["CON-201", "CON-210", "CLM-134"], safety: 96, qos: 91 },
  { code: "ACT-3", verdict: "pending", plain: "Tilt the nearest tower's antenna down by two degrees so less energy points toward the sky.", rationale: "Safe, but blocked from execution until a fresh down-tilt survey closes the data gap.", cites: ["GAP-402", "CON-201"], safety: 88, qos: 94 },
  { code: "ACT-1", verdict: "rejected", plain: "Turn up the tower's transmit power to relieve congestion in the terminal.", rationale: "Rejected: increases radiated energy inside the approach corridor.", violates: ["CON-204", "CONF-301"], cites: ["CLM-106"], safety: 41, qos: 99 },
  { code: "ACT-4", verdict: "rejected", plain: "Switch on a new 4100 MHz carrier for extra capacity.", rationale: "Rejected: activation freeze within 2 NM of an active CAT II runway, and retrofit status of arriving fleet is unverified / pending documentation.", violates: ["CON-207", "CON-213", "GAP-401"], cites: ["CLM-140"], safety: 33, qos: 100 },
];

export interface Agent {
  id: string;
  name: string;
  role: string;
  summary: string;
  confidence: number;
  steps: { title: string; text: string; chips: string[] }[];
}

const stepTitles = ["Telemetry Inspection", "Evidence & Standard Verification", "Operational Reasoning", "Precautionary Guard"];
const mk = (texts: [string, string[]][]) => texts.map(([text, chips], i) => ({ title: stepTitles[i] ?? "", text, chips }));

export const agents: Agent[] = [
  { id: "network", name: "Network Agent", role: "Capacity & QoS", confidence: 0.86, summary: "Sector BS-17 is at 92% load during the arrival bank. I proposed a power boost and traffic steering to protect subscriber experience.", steps: mk([
    ["Sector load 92%, PRB utilisation peaking during arrival bank.", []],
    ["Operator SLA requires ≥85% throughput retention.", ["CON-210"]],
    ["Power boost gives fastest relief; steering gives 91% retention.", ["ACT-1", "ACT-2"]],
    ["Flagged ACT-1 as likely to conflict with corridor limits.", ["CONF-301"]],
  ]) },
  { id: "airspace", name: "Airspace Safety Agent", role: "Approach Corridor Integrity", confidence: 0.97, summary: "Aircraft is on ILS CAT II at 450 ft AGL over threshold. Altimeter integrity is critical down to 100 ft; any power increase in the corridor is unacceptable.", steps: mk([
    ["Aircraft at 450 ft AGL, 980 m horizontal from BS-17.", []],
    ["CAT II decision height is 100 ft; ICAO buffer is 6 dB.", ["CLM-121", "CLM-106"]],
    ["Current margin +42.1 dB; power boost would erode it inside corridor.", ["CON-204"]],
    ["Recommend down-tilt but survey data is stale.", ["ACT-3", "GAP-402"]],
  ]) },
  { id: "spectrum", name: "Spectrum Agent", role: "Frequency Coexistence", confidence: 0.81, summary: "Active carrier at 3.80 GHz maintains a 400 MHz separation from the altimeter band. A 4100 MHz carrier would add capacity but halve that separation.", steps: mk([
    ["Carrier at 3.80 GHz, OOBE within mask.", ["CLM-112"]],
    ["Guard band guidance satisfied for current carrier.", ["CLM-140"]],
    ["4100 MHz would add 100 MHz capacity.", ["ACT-4"]],
    ["Activation freeze may apply near CAT II runway.", ["CON-207", "CONF-302"]],
  ]) },
  { id: "policy", name: "Policy Institutional Agent", role: "Regulation & Authority", confidence: 0.92, summary: "FAA AD and national policy define corridor limits and an upper C-band activation freeze. Retrofit status of arriving fleet is undisclosed.", steps: mk([
    ["Active runway 09L, CAT II operations declared.", []],
    ["Corridor guidance and activation freeze in force.", ["CLM-134", "CON-207"]],
    ["Constraints cannot be relaxed without retrofit disclosure.", ["CON-213"]],
    ["Assume worst-case non-retrofitted receivers.", ["GAP-401"]],
  ]) },
  { id: "optimization", name: "Optimization Agent", role: "Pareto Trade-offs", confidence: 0.89, summary: "Across four candidates, ACT-2 sits on the Pareto frontier with 96 safety and 91 QoS scores. ACT-1 and ACT-4 dominate on capacity but fail safety.", steps: mk([
    ["Collected 4 candidate actions from domain agents.", ["ACT-1", "ACT-2", "ACT-3", "ACT-4"]],
    ["Scored each on safety margin and QoS retention.", ["CON-201", "CON-210"]],
    ["ACT-2 and ACT-3 are non-dominated.", ["ACT-2", "ACT-3"]],
    ["Forward ranked list to deterministic engine.", []],
  ]) },
  { id: "arbitration", name: "Arbitration Agent", role: "Final Verdict", confidence: 0.98, summary: "Accepted ACT-2 off-corridor steering. Rejected ACT-1 and ACT-4 on hard constraint violations. ACT-3 held pending fresh survey data.", steps: mk([
    ["Received ranked candidates and constraint verdicts.", []],
    ["Verified margin ≥ 6 dB for accepted action.", ["CON-201", "CLM-106"]],
    ["Resolved conflicts in favour of airspace safety.", ["CONF-301", "CONF-302"]],
    ["Logged decision to Final Safety Ledger.", ["ACT-2"]],
  ]) },
];

export type Status = "PASS" | "FAIL" | "UNKNOWN" | "UNVERIFIED";
export const ledger: { constraint: string; action: string; status: Status; reason: string; cites: string[] }[] = [
  { constraint: "CON-201", action: "ACT-2", status: "PASS", reason: "Margin +42.1 dB exceeds 6 dB buffer.", cites: ["CLM-106", "CLM-118"] },
  { constraint: "CON-204", action: "ACT-2", status: "PASS", reason: "No EIRP increase; traffic moved off-corridor.", cites: ["CLM-134"] },
  { constraint: "CON-210", action: "ACT-2", status: "PASS", reason: "91% throughput retained (≥85% floor).", cites: [] },
  { constraint: "CON-204", action: "ACT-1", status: "FAIL", reason: "+3 dB EIRP inside approach corridor.", cites: ["CLM-134"] },
  { constraint: "CON-201", action: "ACT-1", status: "FAIL", reason: "Worst-case margin drops below buffer for non-retrofitted receivers.", cites: ["CLM-106", "GAP-401"] },
  { constraint: "CON-207", action: "ACT-4", status: "FAIL", reason: "Upper C-band activation within 2 NM of CAT II runway.", cites: ["CLM-140"] },
  { constraint: "CON-213", action: "ACT-4", status: "UNVERIFIED", reason: "Fleet retrofit status not disclosed.", cites: ["GAP-401"] },
  { constraint: "CON-201", action: "ACT-3", status: "UNVERIFIED", reason: "Down-tilt survey older than 180 days.", cites: ["GAP-402"] },
  { constraint: "CON-210", action: "ACT-3", status: "PASS", reason: "94% throughput retained.", cites: [] },
];

export interface GraphNode { id: string; label: string; col: number; row: number; role: string; inputs: string[] }
export const graph: { nodes: GraphNode[]; edges: [string, string][] } = {
  nodes: [
    { id: "input", label: "Flight & 5G Telemetry", col: 0, row: 1.5, role: "Fuses ADS-B flight track, ILS state and base station configuration into a single snapshot.", inputs: ["ADS-B track", "Runway state", "BS-17 config"] },
    { id: "network", label: "Network Agent", col: 1, row: 0, role: "Assesses capacity and proposes QoS actions.", inputs: ["Sector load", "Operator SLA"] },
    { id: "airspace", label: "Airspace Safety Agent", col: 1, row: 1, role: "Protects approach corridor and altimeter integrity.", inputs: ["Altitude", "Slant range", "ICAO buffer"] },
    { id: "spectrum", label: "Spectrum Agent", col: 1, row: 2, role: "Evaluates frequency separation and emissions.", inputs: ["Carrier map", "Emission masks"] },
    { id: "policy", label: "Policy Institutional Agent", col: 1, row: 3, role: "Maps regulations and authority directives.", inputs: ["FAA AD", "Spectrum policy"] },
    { id: "optimization", label: "Optimization Agent", col: 2, row: 1.5, role: "Computes Pareto trade-offs between safety and QoS.", inputs: ["4 agent reports", "Candidate actions"] },
    { id: "engine", label: "Deterministic Constraint Engine", col: 3, row: 1.5, role: "Checks every candidate against hard constraints. No reasoning, only rules.", inputs: ["Ranked candidates", "Constraint set"] },
    { id: "ledger", label: "Final Safety Ledger", col: 4, row: 1.5, role: "Immutable record of verdicts, reasons and citations.", inputs: ["Verdicts", "Citations"] },
  ],
  edges: [
    ["input", "network"], ["input", "airspace"], ["input", "spectrum"], ["input", "policy"],
    ["network", "optimization"], ["airspace", "optimization"], ["spectrum", "optimization"], ["policy", "optimization"],
    ["optimization", "engine"], ["engine", "ledger"],
  ],
};
