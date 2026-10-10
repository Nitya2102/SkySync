"""FastAPI application for 5G–Airspace Coexistence and Safety Optimization.

Supports two execution engines:
  1. LangGraph (default) — stateful multi-agent graph with conflict negotiation,
     feedback loops, and human-in-the-loop gates.
  2. Legacy Orchestrator (fallback) — procedural pipeline (set USE_LANGGRAPH=0).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import KB_DIR, ROOT_DIR, RUNS_DIR, MOCK_LLM, USE_LANGGRAPH
from app.groq_client import groq_client
from app.models import (
    CandidateAction,
    CellState,
    AircraftState,
    RunRequest,
    RunResult,
    SimulationState,
)
from app.orchestrator import orchestrator
from app.rag.hybrid_retriever import hybrid_retriever

# LangGraph runner (lazy import to avoid startup cost if disabled)
if USE_LANGGRAPH:
    from app.graph.runner import graph_runner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SkySync")

app = FastAPI(
    title="SkySync: Real-Time 5G–Airspace Coexistence & Safety Optimization",
    description="Multi-agent safety arbitration engine with deterministic constraint checking",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active run streams
active_runs: dict[str, dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing SkySync services...")
    hybrid_retriever.load()
    await groq_client.initialize()

    # Initialize LLM provider if available
    if USE_LANGGRAPH:
        try:
            from app.llm.provider import llm_provider
            await llm_provider.initialize()
            logger.info("LangGraph engine active. LLM provider: %s", llm_provider.active_provider)
        except Exception as e:
            logger.warning("LLM provider init failed: %s. Agents will use GroqClient.", e)

    engine = "LangGraph" if USE_LANGGRAPH else "Legacy Orchestrator"
    logger.info(
        "SkySync ready. Engine: %s, Reason model: %s, Fast model: %s",
        engine, groq_client.active_reason_model, groq_client.active_fast_model,
    )


@app.get("/api/health")
async def health_check():
    engine_info = {
        "type": "langgraph" if USE_LANGGRAPH else "legacy_orchestrator",
        "features": [],
    }
    if USE_LANGGRAPH:
        engine_info["features"] = [
            "conflict_negotiation",
            "feedback_loops",
            "human_in_the_loop",
            "checkpointing",
            "concurrent_fan_out",
        ]

    return {
        "status": "healthy",
        "engine": engine_info,
        "mode": "autonomous_active",
        "kb_docs": hybrid_retriever.doc_count,
        "kb_claims": len(hybrid_retriever.claims_by_id),
        "kb_chunks": len(hybrid_retriever.chunks_by_id),
    }


@app.get("/api/scenarios")
async def get_scenarios():
    scenarios_file = KB_DIR / "scenarios.json"
    if scenarios_file.exists():
        return json.loads(scenarios_file.read_text(encoding="utf-8"))
    seed_file = KB_DIR / "scenario_seed.json"
    if seed_file.exists():
        data = json.loads(seed_file.read_text(encoding="utf-8"))
        return [data]
    return []


@app.get("/api/kb/dictionary")
async def get_kb_dictionary():
    """Returns human-friendly descriptions for all claims, constraints, conflicts, and gaps."""
    # Sources lookup
    src_file = KB_DIR / "sources.csv"
    src_map = {}
    if src_file.exists():
        import csv
        for r in csv.DictReader(open(src_file, encoding="utf-8")):
            src_map[r["source_id"]] = r.get("title", r["source_id"])

    # Claims
    claims_dict = {}
    for cid, c in hybrid_retriever.claims_by_id.items():
        src_title = src_map.get(c.get("source_id", ""), c.get("source_id", "Aviation Authority"))
        claims_dict[cid] = {
            "id": cid,
            "title": f"{c.get('subject', 'Standard').replace('-', ' ').title()} ({c.get('jurisdiction', 'Global')})",
            "summary": c.get("claim", ""),
            "authority": src_title,
            "legal_status": c.get("legal_status", "in_force"),
            "effective_from": c.get("effective_from"),
            "verification": c.get("verification", "primary"),
            "numeric": c.get("numeric", {}),
        }

    # Constraints
    cons_dict = {}
    for con in hybrid_retriever.constraints:
        cons_dict[con["constraint_id"]] = {
            "id": con["constraint_id"],
            "title": con.get("title", "Safety Constraint"),
            "rule": con.get("rule", ""),
            "type": con.get("type", "HARD"),
            "legal_status": con.get("legal_status", "in_force"),
            "effective_from": con.get("effective_from"),
            "evidence_claims": con.get("evidence_claims", []),
        }

    # Conflicts
    conf_dict = {}
    for conf in hybrid_retriever.conflicts:
        conf_dict[conf["conflict_id"]] = {
            "id": conf["conflict_id"],
            "title": conf.get("topic", "Jurisdictional Conflict"),
            "positions": conf.get("positions", []),
            "handling": conf.get("handling", "Retain all; cite uncertainty"),
        }

    # Policy Gaps
    gaps_dict = {}
    for gap in hybrid_retriever.gaps:
        gaps_dict[gap["gap_id"]] = {
            "id": gap["gap_id"],
            "title": gap.get("title", "Policy Gap"),
            "description": gap.get("description", ""),
            "type": gap.get("type", "gap"),
        }

    # Actions
    actions_dict = {
        "ACT-1": {
            "id": "ACT-1",
            "title": "Increase Cellular Power (+3 dB)",
            "summary": "Boost base station RF output to recover degraded user throughput and PRB congestion.",
            "category": "Transmission Power",
            "risk": "High (Expands RF interference contour towards runway glideslope)",
        },
        "ACT-2": {
            "id": "ACT-2",
            "title": "Off-Corridor Traffic Steering (>1200 m)",
            "summary": "Handover high-bandwidth edge user equipments to an adjacent cell located over 1200 m away from runway threshold.",
            "category": "Traffic Management",
            "risk": "Zero (Maintains safe physical separation; reduces emissions in approach zone)",
        },
        "ACT-3": {
            "id": "ACT-3",
            "title": "Antenna Downtilt 3° + PRB Power Capping",
            "summary": "Mechanically tilt antenna downward and cap resource-block power to shield aircraft above 450 ft.",
            "category": "RF Beam Shaping",
            "risk": "Low (Requires verification that simulated safety margin exceeds 6 dB)",
        },
        "ACT-4": {
            "id": "ACT-4",
            "title": "Activate 4100 MHz (n77 Upper Carrier)",
            "summary": "Switch cellular carrier frequency to 4100 MHz to bypass lower band PRB congestion.",
            "category": "Spectrum Retuning",
            "risk": "Critical (Violates national band license in India and abuts protected 4200–4400 MHz radar altimeter band)",
        },
    }

    # Format all items into unified DictEntry mapping
    entries = {}

    for cid, c in claims_dict.items():
        val = ""
        if c.get("numeric"):
            num = c["numeric"]
            if "margin_db" in num:
                val = f"Margin: {num['margin_db']} dB"
            elif "power_limit_dbm" in num:
                val = f"Limit: {num['power_limit_dbm']} dBm"
            elif "frequency_mhz" in num:
                val = f"{num['frequency_mhz']} MHz"
        entries[cid] = {
            "code": cid,
            "title": c["title"],
            "explanation": c["summary"],
            "source": c["authority"],
            "tier": "Primary Standard" if "primary" in c.get("verification", "") else "Regulatory",
            "kind": "claim",
            "value": val or None,
        }

    for kid, k in cons_dict.items():
        entries[kid] = {
            "code": kid,
            "title": k["title"],
            "explanation": k["rule"],
            "source": f"{k.get('jurisdiction', 'International').title()} Standard",
            "tier": "Regulatory" if k.get("type") == "HARD" else "Advisory",
            "kind": "constraint",
            "value": f"Type: {k.get('type', 'HARD')}",
        }

    for fid, f in conf_dict.items():
        entries[fid] = {
            "code": fid,
            "title": f["title"],
            "explanation": f["handling"],
            "source": "Inter-Agency Arbitration",
            "tier": "Derived",
            "kind": "conflict",
        }

    for gid, g in gaps_dict.items():
        entries[gid] = {
            "code": gid,
            "title": g["title"],
            "explanation": g["description"],
            "source": "Precautionary Knowledge Base",
            "tier": "Derived",
            "kind": "gap",
        }

    for aid, a in actions_dict.items():
        entries[aid] = {
            "code": aid,
            "title": a["title"],
            "explanation": f"{a['summary']} Risk: {a['risk']}",
            "source": "Swarm Mitigation Candidate",
            "tier": "Operational",
            "kind": "action",
        }

    # Add legacy and synthetic aliases so all UI cards resolve
    aliases = {
        "CON-201": { "code": "CON-201", "title": "Minimum Safety Margin ≥ 6 dB", "explanation": "Hard deterministic constraint: computed margin must exceed the ICAO buffer under worst-case geometry.", "source": "Derived from CLM-106", "tier": "Derived", "value": "≥ 6.0 dB", "kind": "constraint" },
        "CON-204": { "code": "CON-204", "title": "No Power Increase Inside Corridor", "explanation": "Base station EIRP may not increase for cells whose main lobe intersects the approach corridor.", "source": "FAA AD 2023-11-07", "tier": "Regulatory", "kind": "constraint" },
        "CON-207": { "code": "CON-207", "title": "Upper C-Band Activation Freeze", "explanation": "Carriers above 4000 MHz may not be activated within 2 NM of an active CAT II/III runway.", "source": "National Spectrum Policy", "tier": "Regulatory", "value": "Radius: 2 NM", "kind": "constraint" },
        "CON-210": { "code": "CON-210", "title": "Network QoS Floor", "explanation": "Mitigations must preserve at least 85% of subscriber throughput in the affected sector.", "source": "Operator SLA", "tier": "Operational", "value": "≥ 85%", "kind": "constraint" },
        "CON-213": { "code": "CON-213", "title": "Retrofit Filter Status Disclosure", "explanation": "Aircraft altimeter retrofit status must be verified to relax any spectrum constraint.", "source": "FAA SAIB", "tier": "Regulatory", "kind": "constraint" },
        "CONF-301": { "code": "CONF-301", "title": "Capacity vs. Corridor Power Limits", "explanation": "Network Agent requests higher power for congestion relief; Airspace Safety Agent requires power hold.", "source": "Agent arbitration", "tier": "Derived", "kind": "conflict" },
        "CONF-302": { "code": "CONF-302", "title": "Spectrum Expansion vs. Activation Freeze", "explanation": "Spectrum Agent proposes 4100 MHz carrier which collides with activation freeze near runway.", "source": "Agent arbitration", "tier": "Derived", "kind": "conflict" },
        "GAP-401": { "code": "GAP-401", "title": "Unverified Altimeter Retrofit Fleet Share", "explanation": "Share of arriving aircraft with retrofitted filters is unverified; precautionary assumption applied.", "source": "Knowledge base gap", "tier": "Derived", "kind": "gap" },
        "GAP-402": { "code": "GAP-402", "title": "Missing Antenna Down-tilt Log", "explanation": "Latest site survey for BS-17 down-tilt is older than 180 days.", "source": "Site registry", "tier": "Operational", "kind": "gap" },
    }
    entries.update(aliases)

    return {
        "entries": entries,
        **entries,
        "claims": claims_dict,
        "constraints": cons_dict,
        "conflicts": conf_dict,
        "gaps": gaps_dict,
        "actions": actions_dict,
    }


@app.get("/api/graph")
async def get_agent_graph():
    """Returns nodes and edges representing the multi-agent pipeline and knowledge graph."""
    nodes = [
        {"id": "scenario", "label": "Flight & 5G Telemetry", "type": "input", "group": "input"},
        {"id": "kb", "label": "Regulatory Knowledge Base", "type": "knowledge", "group": "kb"},
        {"id": "network", "label": "Network Agent", "type": "agent", "role": "QoS & PRB Load", "group": "agent"},
        {"id": "airspace_safety", "label": "Airspace Safety Agent", "type": "agent", "role": "Glide Path & ITM Margin", "group": "agent"},
        {"id": "spectrum", "label": "Spectrum Agent", "type": "agent", "role": "4.2-4.4 GHz Exclusivity", "group": "agent"},
        {"id": "policy_institutional", "label": "Policy Institutional Agent", "type": "agent", "role": "DGCA In-Force Rules", "group": "agent"},
        {"id": "optimization", "label": "Optimization Agent", "type": "agent", "role": "Pareto Trade-offs", "group": "agent"},
        {"id": "constraint_checker", "label": "Deterministic Constraint Engine", "type": "engine", "role": "Code Decides (No LLM)", "group": "deterministic"},
        {"id": "margin_simulator", "label": "Margin Simulator (PFD)", "type": "engine", "role": "±0.1 dB CLM-109 Math", "group": "deterministic"},
        {"id": "arbitration", "label": "Arbitration Agent", "type": "agent", "role": "Final Safety Ledger", "group": "arbitration"},
    ]

    edges = [
        {"from": "scenario", "to": "network", "label": "PRB 94%, Throughput -38%"},
        {"from": "scenario", "to": "airspace_safety", "label": "CAT II, 450 ft AGL, 900m dist"},
        {"from": "scenario", "to": "spectrum", "label": "n78 (3300-3670 MHz)"},
        {"from": "scenario", "to": "policy_institutional", "label": "India / AIC 19/2025 as-of 2026"},
        {"from": "kb", "to": "network", "label": "3GPP TS 23.501"},
        {"from": "kb", "to": "airspace_safety", "label": "CLM-106 (6dB), CLM-109"},
        {"from": "kb", "to": "spectrum", "label": "RR 5.438, CLM-140"},
        {"from": "kb", "to": "policy_institutional", "label": "CLM-131, GAP-006"},
        {"from": "airspace_safety", "to": "margin_simulator", "label": "Compute PFD"},
        {"from": "network", "to": "optimization", "label": "Proposed ACT-1"},
        {"from": "airspace_safety", "to": "optimization", "label": "Proposed ACT-3"},
        {"from": "spectrum", "to": "optimization", "label": "Proposed ACT-4"},
        {"from": "optimization", "to": "arbitration", "label": "Ranked Actions (ACT-2 preferred)"},
        {"from": "arbitration", "to": "constraint_checker", "label": "Verify All Hard Rules"},
        {"from": "constraint_checker", "to": "arbitration", "label": "Deterministic Verdicts"},
    ]

    return {"nodes": nodes, "edges": edges}


@app.post("/api/run", response_model=RunResult)
async def execute_run(req: RunRequest):
    """Execute coexistence arbitration synchronously.

    Uses LangGraph engine (default) or legacy orchestrator (USE_LANGGRAPH=0).
    """
    seed_file = KB_DIR / "scenario_seed.json"
    seed = json.loads(seed_file.read_text(encoding="utf-8")) if seed_file.exists() else {}

    raw_state = req.scenario.get("simulation_state", seed.get("simulation_state", {})) if req.scenario else seed.get("simulation_state", {})
    state = SimulationState(**raw_state)

    raw_actions = req.scenario.get("candidate_actions", seed.get("candidate_actions", [])) if req.scenario else seed.get("candidate_actions", [])
    candidate_actions = [CandidateAction(**a) for a in raw_actions]

    if USE_LANGGRAPH:
        result = await graph_runner.run_pipeline(
            state=state,
            candidate_actions=candidate_actions,
            as_of=req.as_of,
            scenario_id=(req.scenario or {}).get("scenario_id"),
        )
    else:
        result = await orchestrator.run_pipeline(
            state=state,
            candidate_actions=candidate_actions,
            as_of=req.as_of,
            scenario_id=(req.scenario or {}).get("scenario_id"),
        )
    return result


@app.get("/api/run/{run_id}/stream")
async def stream_run(run_id: str, scenario_id: Optional[str] = None, as_of: str = "2026-10-07", delay: float = 1.5):
    """Server-Sent Events endpoint streaming agent reports and arbitration in real time.

    Uses LangGraph engine (default) or legacy orchestrator (USE_LANGGRAPH=0).
    """
    scenario_data = {}
    
    if scenario_id:
        scenarios_file = KB_DIR / "scenarios.json"
        if scenarios_file.exists():
            scenarios = json.loads(scenarios_file.read_text(encoding="utf-8"))
            for s in scenarios:
                if s.get("scenario_id") == scenario_id:
                    scenario_data = s
                    break

    if not scenario_data:
        seed_file = KB_DIR / "scenario_seed.json"
        scenario_data = json.loads(seed_file.read_text(encoding="utf-8")) if seed_file.exists() else {}

    state = SimulationState(**scenario_data.get("simulation_state", {}))
    candidate_actions = [CandidateAction(**a) for a in scenario_data.get("candidate_actions", [])]

    if USE_LANGGRAPH:
        generator = graph_runner.stream_pipeline(
            state=state,
            candidate_actions=candidate_actions,
            as_of=as_of,
            run_id=run_id,
            scenario_id=scenario_id or scenario_data.get("scenario_id"),
            delay=delay,
        )
    else:
        generator = orchestrator.stream_pipeline(
            state=state,
            candidate_actions=candidate_actions,
            as_of=as_of,
            run_id=run_id,
            scenario_id=scenario_id or scenario_data.get("scenario_id"),
        )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/runs/{run_id}")
async def get_run_audit(run_id: str):
    log_file = RUNS_DIR / f"{run_id}.json"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Run audit log not found")
    return json.loads(log_file.read_text(encoding="utf-8"))


# Static files & UI
static_dir = ROOT_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root_index():
    index_file = ROOT_DIR / "static" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "SkySync API is running. UI not found in static/index.html"}
