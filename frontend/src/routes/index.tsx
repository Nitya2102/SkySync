import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { CheckCircle2, Clock, PlaneLanding, Radio, XCircle } from "lucide-react";
import { Shell, PageTitle } from "@/components/skysync/Shell";
import { CodeChip } from "@/components/skysync/CodeChip";
import { candidateActions, telemetry } from "@/lib/skysync/data";
import { useDictionary } from "@/lib/skysync/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Mission Overview — SkySync Flight Corridor Safety" },
      { name: "description", content: "Live flight telemetry, radar altimeter safety margin and 5G arbitration verdict for runway 09L." },
      { property: "og:title", content: "Mission Overview — SkySync" },
      { property: "og:description", content: "Flight telemetry, PFD safety margin and arbitration verdict." },
    ],
  }),
  component: Overview,
});

function Overview() {
  const navigate = useNavigate();
  const [alt, setAlt] = useState(telemetry.altitudeFt);
  const [hor, setHor] = useState(telemetry.horizontalM);
  const { data: dict } = useDictionary();
  const slant = Math.sqrt((alt * 0.3048) ** 2 + hor ** 2);
  const accepted = candidateActions.find((a) => a.verdict === "accepted")!;
  const rejected = candidateActions.filter((a) => a.verdict === "rejected");

  return (
    <Shell>
      <PageTitle
        eyebrow="Mission Overview & Flight Telemetry"
        title="Runway 09L · Approach in progress"
        sub="One aircraft on final, one 5G tower nearby. Here is whether they can safely share the sky."
      />

      {/* Telemetry Status Banner (Clean White & Blue) */}
      <section className="grid gap-4 rounded-3xl bg-white p-6 shadow-cloud border border-blue-100/80 md:grid-cols-4">
        <Stat icon={<PlaneLanding className="h-4 w-4 text-blue-600" />} label="Runway" value={telemetry.runway} />
        <Stat icon={<Radio className="h-4 w-4 text-blue-600" />} label="Approach Category" value={telemetry.approach} />
        <Stat label="Height over threshold" value={`${alt} ft AGL`} />
        <Stat label="Slant distance to BS-17" value={`${slant.toFixed(0)} m`} />
        <div className="grid gap-6 border-t border-slate-100 pt-5 md:col-span-4 md:grid-cols-2">
          <Slider label="Aircraft altitude (ft AGL)" min={100} max={1500} value={alt} onChange={setAlt} />
          <Slider label="Horizontal distance to tower (m)" min={100} max={3000} value={hor} onChange={setHor} />
        </div>
      </section>

      {/* Safety Gauge & Coexistence Verdict */}
      <section className="mt-6 grid gap-6 md:grid-cols-[1.2fr_1fr]">
        {/* Radar Altimeter Margin (Clean White & Blue) */}
        <div className="rounded-3xl bg-white p-6 shadow-cloud border border-blue-100/80">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">Radar Altimeter Safety Margin</h2>
            <span className="font-mono text-xs text-blue-600 font-medium">ITU RR 5.438</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Signal isolation between 5G emissions and aircraft radar altimeter.
          </p>
          <Gauge margin={telemetry.margin} threshold={telemetry.threshold} />
          <div className="mt-4 grid grid-cols-3 gap-3 text-center">
            <Mini label="Power Flux Density" value={`${telemetry.pfd}`} unit="dBW/m²/MHz" />
            <Mini label="Safety margin" value={`+${telemetry.margin}`} unit="dB" good />
            <Mini label="ICAO minimum" value={`${telemetry.threshold}.0`} unit="dB" />
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <CodeChip code="CLM-106" />
            <CodeChip code="CLM-118" />
            <CodeChip code="CON-201" />
          </div>
        </div>

        {/* Verdict Cards (Green Border for Accepted, Red Border for Rejected, Clean White/Blue background) */}
        <div className="flex flex-col gap-4">
          {/* Accepted Action Card (White background + Green Border) */}
          <div className="rounded-3xl bg-white p-6 shadow-cloud border-2 border-emerald-500">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-700">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                Accepted Action
              </div>
              <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-emerald-700 border border-emerald-200">
                PASS CLEARANCE
              </span>
            </div>
            <h3 className="mt-3 text-lg font-bold text-slate-900">
              {accepted.code}: {dict[accepted.code]?.title || "Off-Corridor Traffic Steering"}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              {accepted.rationale}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {accepted.cites.map((c) => (
                <CodeChip key={c} code={c} />
              ))}
            </div>
          </div>

          {/* Rejected Action Card (White background + Red Border) */}
          {rejected.map((r) => (
            <div key={r.code} className="rounded-2xl bg-white p-5 shadow-cloud border-2 border-rose-500">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-rose-700">
                  <XCircle className="h-4 w-4 text-rose-600" />
                  Rejected: {r.code}
                </div>
                <span className="rounded-full bg-rose-50 px-2 py-0.5 font-mono text-[10px] font-semibold text-rose-700 border border-rose-200">
                  SAFETY VIOLATION
                </span>
              </div>
              <p className="mt-2 text-sm font-semibold text-slate-900">
                {dict[r.code]?.title || "Power Boost"}
              </p>
              <p className="mt-1 text-xs text-slate-600 leading-relaxed">
                {r.rationale}
              </p>
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {r.violates?.map((v) => (
                  <CodeChip key={v} code={v} />
                ))}
              </div>
            </div>
          ))}

          {/* Fast Navigation to Swarm */}
          <div className="flex flex-col gap-2 pt-2">
            <button
              onClick={() => navigate({ to: "/agents" })}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-cloud transition hover:bg-blue-700"
            >
              Open Live Multi-Agent Swarm
            </button>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => navigate({ to: "/agents", search: { scenario: "DEMO-001" } as any })}
                className="rounded-xl border border-blue-200 bg-blue-50/50 p-2 text-center text-[11px] font-medium text-blue-700 hover:bg-blue-100/60 transition"
              >
                Demo 1: Final Approach
              </button>
              <button
                onClick={() => navigate({ to: "/agents", search: { scenario: "DEMO-002" } as any })}
                className="rounded-xl border border-blue-200 bg-blue-50/50 p-2 text-center text-[11px] font-medium text-blue-700 hover:bg-blue-100/60 transition"
              >
                Demo 2: Touchdown Flare
              </button>
              <button
                onClick={() => navigate({ to: "/agents", search: { scenario: "DEMO-003" } as any })}
                className="rounded-xl border border-blue-200 bg-blue-50/50 p-2 text-center text-[11px] font-medium text-blue-700 hover:bg-blue-100/60 transition"
              >
                Demo 3: CAT III Autoland
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Candidate Actions (Clean White Cards with subtle Blue highlights) */}
      <section className="mt-10">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Candidate Actions Pool</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {candidateActions.map((a) => (
            <div key={a.code} className="rounded-2xl bg-white p-5 shadow-cloud border border-slate-200">
              <div className="flex items-center justify-between">
                <CodeChip code={a.code} />
                <VerdictPill v={a.verdict} />
              </div>
              <p className="mt-3 text-sm text-slate-800 font-medium">{a.plain}</p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <Bar label="Safety Margin" v={a.safety} />
                <Bar label="Network QoS" v={a.qos} />
              </div>
            </div>
          ))}
        </div>
      </section>
    </Shell>
  );
}

function Stat({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div>
      <p className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">{icon}{label}</p>
      <p className="mt-1 font-mono text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}

function Mini({ label, value, unit, good }: { label: string; value: string; unit: string; good?: boolean }) {
  return (
    <div className="rounded-xl bg-blue-50/50 border border-blue-100 p-3">
      <p className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">{label}</p>
      <p className={`font-mono text-lg font-bold ${good ? "text-emerald-600" : "text-slate-900"}`}>{value}</p>
      <p className="font-mono text-[10px] text-slate-500">{unit}</p>
    </div>
  );
}

function Slider({ label, min, max, value, onChange }: { label: string; min: number; max: number; value: number; onChange: (n: number) => void }) {
  return (
    <label className="block">
      <span className="flex justify-between text-xs text-slate-600 font-medium">
        <span>{label}</span>
        <span className="font-mono text-blue-600 font-bold">{value}</span>
      </span>
      <input type="range" min={min} max={max} value={value} onChange={(e) => onChange(+e.target.value)} className="mt-2 w-full accent-blue-600" />
    </label>
  );
}

function Bar({ label, v }: { label: string; v: number }) {
  return (
    <div>
      <div className="flex justify-between text-[11px] text-slate-500 font-medium">
        <span>{label}</span>
        <span className="font-mono text-slate-800 font-semibold">{v}%</span>
      </div>
      <div className="mt-1 h-1.5 rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-blue-600" style={{ width: `${v}%` }} />
      </div>
    </div>
  );
}

export function VerdictPill({ v }: { v: "accepted" | "rejected" | "pending" }) {
  if (v === "accepted") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold text-emerald-700 bg-white border border-emerald-500">
        <CheckCircle2 className="h-3 w-3 text-emerald-600" />
        Accepted
      </span>
    );
  }
  if (v === "rejected") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold text-rose-700 bg-white border border-rose-500">
        <XCircle className="h-3 w-3 text-rose-600" />
        Rejected
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold text-slate-600 bg-white border border-slate-300">
      <Clock className="h-3 w-3 text-slate-400" />
      On Hold
    </span>
  );
}

function Gauge({ margin, threshold }: { margin: number; threshold: number }) {
  const max = 60;
  const pct = Math.min(margin / max, 1);
  const angle = Math.PI * (1 - pct);
  const tAngle = Math.PI * (1 - threshold / max);
  const pt = (a: number, r: number) => [100 + r * Math.cos(a), 100 - r * Math.sin(a)];
  const [nx, ny] = pt(angle, 70);
  const [tx1, ty1] = pt(tAngle, 62);
  const [tx2, ty2] = pt(tAngle, 92);
  const [ex, ey] = pt(angle, 80);

  return (
    <svg viewBox="0 0 200 115" className="mx-auto mt-4 w-full max-w-sm">
      <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="#e2e8f0" strokeWidth="14" strokeLinecap="round" />
      <path d={`M20 100 A80 80 0 0 1 ${ex} ${ey}`} fill="none" stroke="#2563eb" strokeWidth="14" strokeLinecap="round" />
      <line x1={tx1} y1={ty1} x2={tx2} y2={ty2} stroke="#f43f5e" strokeWidth="2.5" />
      <line x1="100" y1="100" x2={nx} y2={ny} stroke="#0f172a" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="100" cy="100" r="5" fill="#0f172a" />
      <text x="100" y="80" textAnchor="middle" fill="#1e3a8a" className="font-mono text-[16px] font-bold">
        +{margin} dB
      </text>
    </svg>
  );
}
