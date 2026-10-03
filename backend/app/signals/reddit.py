"""Reddit ingestion via the public JSON endpoints (no OAuth credentials needed).

Works unauthenticated with a descriptive User-Agent, rate-limited by Reddit
(~10–20 req/min/IP) — plenty for demo-scale queries. If the main host blocks
us (some datacenter IPs get 403), we fall back to old.reddit.com. Swappable
per PROJECT.md: when Reddit breaks, replace this adapter, not the consumers.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Iterable

import httpx

from app import config
from app.signals.adapter import SignalAdapter
from app.signals.schema import HumanSignal, RawPayload

logger = logging.getLogger(__name__)

_HOSTS = ("https://www.reddit.com", "https://old.reddit.com")


class RedditAdapter(SignalAdapter):
    source = "reddit"

    def __init__(
        self,
        query: str,
        area: str | None = None,
        *,
        limit: int = 25,
        time_filter: str = "year",
        subreddit: str | None = None,
    ):
        self.query = query
        self.area = area
        self.limit = min(limit, 100)
        self.time_filter = time_filter
        self.subreddit = subreddit

    def _search_url(self, host: str) -> tuple[str, dict]:
        if self.subreddit:
            return f"{host}/r/{self.subreddit}/search.json", {
                "q": self.query,
                "restrict_sr": "true",
            }
        q = f"{self.query} {self.area}" if self.area else self.query
        return f"{host}/search.json", {"q": q}

    def fetch(self) -> Iterable[RawPayload]:
        params = {"limit": self.limit, "sort": "relevance", "t": self.time_filter}
        headers = {"User-Agent": config.REDDIT_USER_AGENT}
        last_error: str | None = None
        for host in _HOSTS:
            try:
                url, extra = self._search_url(host)
                resp = httpx.get(
                    url,
                    params={**params, **extra},
                    headers=headers,
                    timeout=20,
                    follow_redirects=True,
                )
                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code} from {host}"
                    logger.warning("Reddit %s: %s", host, last_error)
                    continue
                return [
                    RawPayload(
                        source=self.source,
                        payload={
                            "query": extra.get("q", self.query),
                            "area": self.area,
                            "response": resp.json(),
                        },
                    )
                ]
            except Exception as exc:  # network/TLS/timeout — try next host
                last_error = f"{type(exc).__name__}: {exc}"
                logger.warning("Reddit %s failed: %s", host, last_error)
        return [
            RawPayload(
                source=self.source,
                payload={
                    "query": self.query,
                    "area": self.area,
                    "error": last_error or "unreachable",
                },
            )
        ]

    def normalize(self, raw: RawPayload) -> list[HumanSignal]:
        data = raw.payload
        if "error" in data:
            return []
        children = (
            data.get("response", {}).get("data", {}).get("children", []) or []
        )
        signals: list[HumanSignal] = []
        for child in children:
            d = child.get("data") or {}
            if d.get("stickied"):
                continue
            text = (d.get("selftext") or "").strip() or (d.get("title") or "")
            if len(text.strip()) < 12:
                continue
            created = d.get("created_utc") or time.time()
            permalink = d.get("permalink") or ""
            signals.append(
                HumanSignal(
                    id=f"reddit:{d.get('name') or d.get('id')}",
                    source=self.source,
                    source_family="social",
                    kind="comment" if d.get("link_title") else "post",
                    source_id=str(d.get("id")),
                    author_handle=d.get("author") or "[deleted]",
                    text=text[:1200],
                    engagement={
                        "score": d.get("score") or 0,
                        "num_comments": d.get("num_comments") or 0,
                    },
                    observed_at=datetime.fromtimestamp(
                        created, tz=timezone.utc
                    ),
                    url=f"https://www.reddit.com{permalink}" if permalink else None,
                    extra={
                        "subreddit": d.get("subreddit"),
                        "title": d.get("title") or d.get("link_title"),
                        "area_query": data.get("area"),
                    },
                )
            )
        return signals
