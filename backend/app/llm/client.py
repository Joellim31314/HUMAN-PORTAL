"""Bounded, best-effort JSON completions through DeepSeek."""
import asyncio
import json
import logging

from openai import AsyncOpenAI

from app import config

logger = logging.getLogger(__name__)
_semaphore = asyncio.Semaphore(max(1, config.LLM_CONCURRENCY))


def llm_available() -> bool:
    return bool(config.DEEPSEEK_API_KEY.strip())


async def chat_json(system: str, user: str, temperature: float = 0.8,
                    max_tokens: int = 600) -> dict | None:
    if not llm_available():
        return None
    try:
        # Timeout starts once we hold a slot, so queued interviews don't expire waiting.
        async with _semaphore:
            async with asyncio.timeout(config.LLM_TIMEOUT_S):
                async with AsyncOpenAI(api_key=config.DEEPSEEK_API_KEY,
                                       base_url=config.DEEPSEEK_BASE_URL,
                                       max_retries=0) as client:
                    for attempt in range(2):
                        response = await client.chat.completions.create(
                            model=config.DEEPSEEK_MODEL,
                            messages=[{"role": "system", "content": system},
                                      {"role": "user", "content": user}],
                            temperature=temperature, max_tokens=max_tokens,
                            response_format={"type": "json_object"},
                        )
                        try:
                            value = json.loads(response.choices[0].message.content or "")
                            if isinstance(value, dict):
                                return value
                        except (ValueError, IndexError, TypeError):
                            pass
                        if attempt == 0:
                            user += "\nReturn a valid JSON object only."
    except Exception:
        logger.warning("LLM completion unavailable; using template", exc_info=True)
    return None
