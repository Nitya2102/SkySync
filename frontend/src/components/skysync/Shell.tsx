import { Link } from "@tanstack/react-router";
import { Plane } from "lucide-react";
import type { ReactNode } from "react";
import { useHealth } from "@/lib/skysync/api";

const tabs = [
  { to: "/", label: "Mission Overview" },
  { to: "/agents", label: "Agent Swarm" },
  { to: "/pipeline", label: "Decision Pipeline" },
  { to: "/ledger", label: "Regulatory Ledger" },
] as const;

export function Shell({ children }: { children: ReactNode }) {
  const { data } = useHealth();
  return (
    <div className="min-h-screen bg-sky-gradient">
      <header className="sticky top-0 z-30 border-b border-border/70 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-6 py-4">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary text-primary-foreground shadow-cloud">
              <Plane className="h-4 w-4 -rotate-45" />
            </span>
            <span className="leading-tight">
              <span className="block text-base font-bold tracking-tight text-foreground">SkySync</span>
              <span className="block text-[11px] text-muted-foreground">Aerodrome Corridor & 5G Coexistence</span>
            </span>
          </Link>
          <nav className="order-3 flex w-full gap-1 overflow-x-auto rounded-full bg-secondary p-1 md:order-none md:ml-8 md:w-auto">
            {tabs.map((t) => (
              <Link
                key={t.to}
                to={t.to}
                activeOptions={{ exact: true }}
                className="whitespace-nowrap rounded-full px-4 py-1.5 text-sm text-muted-foreground transition hover:text-foreground"
                activeProps={{ className: "bg-card text-foreground shadow-sm font-medium" }}
              >
                {t.label}
              </Link>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2 rounded-full bg-mint px-3 py-1.5 text-xs text-mint-ink">
            <span className="h-2 w-2 animate-pulse rounded-full bg-mint-ink" />
            Autonomous Aerospace Reasoning Engine (Active & Online)
            {data && !data.live && <span className="opacity-70">· demo data</span>}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-10">{children}</main>
    </div>
  );
}

export function PageTitle({ eyebrow, title, sub }: { eyebrow: string; title: string; sub?: string }) {
  return (
    <div className="mb-8">
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-primary">{eyebrow}</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground md:text-4xl">{title}</h1>
      {sub && <p className="mt-2 max-w-2xl text-muted-foreground">{sub}</p>}
    </div>
  );
}
