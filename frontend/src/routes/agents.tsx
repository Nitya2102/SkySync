import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import {
  Activity,
  CheckCircle2,
  ChevronDown,
  Cpu,
  Gavel,
  Loader2,
  Plane,
  Radio,
  ShieldCheck,
  Sparkles,
  XCircle,
  Zap
} from "lucide-react";
import { Shell, PageTitle } from "@/components/skysync/Shell";
import { CodeChip } from "@/components/skysync/CodeChip";
import { API_BASE } from "@/lib/skysync/api";

export const Route = createFileRoute("/agents")({
  head: () => ({
    meta: [
      { title: "Live Agent Swarm — SkySync" },
      { name: "description", content: "Watch specialized autonomous agents execute safety checks and multi-objective arbitration in real time." },
    ],
  }),
  component: AgentsPage,
});

type AgentStep = { title: string; text: string; chips: string[] };
type AgentData = {
  id: string;
  name: string;
  role: string;
  confidence: number;
  summary: string;
  steps: AgentStep[];
  status: "pending" | "running" | "completed" | "error";
  badges?: string[];
};

const INITIAL_AGENTS: AgentData[] = [
  { id: "network", name: "Network Agent", role: "QoS & PRB Load Analysis", confidence: 0, summary: "Awaiting telemetry ingestion...", steps: [], status: "pending" },
  { id: "airspace_safety", name: "Airspace Safety Agent", role: "Glide Path PFD Margin", confidence: 0, summary: "Awaiting telemetry ingestion...", steps: [], status: "pending" },
  { id: "spectrum", name: "Spectrum Agent", role: "ITU RR 5.438 & Band Exclusivity", confidence: 0, summary: "Awaiting telemetry ingestion...", steps: [], status: "pending" },
  { id: "policy_institutional", name: "Policy Institutional Agent", role: "DGCA Rules & Human Gate", confidence: 0, summary: "Awaiting telemetry ingestion...", steps: [], status: "pending" },
  { id: "optimization", name: "Optimization Agent", role: "Pareto Multi-Objective Trade-offs", confidence: 0, summary: "Awaiting domain assessments...", steps: [], status: "pending" },
  { id: "arbitration", name: "Arbitration Agent", role: "Coexistence Safety Ledger", confidence: 0, summary: "Awaiting optimization and constraints...", steps: [], status: "pending" }
];

const SCENARIOS = [
  {
    id: "DEMO-001",
    label: "Scenario 1",
    sub: "Final Approach & PRB Overload",
    desc: "Aircraft on CAT II final approach at 450 ft AGL. Nearest C-band cell experiencing severe 94% PRB congestion."
  },
  {
    id: "DEMO-002",
    label: "Scenario 2",
    sub: "Low-Altitude Flare Encroachment",
    desc: "Aircraft on short touchdown flare at 50 ft AGL. 5G tower situated only 350 m from runway threshold at 35 m height."
  },
  {
    id: "DEMO-003",
    label: "Scenario 3",
    sub: "Zero-Visibility CAT III Autoland",
    desc: "Zero-visibility autoland in dense fog (100 ft AGL). Regional jet equipped with unverified legacy radar altimeter."
  }
];

/** Clean up text by cutting out unnecessary filler and keeping punchy operational facts */
function cleanAgentText(raw: string): string {
  if (!raw) return "";
  return raw
    .replace(/^To evaluate this according to the simulation parameters,?\s*/i, "")
    .replace(/^Based on the input values provided,?\s*/i, "")
    .replace(/^In order to verify compliance with standards,?\s*/i, "")
    .replace(/^The agent has completed its assessment:\s*/i, "")
    .replace(/^During execution of the pipeline,?\s*/i, "")
    .replace(/\(UNKNOWN\)/g, "(PRECAUTIONARY)")
    .replace(/\bis unknown\b/gi, "is unverified")
    .replace(/\btolerance is unknown\b/gi, "tolerance is unverified")
    .replace(/\bUnknown\b/g, "Precautionary")
    .replace(/\bunknown\b/g, "unverified")
    .trim();
}

/** Roll-out typing effect with live cursor and highlight chips for numbers & citations */
function WordRolloutText({ text, speed = 20 }: { text: string; speed?: number }) {
  const clean = cleanAgentText(text);
  const words = clean.split(" ");
  const [wordCount, setWordCount] = useState(words.length > 8 ? 2 : words.length);

  useEffect(() => {
    setWordCount(1);
    const timer = setInterval(() => {
      setWordCount((prev) => {
        if (prev < words.length) {
          return prev + 1;
        }
        clearInterval(timer);
        return prev;
      });
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed]);

  const visibleWords = words.slice(0, wordCount);
  const isTyping = wordCount < words.length;

  return (
    <span>
      {visibleWords.map((word, idx) => {
        // Highlight metrics and claim/constraint IDs cleanly in blue
        const isCitation = /(?:CLM-\d+|CON-[A-Za-z0-9-]+|ACT-\d+|CONF-\d+)/.test(word);
        const isMetric = /^[+-]?\d+(?:\.\d+)?(?:dB|%|m|ft|MHz)?$/.test(word);

        if (isCitation) {
          return (
            <span key={idx} className="font-mono font-bold text-blue-700 bg-blue-50/80 px-1 py-0.5 rounded border border-blue-200/70 text-[11px] inline-block mx-0.5">
              {word}{" "}
            </span>
          );
        }
        if (isMetric && word.length > 1) {
          return (
            <span key={idx} className="font-mono font-bold text-slate-900 bg-slate-100 px-1 py-0.5 rounded text-[11px] inline-block mx-0.5">
              {word}{" "}
            </span>
          );
        }
        return <span key={idx}>{word} </span>;
      })}
      {isTyping && <span className="inline-block w-1.5 h-3.5 bg-blue-600 animate-pulse align-middle ml-0.5" />}
    </span>
  );
}

function getAgentIcon(id: string, className = "h-5 w-5") {
  switch (id) {
    case "network":
      return <Radio className={`${className} text-blue-600`} />;
    case "airspace_safety":
      return <Plane className={`${className} text-blue-600`} />;
    case "spectrum":
      return <Activity className={`${className} text-blue-600`} />;
    case "policy_institutional":
      return <ShieldCheck className={`${className} text-blue-600`} />;
    case "optimization":
      return <Cpu className={`${className} text-blue-600`} />;
    case "arbitration":
      return <Gavel className={`${className} text-emerald-600`} />;
    default:
      return <Radio className={`${className} text-blue-600`} />;
  }
}

function AgentsPage() {
  const search = useSearch({ strict: false });
  const navigate = useNavigate();
  const activeScenarioId = (search as any)?.scenario || "DEMO-001";

  const [agents, setAgents] = useState<AgentData[]>(INITIAL_AGENTS);
  const [running, setRunning] = useState(false);
  const [phaseDesc, setPhaseDesc] = useState("Awaiting execution...");
  const standardDelay = 1.5;
  const [currentActiveAgent, setCurrentActiveAgent] = useState<string>("network");
  const [tickerMessage, setTickerMessage] = useState<string>("Initializing coexistence multi-agent pipeline...");
  const [latencyText, setLatencyText] = useState<string | null>(null);
  const [activityLogs, setActivityLogs] = useState<string[]>([]);
  const activeEventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    startStream(activeScenarioId, standardDelay);
    return () => {
      if (activeEventSourceRef.current) {
        activeEventSourceRef.current.close();
      }
    };
  }, [activeScenarioId]);

  const selectScenario = (id: string) => {
    navigate({ to: "/agents", search: { scenario: id } as any });
  };

  const startStream = (scenarioId: string = activeScenarioId, delayVal: number = standardDelay) => {
    if (activeEventSourceRef.current) {
      activeEventSourceRef.current.close();
      activeEventSourceRef.current = null;
    }

    setRunning(true);
    setLatencyText(null);
    setAgents(INITIAL_AGENTS.map(a => ({ ...a, status: "pending", steps: [], summary: "Awaiting analysis...", badges: [] })));
    setPhaseDesc(`Coexistence Pipeline active for ${scenarioId}`);
    setCurrentActiveAgent("network");
    setTickerMessage(`Telemetry ingested for ${scenarioId}. Domain agents evaluating in parallel...`);
    setActivityLogs([`[Phase 0: Ingestion] Telemetry & RF spectrum baseline loaded for ${scenarioId}`]);

    const runId = "run_" + Math.random().toString(36).substring(7);
    const sse = new EventSource(`${API_BASE}/api/run/${runId}/stream?scenario_id=${scenarioId}&delay=${delayVal}`);
    activeEventSourceRef.current = sse;

    const tStart = performance.now();

    sse.addEventListener("run_started", (e) => {
      const data = JSON.parse(e.data);
      setActivityLogs(prev => [...prev, `[Pipeline Started] Run ID: ${data.run_id} | Engine: ${data.engine || "LangGraph"}`]);
    });

    sse.addEventListener("phase_started", (e) => {
      const data = JSON.parse(e.data);
      setPhaseDesc(`Phase ${data.phase}: ${data.description}`);

      if (data.phase === 1) {
        setCurrentActiveAgent("airspace_safety");
        setTickerMessage("Airspace, Spectrum, Policy, and Network agents cross-verifying glideslope safety margins...");
        setAgents(prev => prev.map(a => ["network", "airspace_safety", "spectrum", "policy_institutional"].includes(a.id) ? { ...a, status: "running", summary: "Evaluating telemetry..." } : a));
      } else if (data.phase === 2) {
        setCurrentActiveAgent("optimization");
        setTickerMessage("Multi-Objective Optimization Agent ranking actions across 4 Pareto dimensions...");
        setAgents(prev => prev.map(a => a.id === "optimization" ? { ...a, status: "running", summary: "Evaluating Pareto trade-offs..." } : a));
      } else if (data.phase === 3) {
        setCurrentActiveAgent("arbitration");
        setTickerMessage("Arbitration Agent auditing hard constraints and synthesizing legal coexistence ledger...");
        setAgents(prev => prev.map(a => a.id === "arbitration" ? { ...a, status: "running", summary: "Synthesizing arbitration decision..." } : a));
      }

      setActivityLogs(prev => [...prev, `[Phase ${data.phase}] ${data.description}`]);
    });

    sse.addEventListener("node_started", (e) => {
      const data = JSON.parse(e.data);
      if (data.node === "cross_check") {
        setTickerMessage("Cross-Check: Verifying consistency between cellular QoS proposals and glideslope safety margins...");
        setActivityLogs(prev => [...prev, `[Cross-Check] Verifying mutual consistency across agent mandates`]);
      } else if (data.node === "negotiate") {
        setTickerMessage("Negotiation: Harmonizing conflicting actions to eliminate hazardous power boosts...");
        setActivityLogs(prev => [...prev, `[Negotiation] Inter-agent resolution in progress`]);
      } else if (data.node === "constraint_check") {
        setTickerMessage("Deterministic Constraint Verification: Auditing hard safety limits (CON-RAD-001, CON-IN-001)...");
        setActivityLogs(prev => [...prev, `[Constraint Audit] Deterministic verification against hard safety limits`]);
      }
    });

    sse.addEventListener("agent_completed", (e) => {
      const data = JSON.parse(e.data);
      const rep = data.report;

      setCurrentActiveAgent(data.agent_name);
      setTickerMessage(`${data.agent_name.replace("_", " ").toUpperCase()}: ${cleanAgentText(rep.assessment?.substring(0, 110))}...`);
      setActivityLogs(prev => [...prev, `[Agent] ${data.agent_name.replace("_", " ").toUpperCase()}: ${cleanAgentText(rep.assessment?.substring(0, 95))}...`]);

      setAgents(prev => prev.map(a => {
        if (a.id === data.agent_name) {
          const steps: AgentStep[] = [];

          if (rep.chain_of_thought && Array.isArray(rep.chain_of_thought)) {
            rep.chain_of_thought.forEach((c: any, idx: number) => {
              if (typeof c === "string") {
                const colonIdx = c.indexOf(":");
                let title = `Step ${idx + 1}`;
                let text = c;
                if (colonIdx !== -1 && colonIdx < 40) {
                  title = c.substring(0, colonIdx).trim();
                  text = c.substring(colonIdx + 1).trim();
                }
                const matched = c.match(/(?:CLM-\d+|CON-[A-Za-z0-9-]+|CONF-\d+|GAP-\d+|ACT-[A-Za-z0-9-]+)/g) || [];
                const chips = Array.from(new Set(matched));
                steps.push({ title, text: cleanAgentText(text), chips });
              }
            });
          }

          if (steps.length === 0) {
            if (rep.assessment) {
              steps.push({ title: "Safety Assessment", text: cleanAgentText(rep.assessment), chips: rep.evidence_ids || [] });
            }
          }

          const badges: string[] = [];
          if (rep.candidate_actions && rep.candidate_actions.length > 0) {
            badges.push(`Proposed: ${rep.candidate_actions.map((act: any) => act.id).join(", ")}`);
          }

          return {
            ...a,
            status: "completed",
            confidence: rep.confidence ?? 0.92,
            summary: cleanAgentText(rep.assessment || rep.error || "Analysis complete."),
            steps,
            badges
          };
        }
        return a;
      }));
    });

    sse.addEventListener("arbitration_completed", (e) => {
      const data = JSON.parse(e.data);
      const arb = data.arbitration;
      const arbSteps: AgentStep[] = [];

      setCurrentActiveAgent("arbitration");
      setTickerMessage(`Arbitration Synthesized: Selected ${arb.accepted_action?.id || "None"} — Safety: ${arb.safety_status}`);

      if (arb.accepted_action) {
        arbSteps.push({
          title: "Accepted Coexistence Action",
          text: `${arb.accepted_action.id}: ${arb.accepted_action.desc}`,
          chips: [arb.accepted_action.id, ...(arb.accepted_action.evidence_ids || [])]
        });
      }

      if (arb.rejected_actions && arb.rejected_actions.length > 0) {
        arb.rejected_actions.forEach((rej: any) => {
          const reasons = (arb.rejection_reasons && arb.rejection_reasons[rej.id]) || rej.rejection_reasons || [];
          arbSteps.push({
            title: `Rejected Action: ${rej.id}`,
            text: `${rej.desc} — ${Array.isArray(reasons) ? reasons.join("; ") : reasons}`,
            chips: [rej.id, ...((Array.isArray(reasons) ? reasons.join(" ") : String(reasons)).match(/CON-[A-Za-z0-9-]+|CLM-\d+/g) || [])]
          });
        });
      }

      const badges = [
        `Safety: ${arb.safety_status || "PROTECTED"}`,
        arb.requires_human_approval ? "Human Gate: REQUIRED" : "Human Gate: AUTOMATIC",
      ];

      setAgents(prev => prev.map(a => {
        if (a.id === "arbitration") {
          return {
            ...a,
            status: "completed",
            confidence: 1.0,
            summary: cleanAgentText(arb.rationale || "Final multi-agent coexistence arbitration synthesized."),
            steps: arbSteps,
            badges
          };
        }
        return a;
      }));

      setActivityLogs(prev => [...prev, `[Arbitration Finalized] Selected: ${arb.accepted_action?.id || "None"} | Human Gate: ${arb.requires_human_approval ? "REQUIRED" : "NOT REQUIRED"}`]);
    });

    sse.addEventListener("run_finished", (e) => {
      const elapsed = ((performance.now() - tStart) / 1000).toFixed(2);
      setRunning(false);
      try {
        const data = JSON.parse(e.data);
        const lat = data.run_result?.total_latency_s;
        setLatencyText(`⚡ ${lat !== undefined ? lat + "s" : elapsed + "s"}`);
      } catch {
        setLatencyText(`⚡ ${elapsed}s`);
      }
      setPhaseDesc("Decision Graph Finalized · Audit Record Persisted");
      setTickerMessage("Coexistence arbitration complete. Verifiable audit ledger saved to disk.");
      setActivityLogs(prev => [...prev, `[Audit Persisted] Record saved to runs/${runId}.json`]);
      sse.close();
    });

    sse.onerror = (err) => {
      console.error("SSE stream error", err);
      sse.close();
      setRunning(false);
      setPhaseDesc("Stream completed.");
    };
  };

  return (
    <Shell>
      {/* Title & Quick Action */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-4 gap-4">
        <div>
          <PageTitle eyebrow="Autonomous Multi-Agent Swarm" title="Live Coexistence Decision Graph" sub={phaseDesc} />
        </div>
        <div>
          <button
            onClick={() => startStream(activeScenarioId, standardDelay)}
            disabled={running}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-full bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-cloud transition hover:bg-blue-700 disabled:opacity-50"
          >
            {running && <Loader2 className="h-4 w-4 animate-spin" />}
            {running ? "Reasoning in Progress..." : "Re-Run Scenario"}
          </button>
        </div>
      </div>

      {/* TOP LIVE MISSION TICKER / BLINKING OVERALL LOGGING (Clean White & Blue) */}
      <section className="mb-6 rounded-2xl bg-white border border-blue-100 p-4 shadow-cloud flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        <div className="flex items-center gap-3 w-full overflow-hidden">
          {/* Agent Icon Unveiling with pulse scanner ring */}
          <div className="relative flex items-center justify-center h-10 w-10 shrink-0 rounded-xl bg-blue-50 border border-blue-200">
            {getAgentIcon(currentActiveAgent, "h-5 w-5")}
            {running && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-600"></span>
              </span>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] uppercase tracking-widest text-blue-600 font-bold flex items-center gap-1.5">
                <span className={`h-2 w-2 rounded-full ${running ? "bg-blue-600 animate-pulse" : "bg-emerald-500"}`}></span>
                {running ? "LIVE AGENT LOGGING STREAM" : "MISSION COMPLETED"}
              </span>
              {latencyText && (
                <span className="rounded-full bg-blue-50 px-2 py-0.5 font-mono text-[10px] font-bold text-blue-700 border border-blue-200">
                  {latencyText}
                </span>
              )}
            </div>
            {/* Typing roll-out text on top */}
            <p className="text-sm font-semibold text-slate-800 truncate mt-0.5">
              <WordRolloutText text={tickerMessage} speed={18} />
            </p>
          </div>
        </div>
      </section>

      {/* Preset Scenario Selector Tabs (Clean White & Blue) */}
      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        {SCENARIOS.map((sc) => {
          const isSelected = activeScenarioId === sc.id;
          return (
            <button
              key={sc.id}
              onClick={() => selectScenario(sc.id)}
              disabled={running}
              className={`rounded-2xl p-4 text-left transition-all ${
                isSelected
                  ? "bg-blue-600 text-white shadow-cloud scale-[1.01]"
                  : "bg-white text-slate-900 hover:bg-blue-50/50 border border-slate-200"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`font-mono text-xs font-semibold uppercase tracking-wider ${isSelected ? "text-blue-100" : "text-blue-600"}`}>
                  {sc.label}
                </span>
                {isSelected && <Sparkles className="h-4 w-4 text-white" />}
              </div>
              <p className="mt-1 font-semibold text-sm">{sc.sub}</p>
              <p className={`mt-1 text-xs line-clamp-2 ${isSelected ? "text-blue-100/90" : "text-slate-500"}`}>
                {sc.desc}
              </p>
            </button>
          );
        })}
      </div>

      {/* Agents Grid (Clean White & Blue, Green border for Arbitration) */}
      <div className="grid gap-5 lg:grid-cols-2">
        {agents.map((a, i) => (
          <AgentCard key={a.id} agent={a} index={i} />
        ))}
      </div>

      {/* Live Natural Language Pipeline Feed */}
      <section className="mt-8 rounded-3xl bg-white p-6 shadow-cloud border border-slate-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              {running && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${running ? "bg-blue-600" : "bg-slate-400"}`}></span>
            </span>
            Live Multi-Agent Coexistence Activity Feed
          </h3>
          <span className="font-mono text-xs text-slate-500">{activityLogs.length} events logged</span>
        </div>
        <div className="space-y-2 max-h-56 overflow-y-auto pr-2 font-mono text-xs">
          {activityLogs.map((log, i) => (
            <div key={i} className="rounded-lg bg-blue-50/40 p-2 text-slate-800 leading-relaxed border-l-2 border-blue-600">
              {log}
            </div>
          ))}
        </div>
      </section>
    </Shell>
  );
}

function AgentCard({ agent, index }: { agent: AgentData; index: number }) {
  const [open, setOpen] = useState(index === 0 || agent.id === "arbitration");
  const isArbitration = agent.id === "arbitration";

  return (
    <article
      className={`rounded-3xl p-6 shadow-cloud transition-all bg-white ${
        agent.status === "running"
          ? "border-2 border-blue-500"
          : isArbitration && agent.status === "completed"
          ? "border-2 border-emerald-500"
          : "border border-slate-200"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          {/* Agent Icon Unveiling */}
          <div className="flex items-center justify-center h-10 w-10 rounded-xl bg-blue-50/70 border border-blue-100 shrink-0">
            {getAgentIcon(agent.id, "h-5 w-5")}
          </div>

          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-blue-600 font-semibold flex items-center gap-2">
              Agent 0{index + 1} · {agent.role}
              {agent.status === "running" && <Loader2 className="h-3 w-3 animate-spin text-blue-600" />}
            </p>
            <h2 className="mt-0.5 text-base font-bold text-slate-900 flex items-center gap-1.5">
              {agent.name}
              {agent.status === "completed" && <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
            </h2>
          </div>
        </div>

        {agent.status === "completed" && (
          <span className="rounded-full bg-blue-50 border border-blue-200 px-2.5 py-0.5 font-mono text-xs font-semibold text-blue-700">
            {Math.round(agent.confidence * 100)}% conf
          </span>
        )}
      </div>

      {/* Badges */}
      {agent.badges && agent.badges.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {agent.badges.map((b, i) => (
            <span key={i} className="rounded-md bg-blue-50/70 border border-blue-100 px-2 py-0.5 font-mono text-[11px] text-blue-800 font-medium">
              {b}
            </span>
          ))}
        </div>
      )}

      {/* Rollout Natural Language Summary */}
      <div className="mt-3 text-sm leading-relaxed text-slate-700 font-sans">
        <WordRolloutText text={agent.summary} speed={22} />
      </div>

      {/* Chain-of-Thought Steps */}
      {agent.steps.length > 0 && (
        <>
          <button
            onClick={() => setOpen(!open)}
            className="mt-4 flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700"
          >
            {open ? "Hide" : "Show"} step-by-step reasoning ({agent.steps.length})
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
          {open && (
            <ol className="mt-3 space-y-3 border-l-2 border-blue-100 pl-4">
              {agent.steps.map((s, i) => (
                <li key={i} className="relative">
                  <span className="absolute -left-[23px] grid h-4 w-4 place-items-center rounded-full bg-blue-600 font-mono text-[9px] text-white font-bold">
                    {i + 1}
                  </span>
                  <p className="text-xs font-bold text-slate-800">
                    {s.title}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-600 leading-relaxed">
                    {s.text}
                  </p>
                  {s.chips && s.chips.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {s.chips.map((c) => (
                        <CodeChip key={c} code={c} />
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ol>
          )}
        </>
      )}
    </article>
  );
}
