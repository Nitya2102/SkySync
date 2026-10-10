import { useQuery } from "@tanstack/react-query";
import { mockDictionary, type DictEntry } from "./data";

export const API_BASE = "http://localhost:8000";

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 30000);
  try {
    const r = await fetch(`${API_BASE}${path}`, { ...init, signal: ctrl.signal });
    if (!r.ok) throw new Error(String(r.status));
    return (await r.json()) as T;
  } finally {
    clearTimeout(t);
  }
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      try {
        const h = await getJson<{ documents?: number }>("/api/health");
        return { online: true, live: true, documents: h.documents ?? 0 };
      } catch {
        return { online: true, live: false, documents: 42 };
      }
    },
    staleTime: 30_000,
    retry: false,
  });
}

export function useDictionary() {
  return useQuery({
    queryKey: ["dictionary"],
    queryFn: async () => {
      try {
        const d = await getJson<any>("/api/kb/dictionary");
        const map: Record<string, DictEntry> = {};
        if (d && typeof d === "object") {
          if (d.entries && typeof d.entries === "object") {
            Object.assign(map, d.entries);
          }
          for (const [k, v] of Object.entries<any>(d)) {
            if (v && typeof v === "object" && (v.code || v.title || v.id)) {
              const code = v.code || v.id || k;
              map[code] = {
                code,
                title: v.title || code,
                explanation: v.explanation || v.summary || v.rule || v.description || "",
                source: v.source || v.authority || "Regulatory Standard",
                tier: v.tier || "Regulatory",
                kind: v.kind || (code.startsWith("CLM") ? "claim" : code.startsWith("CON") ? "constraint" : code.startsWith("GAP") ? "gap" : code.startsWith("ACT") ? "action" : "conflict"),
                value: v.value,
              };
            }
          }
        }
        return { ...mockDictionary, ...map };
      } catch {
        return mockDictionary;
      }
    },
    initialData: mockDictionary,
    initialDataUpdatedAt: 0,
    staleTime: 60_000,
    retry: false,
  });
}

export async function runArbitration() {
  try {
    return { live: true, data: await getJson<unknown>("/api/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ as_of: "2026-10-07" }) }) };
  } catch {
    await new Promise((r) => setTimeout(r, 900));
    return { live: false, data: null };
  }
}
