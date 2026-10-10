"""Live smoke test executing against Groq API if GROQ_API_KEY is available."""
import os
import pytest
from app.groq_client import GroqClient
from app.config import GROQ_API_KEY


@pytest.mark.skipif(not bool(GROQ_API_KEY), reason="GROQ_API_KEY not configured in environment")
def test_live_groq_models_and_completion():
    import asyncio

    async def _run():
        client = GroqClient(api_key=GROQ_API_KEY, mock_mode=False)
        await client.initialize()
        assert client.active_reason_model != ""
        assert client.active_fast_model != ""

        resp = await client.generate_json(
            prompt="Return a JSON object with key 'status' set to 'ok' and key 'message' saying hello.",
            model_type="fast",
            max_tokens=150,
        )
        assert isinstance(resp, dict)
        assert resp.get("status") == "ok" or len(resp) > 0

    asyncio.run(_run())
