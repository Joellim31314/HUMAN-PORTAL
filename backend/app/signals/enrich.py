"""Sentiment/topic enrichment for HumanSignals — DeepSeek first, heuristic fallback.

The ingest schema keeps sentiment out of adapters ("filled downstream, not at
ingest"); this is the downstream. One batched JSON completion classifies up
to 20 texts per call; anything the LLM can't do falls back to a tiny keyword
scorer so the demo never dies on a missing key or timeout.
"""

from __future__ import annotations

import logging

from app.llm.client import chat_json, llm_available
from app.signals.schema import HumanSignal

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You classify food & beverage consumer signals for a market-research tool. "
    'Return a JSON object of the form {"results": [{"i": 0, "sentiment": <number -1 to 1>, '
    '"topics": [<short kebab-case tags like "matcha-switching", "caffeine-anxiety", '
    '"price-sensitivity">]}]} — one entry per text, in order. Sentiment: positive > 0, '
    "negative < 0, mixed near 0. At most 3 topics each."
)

_POS = (
    "love", "loved", "amazing", "delicious", "obsessed", "best", "perfect",
    "great", "good", "fantastic", "recommend", "favourite", "favorite",
    "yum", "tasty", "better", "helped", "calm", "enjoy",
)
_NEG = (
    "hate", "hated", "awful", "terrible", "worst", "bad", "gross",
    "disappointed", "disappointing", "never again", "waste", "horrible",
    "sick", "jitters", "overpriced", "expensive", "reject",
)


def _heuristic(text: str) -> tuple[float, list[str]]:
    low = text.lower()
    score = 0
    for w in _POS:
        if w in low:
            score += 1
    for w in _NEG:
        if w in low:
            score -= 1
    sentiment = max(-1.0, min(1.0, score / 3))
    return sentiment, []


async def _llm_batch(texts: list[str]) -> list[tuple[float, list[str]]] | None:
    payload = {"texts": texts}
    result = await chat_json(_SYSTEM, str(payload), temperature=0.2, max_tokens=1200)
    if not result or not isinstance(result.get("results"), list):
        return None
    out: list[tuple[float, list[str]]] = []
    try:
        for entry in result["results"]:
            i = int(entry["i"])
            sentiment = max(-1.0, min(1.0, float(entry.get("sentiment", 0))))
            topics = [str(t) for t in (entry.get("topics") or [])][:3]
            while len(out) < i:
                out.append((0.0, []))
            out.append((sentiment, topics))
    except (TypeError, ValueError, IndexError):
        return None
    return out if len(out) == len(texts) else None


async def enrich_signals(signals: list[HumanSignal]) -> list[HumanSignal]:
    if not signals:
        return signals
    texts = [s.text for s in signals]
    classified: list[tuple[float, list[str]]] | None = None
    if llm_available():
        # One batch is enough at demo scale; chunk for safety above 20.
        chunks = [texts[i : i + 20] for i in range(0, len(texts), 20)]
        merged: list[tuple[float, list[str]]] = []
        for chunk in chunks:
            part = await _llm_batch(chunk)
            if part is None:
                merged = []
                break
            merged.extend(part)
        if merged and len(merged) == len(texts):
            classified = merged
        else:
            logger.warning("LLM enrichment incomplete; heuristic fallback")
    return [
        s.model_copy(
            update={
                "sentiment": classified[i][0] if classified else _heuristic(s.text)[0],
                "topics": classified[i][1] if classified else [],
            }
        )
        for i, s in enumerate(signals)
    ]
