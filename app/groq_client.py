"""Groq LLM Client wrapper using official AsyncGroq SDK.

Features:
- Configurable models (GROQ_MODEL_REASON, GROQ_MODEL_FAST)
- client.models.list() discovery at startup with closest-match fallback
- Concurrency limiting via asyncio.Semaphore
- Retry with exponential backoff on 429 / 503
- JSON object response format enforcement
- Mock mode when MOCK_LLM=1 or when GROQ_API_KEY is not set
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Optional

from openai import AsyncOpenAI, APIStatusError, RateLimitError

from app.config import (
    GROQ_API_KEY,
    TOGETHER_API_KEY,
    GROQ_MODEL_REASON,
    GROQ_MODEL_FAST,
    GROQ_CONCURRENCY,
    MOCK_LLM,
    DEFAULT_TEMPERATURE,
    LLM_TIMEOUT,
)

logger = logging.getLogger(__name__)


class GroqClient:
    """Manages AsyncGroq lifecycle, concurrency, retries, and mock fallbacks."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        reason_model: Optional[str] = None,
        fast_model: Optional[str] = None,
        concurrency: int = GROQ_CONCURRENCY,
        mock_mode: Optional[bool] = None,
    ):
        self.api_key = api_key if api_key is not None else (GROQ_API_KEY or TOGETHER_API_KEY)
        self.mock_mode = mock_mode if mock_mode is not None else (MOCK_LLM or not bool(self.api_key))
        self.configured_reason_model = reason_model or GROQ_MODEL_REASON
        self.configured_fast_model = fast_model or GROQ_MODEL_FAST
        self.active_reason_model = self.configured_reason_model
        self.active_fast_model = self.configured_fast_model
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self._client: Optional[AsyncOpenAI] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Call client.models.list() at startup and verify/resolve models."""
        if self._initialized:
            return

        if self.mock_mode:
            logger.info("GroqClient running in MOCK mode (no API calls)")
            self._initialized = True
            return

        try:
            is_groq = self.api_key.startswith("gsk_")
            base_url = "https://api.groq.com/openai/v1" if is_groq else "https://api.together.xyz/v1"
            provider_name = "Groq" if is_groq else "Together AI"
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=base_url)
            models_resp = await self._client.models.list()
            available_ids = [m.id for m in models_resp.data]
            logger.info("%s models available: %s", provider_name, len(available_ids))

            # Resolve reason model
            if self.configured_reason_model in available_ids:
                self.active_reason_model = self.configured_reason_model
            else:
                self.active_reason_model = self._find_closest_model(
                    self.configured_reason_model, available_ids, default="llama-3.3-70b-versatile"
                )
                logger.warning(
                    "Configured reason model '%s' not in available models. Picked closest: '%s'",
                    self.configured_reason_model,
                    self.active_reason_model,
                )

            # Resolve fast model
            if self.configured_fast_model in available_ids:
                self.active_fast_model = self.configured_fast_model
            else:
                self.active_fast_model = self._find_closest_model(
                    self.configured_fast_model, available_ids, default="llama-3.1-8b-instant"
                )
                logger.warning(
                    "Configured fast model '%s' not in available models. Picked closest: '%s'",
                    self.configured_fast_model,
                    self.active_fast_model,
                )
        except Exception as e:
            logger.error("Failed to initialize Groq client / list models: %s. Falling back to mock.", e)
            self.mock_mode = True
        finally:
            self._initialized = True

    def _find_closest_model(self, target: str, available: list[str], default: str) -> str:
        """Pick closest available chat-compatible model ID based on keyword match or fallback."""
        if not available:
            return default

        # Filter out non-chat models (whisper, prompt-guard, safeguard, audio, etc.)
        chat_candidates = [
            m for m in available
            if not any(non_chat in m.lower() for non_chat in ("whisper", "prompt-guard", "safeguard", "orpheus"))
        ]
        if not chat_candidates:
            chat_candidates = available

        target_lower = target.lower()
        # Direct substring match
        for m in chat_candidates:
            if target_lower in m.lower() or m.lower() in target_lower:
                return m
        # Check known reliable chat models:
        for m in chat_candidates:
            if "llama" in m.lower():
                return m
        for m in chat_candidates:
            if "qwen" in m.lower():
                return m
        # Fallback to first chat candidate
        return chat_candidates[0]

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        model_type: str = "reason",  # "reason" or "fast"
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = 1000,
        max_retries: int = 3,
        agent_name: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Generate structured JSON response with retries, backoff, and semaphore."""
        import re

        if not self._initialized:
            await self.initialize()

        if self.mock_mode:
            return self._generate_mock_response(agent_name=agent_name, prompt=prompt, context=context)

        model = self.active_reason_model if model_type == "reason" else self.active_fast_model
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        delay = 1.0
        last_exception = None

        for attempt in range(1, max_retries + 1):
            async with self.semaphore:
                try:
                    assert self._client is not None
                    resp = await asyncio.wait_for(
                        self._client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            response_format={"type": "json_object"},
                        ),
                        timeout=LLM_TIMEOUT,
                    )
                    content = resp.choices[0].message.content or "{}"
                    parsed = json.loads(content)
                    return parsed
                except APIStatusError as e:
                    last_exception = e
                    status_code = getattr(e, "status_code", None)
                    if "json_validate_failed" in str(e) or status_code == 400:
                        logger.warning("Groq json_object mode failed; retrying with plain text JSON extraction...")
                        try:
                            resp = await asyncio.wait_for(
                                self._client.chat.completions.create(
                                    model=model,
                                    messages=messages,
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                ),
                                timeout=LLM_TIMEOUT,
                            )
                            content = resp.choices[0].message.content or "{}"
                            match = re.search(r"\{.*\}", content, re.DOTALL)
                            if match:
                                return json.loads(match.group(0))
                            return json.loads(content)
                        except Exception as inner_e:
                            last_exception = inner_e
                    elif status_code in (429, 503) and attempt < max_retries:
                        logger.warning(
                            "Groq API %s encountered (attempt %d/%d). Retrying in %.1fs...",
                            status_code,
                            attempt,
                            max_retries,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        delay *= 2.0
                    else:
                        logger.error("Groq API error: %s", e)
                        raise
                except RateLimitError as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2.0
                    else:
                        raise
                except json.JSONDecodeError as e:
                    logger.warning("Groq response JSON decode error: %s. Retrying...", e)
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                except asyncio.TimeoutError:
                    logger.warning("Groq request timed out on attempt %d/%d", attempt, max_retries)
                    if attempt == max_retries:
                        raise

                except json.JSONDecodeError as e:
                    logger.warning("Groq response JSON decode error: %s. Retrying...", e)
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                except asyncio.TimeoutError:
                    logger.warning("Groq request timed out on attempt %d/%d", attempt, max_retries)
                    if attempt == max_retries:
                        raise

        if last_exception:
            raise last_exception
        raise RuntimeError("Failed to generate JSON after retries")

    def _generate_mock_response(
        self, agent_name: str, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Deterministic mock responses matching answer_contract in schema.json."""
        ctx = context or {}
        evidence_ids = ctx.get("evidence_ids", [])
        constraints = ctx.get("constraints", [])
        scenario = ctx.get("scenario") or self._extract_scenario(prompt)
        cell = scenario.get("cell", {})
        aircraft = scenario.get("aircraft", {})
        jurisdiction = scenario.get("jurisdiction", "")
        cell_id = cell.get("id", "CELL-UNKNOWN")
        callsign = aircraft.get("callsign", "AIRCRAFT-UNKNOWN")
        phase = aircraft.get("phase", "unknown")
        altitude = aircraft.get("height_agl_ft", 0)
        distance = cell.get("distance_to_runway_threshold_m", 0)
        prb = cell.get("prb_util_pct", 0)
        throughput_drop = cell.get("throughput_drop_pct", 0)

        if agent_name == "network":
            return {
                "agent_name": "network",
                "observation": f"Cell {cell_id} exhibits {prb}% PRB utilization and {throughput_drop}% throughput degradation.",
                "assessment": "High load requires mitigation. Prefer resource or traffic changes that do not increase emissions near the aircraft.",
                "evidence_ids": [eid for eid in evidence_ids if "CLM" in eid][:3] or ["CLM-008", "CLM-009"],
                "constraints": [cid for cid in constraints if "CON" in cid][:2] or ["CON-INT-004"],
                "candidate_actions": [
                    {
                        "id": "ACT-1",
                        "desc": "Raise cell power +3 dB for QoS recovery",
                        "action_type": "power_change",
                        "parameters": {"power_delta_db": 3.0, "new_eirp_dbm_mhz": 65.0},
                    }
                ],
                "confidence": 0.88,
                "uncertainty": "Uncertain if traffic steering to adjacent cell CELL-18 can absorb full load without handover drops.",
                "evidence_status": "sufficient",
                "warnings": [],
                "conflicts_cited": [],
            }

        elif agent_name == "airspace_safety":
            return {
                "agent_name": "airspace_safety",
                "observation": f"Aircraft {callsign} is in {phase} at {altitude} ft AGL. Cell {cell_id} is {distance} m from the runway threshold.",
                "assessment": "Power increases are unsafe near the approach corridor. Use geometry-preserving mitigation and verify the simulated margin.",
                "evidence_ids": [eid for eid in evidence_ids if "CLM" in eid][:4] or ["CLM-106", "CLM-107", "CLM-109"],
                "constraints": [cid for cid in constraints if "CON" in cid] or ["CON-INT-003", "CON-INT-001"],
                "candidate_actions": [
                    {
                        "id": "ACT-3",
                        "desc": "Downtilt 3 deg + cap PRB-based power",
                        "action_type": "downtilt",
                        "parameters": {"downtilt_delta_deg": 3.0, "cap_prb_power": True},
                    }
                ],
                "confidence": 0.92,
                "uncertainty": "Aircraft radar altimeter tolerance category is unknown; applying conservative ITM baseline.",
                "evidence_status": "sufficient",
                "warnings": ["Aircraft RA tolerance is unknown: using precautionary limit"],
                "conflicts_cited": [cid for cid in ctx.get("conflicts", []) if "CONF" in cid] or ["CONF-001"],
            }

        elif agent_name == "spectrum":
            return {
                "agent_name": "spectrum",
                "observation": "Operating in n78 band (3300-3670 MHz licensed in India). Unused carrier proposed at 4100 MHz is outside licensed scope.",
                "assessment": "Carrier at 4100 MHz violates national licensing under CON-INT-004 and abuts protected aeronautical band 4200-4400 MHz (CON-INT-001).",
                "evidence_ids": [eid for eid in evidence_ids if "CLM" in eid][:3] or ["CLM-140", "CLM-130"],
                "constraints": [cid for cid in constraints if "CON" in cid] or ["CON-INT-001", "CON-INT-004"],
                "candidate_actions": [
                    {
                        "id": "ACT-4",
                        "desc": "Activate unused carrier at 4100 MHz (n77)",
                        "action_type": "carrier_change",
                        "parameters": {"carrier_mhz": 4100.0},
                    }
                ],
                "confidence": 0.95,
                "uncertainty": "Exact out-of-band emission filter attenuation curve for specific gNodeB model is unverified.",
                "evidence_status": "sufficient",
                "warnings": ["4100 MHz operation violates both national license and proximity boundary"],
                "conflicts_cited": [],
            }

        elif agent_name == "policy_institutional":
            return {
                "agent_name": "policy_institutional",
                "observation": f"Scenario jurisdiction is {jurisdiction}.",
                "assessment": "Applicable rules and authorization status must be checked against the scenario date; missing primary parameters require precautionary handling.",
                "evidence_ids": [eid for eid in evidence_ids if "CLM" in eid][:3] or ["CLM-131"],
                "constraints": [cid for cid in constraints if "CON" in cid] or ["CON-IN-002", "CON-IN-003", "CON-IN-004"],
                "candidate_actions": [],
                "confidence": 0.85,
                "uncertainty": "GAP-006: Lack of published numeric exclusion radius around synthetic airport runways in primary circulars.",
                "evidence_status": "sufficient",
                "warnings": ["DGCA AIC 19/2025 is NOT_YET_IN_FORCE as of 2026-10-07"],
                "conflicts_cited": [],
            }

        elif agent_name == "optimization":
            if phase == "cat_iii_autoland" and aircraft.get("ra_tolerant") in ("non_tolerant", "unknown"):
                action = {
                    "id": "ACT-5",
                    "desc": "Freeze dynamic emission changes & escalate to human ATC / Network Coordinator",
                    "action_type": "human_escalation",
                    "parameters": {"requires_human_approval": True},
                }
                assessment = "Severe CAT III safety uncertainty requires emission freeze and human coordination."
            elif phase == "landing_flare" and distance <= 500:
                action = {
                    "id": "ACT-3",
                    "desc": "Apply 4° mechanical antenna downtilt + 20% PRB power cap",
                    "action_type": "downtilt",
                    "parameters": {"downtilt_delta_deg": 4.0, "cap_prb_power": True},
                }
                assessment = "Close low-altitude geometry requires beam shaping and power capping."
            else:
                action = {
                    "id": "ACT-2",
                    "desc": "Steer traffic to neighbouring cell >1200 m from threshold",
                    "action_type": "traffic_steering",
                    "parameters": {"target_cell_id": "CELL-18", "min_distance_m": 1200.0},
                }
                assessment = "Off-corridor traffic steering improves QoS without increasing emissions near the approach corridor."
            return {
                "agent_name": "optimization",
                "observation": "Multi-objective tradeoff between PRB utilization recovery, QoS SLA, and safety margin preservation.",
                "assessment": assessment,
                "evidence_ids": [eid for eid in evidence_ids if "CLM" in eid][:3] or ["CLM-151", "CLM-005"],
                "constraints": [cid for cid in constraints if "CON" in cid] or ["CON-INT-003"],
                "candidate_actions": [action],
                "confidence": 0.90,
                "uncertainty": "Potential handover signaling overhead during peak load burst.",
                "evidence_status": "sufficient",
                "warnings": ["ECC 362 separation distance (CLM-151) applied as supporting analogy only"],
                "conflicts_cited": [],
            }

        elif agent_name == "arbitration":
            accepted = self._extract_json_after_marker(prompt, "Accepted Action:")
            accepted_id = accepted.get("id", "NONE") if accepted else "NONE"
            accepted_verdict = accepted.get("verdict", "ACCEPT") if accepted else "ESCALATE"
            return {
                "accepted_action": accepted or None,
                "rejected_actions": [],
                "rejection_reasons": {},
                "safety_status": "PROTECTED",
                "spectrum_status": "COMPLIANT",
                "authorization_status": "VERIFIED",
                "performance_status": "OPTIMIZED_WITH_TRAFFIC_STEERING",
                "evidence_ids": [eid for eid in evidence_ids if "CLM" in eid][:5] or [
                    "CLM-106",
                    "CLM-109",
                    "CLM-140",
                    "CLM-151",
                ],
                "warnings": [
                    "DGCA AIC 19/2025 is NOT_YET_IN_FORCE as of 2026-10-07",
                    "ECC 362 distance threshold used as supporting analogy only",
                ],
                "conflicts_cited": [cid for cid in ctx.get("conflicts", []) if "CONF" in cid] or ["CONF-001"],
                "requires_human_approval": accepted_id != "NONE" and accepted_verdict == "ESCALATE",
                "rationale": f"{accepted_id} selected by deterministic constraint arbitration; the LLM provides explanatory synthesis only.",
            }

        # Fallback empty structure
        return {
            "agent_name": agent_name or "unknown",
            "observation": "Default observation",
            "assessment": "Default assessment",
            "evidence_ids": evidence_ids[:2],
            "constraints": constraints[:2],
            "candidate_actions": [],
            "confidence": 0.5,
            "uncertainty": "None",
            "evidence_status": "sufficient",
            "warnings": [],
            "conflicts_cited": [],
        }

    @staticmethod
    def _extract_scenario(prompt: str) -> dict[str, Any]:
        return GroqClient._extract_json_after_marker(prompt, "Scenario:")

    @staticmethod
    def _extract_json_after_marker(text: str, marker: str) -> dict[str, Any]:
        start = text.find(marker)
        if start < 0:
            return {}
        decoder = json.JSONDecoder()
        try:
            value, _ = decoder.raw_decode(text[start + len(marker):].lstrip())
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            return {}


# Global singleton instance
groq_client = GroqClient()
