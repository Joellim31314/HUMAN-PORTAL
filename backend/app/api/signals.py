"""Live human-signal search: pull from Reddit + Stack Exchange, enrich via
DeepSeek, return JSON. No database required — fetch -> normalize -> enrich ->
respond, so it works before `docker compose up -d db` and during the demo.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.llm.client import llm_available
from app.signals.adapter import SignalAdapter
from app.signals.enrich import enrich_signals
from app.signals.reddit import RedditAdapter
from app.signals.stackexchange import StackExchangeAdapter
from app.signals.schema import HumanSignal

router = APIRouter(prefix="/api/signals", tags=["signals"])


def _collect(adapter: SignalAdapter) -> tuple[list[HumanSignal], bool]:
    """Run one adapter; return (signals, live?) where live = source responded."""
    raws = list(adapter.fetch())
    signals = [s for raw in raws for s in adapter.normalize(raw)]
    blocked = any("error" in raw.payload for raw in raws) and not signals
    return signals, not blocked


def _sentiment_label(value: float | None) -> str:
    if value is None:
        return "mixed"
    if value >= 0.15:
        return "positive"
    if value <= -0.15:
        return "negative"
    return "mixed"


def _confidence(value: float | None) -> str:
    if value is None:
        return "low"
    magnitude = abs(value)
    if magnitude >= 0.5:
        return "high"
    if magnitude >= 0.25:
        return "medium"
    return "low"


def _to_json(s: HumanSignal) -> dict:
    site = s.extra.get("site")
    return {
        "id": s.id,
        "platform": f"StackExchange:{site}" if s.source == "stackexchange" else s.source.capitalize(),
        "source": s.source,
        "kind": s.kind,
        "topic": (s.topics[0].replace("-", " ") if s.topics else s.extra.get("title", "")),
        "topics": s.topics,
        "quote": s.text,
        "author": s.author_handle,
        "authorMeta": f"r/{s.extra.get('subreddit', '?')}" if s.source == "reddit" else f"{site}.stackexchange",
        "observedAt": s.observed_at.isoformat(),
        "sentiment": _sentiment_label(s.sentiment),
        "sentimentScore": s.sentiment,
        "confidence": _confidence(s.sentiment),
        "engagement": s.engagement,
        "url": s.url,
    }


@router.get("/search")
async def search_signals(
    query: str = Query(min_length=2),
    area: str | None = None,
    limit: int = Query(default=25, ge=1, le=50),
):
    adapters: list[tuple[str, SignalAdapter]] = [
        ("reddit", RedditAdapter(query=query, area=area, limit=limit)),
        ("stackexchange", StackExchangeAdapter(query=query, limit=max(5, limit // 2))),
    ]
    all_signals: list[HumanSignal] = []
    sources: dict[str, str] = {}
    for name, adapter in adapters:
        signals, live = _collect(adapter)
        sources[name] = "ok" if live else "blocked"
        all_signals.extend(signals)

    deduped = list({s.id: s for s in all_signals}.values())
    deduped.sort(key=lambda s: -(s.engagement.get("score") or 0))
    enriched = await enrich_signals(deduped)
    return {
        "query": query,
        "area": area,
        "live": any(v == "ok" for v in sources.values()),
        "sources": sources,
        "llm": llm_available(),
        "count": len(enriched),
        "signals": [_to_json(s) for s in enriched],
    }


@router.get("/health")
async def signals_health():
    _, reddit_ok = _collect(RedditAdapter(query="tea", limit=1))
    _, se_ok = _collect(StackExchangeAdapter(query="tea", limit=1))
    return {
        "reddit": "ok" if reddit_ok else "blocked",
        "stackexchange": "ok" if se_ok else "blocked",
        "llm": llm_available(),
    }
