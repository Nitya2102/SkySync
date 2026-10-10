"""Multi-provider LLM router with Gemini primary and Together AI fallback.

Routes LLM calls through available providers with automatic failover:
  1. Google Gemini (primary — best reasoning for safety-critical decisions)
  2. Together AI (secondary — your existing Llama provider)
  3. Mock mode (ultimate fallback — deterministic responses for testing)

This module is used by BaseAgent when GOOGLE_API_KEY is configured.
The existing GroqClient continues to work as-is for backward compatibility.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LLMProvider:
    """Multi-provider LLM with automatic failover."""

    def __init__(self):
        self._providers: dict[str, Any] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Discover and initialize available LLM providers."""
        if self._initialized:
            return

        # 1. Google Gemini
        google_key = os.getenv("GOOGLE_API_KEY", "")
        if google_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                self._providers["gemini"] = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=0.1,
                    google_api_key=google_key,
                )
                logger.info("LLMProvider: Google Gemini (%s) initialized.", model_name)
            except Exception as e:
                logger.warning("LLMProvider: Failed to initialize Gemini: %s", e)

        # 2. Together AI (via OpenAI-compatible endpoint)
        together_key = os.getenv("TOGETHER_API_KEY", "")
        if together_key:
            try:
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError:
                    from langchain_community.chat_models.openai import ChatOpenAI

                model_name = os.getenv(
                    "GROQ_MODEL_REASON",
                    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                )
                self._providers["together"] = ChatOpenAI(
                    base_url="https://api.together.xyz/v1",
                    api_key=together_key,
                    model=model_name,
                    temperature=0.1,
                    max_tokens=1000,
                )
                logger.info("LLMProvider: Together AI (%s) initialized.", model_name)
            except Exception as e:
                logger.warning("LLMProvider: Failed to initialize Together AI: %s", e)

        # 3. Groq (via OpenAI-compatible endpoint)
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            try:
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError:
                    from langchain_community.chat_models.openai import ChatOpenAI

                model_name = os.getenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
                self._providers["groq"] = ChatOpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=groq_key,
                    model=model_name,
                    temperature=0.1,
                    max_tokens=1000,
                )
                logger.info("LLMProvider: Groq (%s) initialized.", model_name)
            except Exception as e:
                logger.warning("LLMProvider: Failed to initialize Groq: %s", e)

        if not self._providers:
            logger.warning("LLMProvider: No API keys found. Running in mock mode only.")

        self._initialized = True

    @property
    def is_available(self) -> bool:
        return bool(self._providers)

    @property
    def active_provider(self) -> str:
        """Return the name of the primary active provider."""
        if "gemini" in self._providers:
            return "gemini"
        if "together" in self._providers:
            return "together"
        if "groq" in self._providers:
            return "groq"
        return "mock"

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        agent_name: str = "",
        max_retries: int = 2,
    ) -> dict[str, Any]:
        """Generate a JSON response with automatic provider failover.

        Tries each provider in priority order. Falls back to mock on total failure.
        """
        if not self._initialized:
            await self.initialize()

        from langchain_core.messages import HumanMessage, SystemMessage

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        last_error = None
        for provider_name, llm in self._providers.items():
            for attempt in range(1, max_retries + 1):
                try:
                    response = await llm.ainvoke(messages)
                    content = response.content if hasattr(response, "content") else str(response)

                    # Parse JSON from response
                    parsed = self._extract_json(content)
                    if parsed:
                        logger.info(
                            "LLMProvider: %s succeeded for %s (attempt %d)",
                            provider_name, agent_name, attempt,
                        )
                        return parsed

                    logger.warning(
                        "LLMProvider: %s returned non-JSON for %s. Raw: %s",
                        provider_name, agent_name, content[:200],
                    )
                except Exception as e:
                    last_error = e
                    logger.warning(
                        "LLMProvider: %s failed for %s (attempt %d/%d): %s",
                        provider_name, agent_name, attempt, max_retries, e,
                    )

        # Ultimate fallback
        logger.error("LLMProvider: All providers failed for %s. Last error: %s", agent_name, last_error)
        raise RuntimeError(f"All LLM providers failed for {agent_name}: {last_error}")

    @staticmethod
    def _extract_json(text: str) -> Optional[dict[str, Any]]:
        """Extract JSON object from LLM response text."""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code blocks
        code_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if code_block:
            try:
                return json.loads(code_block.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding the first { ... } block
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return None


# Global singleton
llm_provider = LLMProvider()
