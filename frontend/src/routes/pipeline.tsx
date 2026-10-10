import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Shell, PageTitle } from "@/components/skysync/Shell";
import { graph } from "@/lib/skysync/data";

export const Route = createFileRoute("/pipeline")({
  head: () => ({
    meta: [
      { title: "Decision Pipeline Graph — SkySync" },
      { name: "description", content: "Interactive graph of how telemetry flows through agents, optimisation and the constraint engine to the safety ledger." },
      { property: "og:title", content: "Decision Pipeline Graph — SkySync" },
      { property: "og:description", content: "Follow the decision from telemetry to final safety ledger." },
    ],
  }),
  component: PipelinePage,
});

const W = 190, H = 56, CX = 230, RY = 105;
const pos = (n: (typeof graph.nodes)[number]) => ({ x: 20 + n.col * CX, y: 30 + n.row * RY });

function PipelinePage() {
  const [sel, setSel] = useState("airspace");
  const [hover, setHover] = useState<string | null>(null);
  const active = hover ?? sel;
  const node = graph.nodes.find((n) => n.id === active)!;
  const linked = new Set(graph.edges.filter((e) => e.includes(active)).flat());

  return (
    <Shell>
      <PageTitle eyebrow="Agent Planning & Decision Pipeline" title="How a decision is made" sub="Hover or click any step to see what it does and what it listens to." />
      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <div className="overflow-x-auto rounded-3xl bg-card p-4 shadow-cloud">
          <svg viewBox="0 0 1150 420" className="min-w-[900px]">
            <defs>
              <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" className="fill-primary/60" /></marker>
            </defs>
            {graph.edges.map(([a, b]) => {
              const A = pos(graph.nodes.find((n) => n.id === a)!), B = pos(graph.nodes.find((n) => n.id === b)!);
              const x1 = A.x + W, y1 = A.y + H / 2, x2 = B.x, y2 = B.y + H / 2, mx = (x1 + x2) / 2;
              const on = a === active || b === active;
              return <path key={a + b} d={`M${x1} ${y1} C${mx} ${y1} ${mx} ${y2} ${x2 - 2} ${y2}`} fill="none" markerEnd="url(#arr)" className={on ? "stroke-primary" : "stroke-border"} strokeWidth={on ? 2.5 : 1.5} strokeDasharray={on ? "6 4" : undefined} style={on ? { animation: "dash 1s linear infinite" } : undefined} />;
            })}
            {graph.nodes.map((n) => {
              const p = pos(n), on = n.id === active, near = linked.has(n.id);
              return (
                <g key={n.id} transform={`translate(${p.x},${p.y})`} className="cursor-pointer" onMouseEnter={() => setHover(n.id)} onMouseLeave={() => setHover(null)} onClick={() => setSel(n.id)}>
                  <rect width={W} height={H} rx="16" className={on ? "fill-primary" : near ? "fill-sky-tint stroke-primary/40" : "fill-background stroke-border"} strokeWidth="1.5" />
                  <text x={W / 2} y={H / 2 + 4} textAnchor="middle" className={`text-[12.5px] font-semibold ${on ? "fill-primary-foreground" : "fill-foreground"}`}>{n.label}</text>
                </g>
              );
            })}
          </svg>
        </div>
        <aside className="rounded-3xl bg-card p-6 shadow-cloud">
          <p className="font-mono text-[11px] uppercase tracking-widest text-primary">Selected step</p>
          <h2 className="mt-1 text-lg font-semibold text-foreground">{node.label}</h2>
          <p className="mt-2 text-sm text-muted-foreground">{node.role}</p>
          <p className="mt-5 text-xs font-semibold uppercase tracking-wider text-foreground">Inputs</p>
          <ul className="mt-2 space-y-1.5">{node.inputs.map((i) => <li key={i} className="rounded-lg bg-secondary px-3 py-1.5 font-mono text-xs text-foreground">{i}</li>)}</ul>
        </aside>
      </div>
    </Shell>
  );
}
