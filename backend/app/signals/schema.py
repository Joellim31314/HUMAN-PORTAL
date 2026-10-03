"""Human-signal schema: the contract every ingestion adapter normalizes into.

Aligned with PROJECT.md ingestion policy: English-only (v1), postcode +
local-authority geography where derivable, provenance (author handle + URL)
kept as-is, source_family set for the >=2-source-families trend verification
rule.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

SourceFamily = Literal["social", "search", "reviews", "official", "first_party"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SignalRegion(BaseModel):
    """UK geography per PROJECT.md: postcode + local authority."""

    postcode: str | None = None
    local_authority: str | None = None
    lat: float | None = None
    lon: float | None = None


class HumanSignal(BaseModel):
    """One real person's taste, distrust, craving, habit, or rejection."""

    id: str  # "{source}:{source_id}" — stable across re-ingestion
    source: str  # adapter name: "reddit", "google_trends", "ocado", ...
    source_family: SourceFamily
    kind: str  # "post" | "comment" | "review" | "trend_point" | "event" | ...
    source_id: str  # id within the source (enables purge + idempotent upsert)
    author_handle: str  # stored as-is (PROJECT.md provenance decision)
    text: str
    language: str = "en"
    sentiment: float | None = None  # -1..1, filled downstream, not at ingest
    topics: list[str] = Field(default_factory=list)  # F&B category tags
    engagement: dict[str, int] = Field(default_factory=dict)  # score, likes, ...
    region: SignalRegion | None = None
    observed_at: datetime  # when the person said it
    fetched_at: datetime = Field(default_factory=_utcnow)
    url: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class RawPayload(BaseModel):
    """Original adapter response. Kept (JSONB on Postgres) so normalized
    signals can be reprocessed without re-scraping."""

    source: str
    payload: dict[str, Any]
    fetched_at: datetime = Field(default_factory=_utcnow)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
