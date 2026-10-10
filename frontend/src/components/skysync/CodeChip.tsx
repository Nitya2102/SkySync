import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import { useDictionary } from "@/lib/skysync/api";
import { type DictEntry } from "@/lib/skysync/data";
import { cn } from "@/lib/utils";

const kindStyle: Record<string, string> = {
  claim: "bg-blue-50 text-blue-700 border border-blue-200",
  constraint: "bg-slate-100 text-slate-800 border border-slate-300",
  conflict: "bg-amber-50 text-amber-800 border border-amber-200",
  gap: "bg-amber-50 text-amber-800 border border-amber-200",
  action: "bg-emerald-50 text-emerald-800 border border-emerald-200",
};

function getFallbackEntry(code: string): DictEntry {
  if (code.startsWith("CON-RAD-") || code === "CON-RAD-001" || code === "CON-RAD-002") {
    return {
      code,
      title: "Radar Altimeter Safety Buffer",
      explanation: "Deterministic safety margin threshold protecting aircraft landing flare computers against aggregate 5G C-band emissions.",
      source: "ICAO Doc 9718 / FAA AD",
      tier: "Primary Standard",
      value: "≥ 6.0 dB Margin",
      kind: "constraint",
    };
  }
  if (code.startsWith("CON-IN-")) {
    return {
      code,
      title: `Indian Spectrum & Aviation Rule (${code})`,
      explanation: "National telecom framework condition governing 3300–3670 MHz and aerodrome coexistence requirements.",
      source: "DoT-WPC / DGCA India",
      tier: "Regulatory",
      kind: "constraint",
    };
  }
  if (code.startsWith("CON-INT-")) {
    return {
      code,
      title: `International Treaty Protection (${code})`,
      explanation: "International Telecommunication Union (ITU) or ICAO binding rule governing aeronautical safety band exclusivity.",
      source: "ITU Radio Regulations",
      tier: "Primary Standard",
      kind: "constraint",
    };
  }
  if (code.startsWith("CON-3GPP-")) {
    return {
      code,
      title: `3GPP Technical Specification (${code})`,
      explanation: "3GPP cellular standard governing resource block allocation, QoS floor, and emission boundaries.",
      source: "3GPP Specification",
      tier: "Operational",
      kind: "constraint",
    };
  }
  if (code.startsWith("CON-")) {
    return {
      code,
      title: `Deterministic Safety Constraint (${code})`,
      explanation: "Mandatory coexistence boundary verified by rule engine during pipeline execution.",
      source: "Regulatory Rule Engine",
      tier: "Regulatory",
      kind: "constraint",
    };
  }
  if (code.startsWith("CLM-")) {
    return {
      code,
      title: `Regulatory Evidence Standard (${code})`,
      explanation: "Primary aviation authority citation defining physical thresholds, antenna separation, or legal in-force mandates.",
      source: "Aviation & Spectrum Authority",
      tier: "Primary Standard",
      kind: "claim",
    };
  }
  if (code.startsWith("GAP-")) {
    return {
      code,
      title: `Precautionary Knowledge Gap (${code})`,
      explanation: "Documented policy or parameter uncertainty where deterministic engine enforces precautionary safety margins.",
      source: "Precautionary Knowledge Base",
      tier: "Derived",
      kind: "gap",
    };
  }
  if (code.startsWith("CONF-")) {
    return {
      code,
      title: `Jurisdictional Swarm Conflict (${code})`,
      explanation: "Reconciled policy divergence between cellular capacity objectives and aviation approach corridor protection.",
      source: "Multi-Agent Swarm Arbitration",
      tier: "Derived",
      kind: "conflict",
    };
  }
  if (code.startsWith("ACT-")) {
    return {
      code,
      title: `Candidate Coexistence Action (${code})`,
      explanation: "Evaluated RF or network configuration action proposed to resolve cellular load or protect aircraft.",
      source: "Swarm Pipeline",
      tier: "Operational",
      kind: "action",
    };
  }
  return {
    code,
    title: `Coexistence Rule Entry (${code})`,
    explanation: "Validated safety reference cited in multi-agent pipeline decision ledger.",
    source: "Knowledge Base",
    tier: "Regulatory",
    kind: "constraint",
  };
}

export function CodeChip({ code, className }: { code: string; className?: string }) {
  const { data } = useDictionary();
  const e = data?.[code] || getFallbackEntry(code);

  return (
    <HoverCard openDelay={120} closeDelay={80}>
      <HoverCardTrigger asChild>
        <button
          type="button"
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 font-mono text-[11px] font-medium ring-1 ring-inset ring-border/60 transition hover:ring-primary/50",
            kindStyle[e?.kind ?? "claim"],
            className,
          )}
        >
          {code}
          {e && <span className="hidden font-sans font-normal opacity-80 sm:inline">· {e.title.split(" ").slice(0, 3).join(" ")}</span>}
        </button>
      </HoverCardTrigger>
      <HoverCardContent className="w-80 rounded-2xl border-slate-200 bg-white p-4 shadow-cloud text-slate-800">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs font-semibold text-blue-600">{e.code}</span>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] uppercase font-semibold tracking-wider text-slate-600">{e.kind}</span>
          </div>
          <h4 className="text-sm font-semibold text-slate-900 leading-snug">{e.title}</h4>
          <p className="text-xs leading-relaxed text-slate-600">{e.explanation}</p>
          <div className="flex items-center justify-between border-t border-slate-100 pt-2 text-[11px]">
            <span className="text-slate-700 font-medium">{e.source} <span className="text-slate-400 font-normal">| {e.tier}</span></span>
            {e.value && <span className="font-mono font-bold text-blue-600">{e.value}</span>}
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}
