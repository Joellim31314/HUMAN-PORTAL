"""Stack Exchange ingestion: cooking.stackexchange.com + coffee.stackexchange.com.

Open API, no key required for demo volume (300 req/day/keyless — we use ~2
per query). Real humans asking and answering food & beverage questions — a
genuine human-signal source that, unlike Reddit, is not blocked from
datacenter IPs. Same adapter contract as everything else.
"""

from __future__ import annotations

import html as html_lib
import logging
import re
from datetime import datetime, timezone
from typing import Iterable

import httpx

from app.signals.adapter import SignalAdapter
from app.signals.schema import HumanSignal, RawPayload

logger = logging.getLogger(__name__)

_API = "https://api.stackexchange.com/2.3"
SITES = ("cooking", "coffee")
_TAGS = re.compile(r"<[^>]+>")
_LINK = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
_MD_CHARS = re.compile(r"[`*_>#~]")
_WS = re.compile(r"\s+")


def _plain(body_html: str, limit: int = 700) -> str:
    text = _TAGS.sub(" ", body_html or "")
    text = _LINK.sub(" ", text)
    text = _MD_CHARS.sub(" ", text)
    text = html_lib.unescape(text)
    text = _WS.sub(" ", text).strip()
    return text[:limit]


class StackExchangeAdapter(SignalAdapter):
    source = "stackexchange"

    def __init__(
        self,
        query: str,
        *,
        limit: int = 15,
        sites: tuple[str, ...] = SITES,
    ):
        self.query = query
        self.limit = min(limit, 50)
        self.sites = sites

    def fetch(self) -> Iterable[RawPayload]:
        raws: list[RawPayload] = []
        for site in self.sites:
            try:
                resp = httpx.get(
                    f"{_API}/search/advanced",
                    params={
                        "order": "desc",
                        "sort": "relevance",
                        "q": self.query,
                        "site": site,
                        "filter": "withbody",
                        "pagesize": self.limit,
                    },
                    timeout=20,
                )
                if resp.status_code != 200:
                    logger.warning("StackExchange %s: HTTP %s", site, resp.status_code)
                    continue
                raws.append(
                    RawPayload(
                        source=self.source,
                        payload={
                            "query": self.query,
                            "site": site,
                            "response": resp.json(),
                        },
                    )
                )
            except Exception as exc:
                logger.warning("StackExchange %s failed: %s", site, exc)
        return raws

    def normalize(self, raw: RawPayload) -> list[HumanSignal]:
        data = raw.payload
        items = (data.get("response") or {}).get("items") or []
        site = data.get("site", "cooking")
        signals: list[HumanSignal] = []
        for item in items:
            title = (item.get("title") or "").strip()
            body = _plain(item.get("body") or "")
            text = f"{title}. {body}".strip(". ")
            if len(text) < 20:
                continue
            owner = item.get("owner") or {}
            created = (item.get("creation_date") or 0) or datetime.now(
                timezone.utc
            ).timestamp()
            signals.append(
                HumanSignal(
                    id=f"stackexchange:{site}-{item.get('question_id')}",
                    source=self.source,
                    source_family="social",
                    kind="question",
                    source_id=str(item.get("question_id")),
                    author_handle=owner.get("display_name") or "anonymous",
                    text=text[:1200],
                    engagement={
                        "score": item.get("score") or 0,
                        "num_answers": item.get("answer_count") or 0,
                        "views": item.get("view_count") or 0,
                    },
                    observed_at=datetime.fromtimestamp(created, tz=timezone.utc),
                    url=item.get("link"),
                    extra={
                        "site": site,
                        "tags": item.get("tags") or [],
                        "title": title,
                        "is_answered": item.get("is_answered", False),
                    },
                )
            )
        return signals
