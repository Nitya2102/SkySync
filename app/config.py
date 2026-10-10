"""Application configuration from environment variables."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
KB_DIR = ROOT_DIR / "kb"
RUNS_DIR = ROOT_DIR / "runs"
RUNS_DIR.mkdir(exist_ok=True)

# Groq / Together AI
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY", "")
GROQ_MODEL_REASON: str = os.getenv("GROQ_MODEL_REASON", "openai/gpt-oss-120b")
GROQ_MODEL_FAST: str = os.getenv("GROQ_MODEL_FAST", "openai/gpt-oss-20b")
GROQ_CONCURRENCY: int = int(os.getenv("GROQ_CONCURRENCY", "4"))

# Google Gemini (primary LLM provider when available)
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Embeddings
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

# Mock mode – tests and UI work without a real key
MOCK_LLM: bool = False  # Switched to False to use Live Together API

# Agent execution mode:
# - "hybrid" (default): Fast Knowledge-Base & Physics heuristics for domain agents + LLM for final arbitration
# - "fast_kb": Pure high-speed Knowledge-Base heuristics for all agents (~0.2s total)
# - "llm_all": Full external LLM generation for every single agent
AGENT_MODE: str = os.getenv("AGENT_MODE", "hybrid").lower()

# LangGraph engine toggle (set USE_LANGGRAPH=0 to fall back to legacy orchestrator)
USE_LANGGRAPH: bool = os.getenv("USE_LANGGRAPH", "1").lower() in ("1", "true", "yes")

# LangSmith tracing (optional — set LANGSMITH_API_KEY to enable)
LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "skysync-5g-airspace")

# Defaults
DEFAULT_AS_OF: str = "2026-10-07"
DEFAULT_TEMPERATURE: float = 0.1
MAX_TOKENS_AGENT: int = 700
MAX_TOKENS_ARBITRATION: int = 1000
LLM_TIMEOUT: int = 30
