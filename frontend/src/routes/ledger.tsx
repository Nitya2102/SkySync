import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Shell, PageTitle } from "@/components/skysync/Shell";
import { CodeChip } from "@/components/skysync/CodeChip";
import { ledger, type Status } from "@/lib/skysync/data";
import { useDictionary } from "@/lib/skysync/api";

export const Route = createFileRoute("/ledger")({
  head: () => ({
    meta: [
      { title: "Regulatory Ledger & Knowledge Explorer — SkySync" },
      { name: "description", content: "Every constraint check with pass, fail or unverified status, plus a searchable aviation and spectrum knowledge base." },
      { property: "og:title", content: "Regulatory Ledger — SkySync" },
      { property: "og:description", content: "Constraint checks and searchable aviation and spectrum claims." },
    ],
  }),
  component: LedgerPage,
});

const pill: Record<Status, string> = {
  PASS: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  FAIL: "bg-rose-50 text-rose-700 border border-rose-200",
  UNKNOWN: "bg-amber-50 text-amber-700 border border-amber-200",
  UNVERIFIED: "bg-amber-50 text-amber-700 border border-amber-200",
};

function LedgerPage() {
  const [f, setF] = useState<Status | "ALL">("ALL");
  const [q, setQ] = useState("");
  const { data: dict } = useDictionary();
  const rows = ledger.filter((r) => f === "ALL" || r.status === f || (f === "UNVERIFIED" && r.status === "UNKNOWN"));
  const entries = useMemo(() => Object.values(dict).filter((e) => (e.code + e.title + e.explanation + e.source).toLowerCase().includes(q.toLowerCase())), [dict, q]);

  return (
    <Shell>
      <PageTitle eyebrow="Regulatory Ledger & Knowledge Explorer" title="Every rule, checked" sub="The constraint engine follows rules, not opinions. Each line shows what was checked and why." />
      <section className="rounded-3xl bg-card p-6 shadow-cloud">
        <div className="mb-4 flex flex-wrap gap-2">
          {(["ALL", "PASS", "FAIL", "UNVERIFIED"] as const).map((s) => (
            <button key={s} onClick={() => setF(s)} className={`rounded-full px-3 py-1 font-mono text-xs transition ${f === s ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:text-foreground"}`}>{s}</button>
          ))}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground"><th className="py-2 pr-4">Constraint</th><th className="pr-4">Action</th><th className="pr-4">Status</th><th className="pr-4">Reason</th><th>Citations</th></tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-border/60 last:border-0">
                  <td className="py-3 pr-4"><CodeChip code={r.constraint} /></td>
                  <td className="pr-4"><CodeChip code={r.action} /></td>
                  <td className="pr-4"><span className={`rounded-full px-2.5 py-0.5 font-mono text-xs font-medium ${pill[r.status]}`}>{r.status === "UNKNOWN" ? "UNVERIFIED" : r.status}</span></td>
                  <td className="pr-4 text-foreground/90">{r.reason}</td>
                  <td><div className="flex flex-wrap gap-1">{r.cites.length ? r.cites.map((c) => <CodeChip key={c} code={c} />) : <span className="text-xs text-muted-foreground">—</span>}</div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-foreground">Knowledge base</h2>
          <label className="flex items-center gap-2 rounded-full bg-card px-4 py-2 shadow-cloud">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search claims, rules, sources…" className="w-64 bg-transparent text-sm outline-none placeholder:text-muted-foreground" />
          </label>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {entries.map((e) => (
            <div key={e.code} className="rounded-2xl bg-card p-5 shadow-cloud">
              <div className="flex items-center justify-between"><CodeChip code={e.code} /><span className="text-[10px] uppercase tracking-wider text-muted-foreground">{e.kind}</span></div>
              <h3 className="mt-3 text-sm font-semibold text-foreground">{e.title}</h3>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{e.explanation}</p>
              <p className="mt-3 text-[11px] text-foreground/70">{e.source} · {e.tier}{e.value && <span className="ml-2 font-mono text-primary">{e.value}</span>}</p>
            </div>
          ))}
          {!entries.length && <p className="text-sm text-muted-foreground">Nothing matches “{q}”.</p>}
        </div>
      </section>
    </Shell>
  );
}
