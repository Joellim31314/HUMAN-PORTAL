"""Postgres persistence for human signals and raw payloads.

Production: Postgres via `docker compose up -d db` (payload columns are
JSONB). Tests: any SQLAlchemy URL, e.g. SQLite in-memory. Simulation results
stay in the JSON file cache (app/store.py) for now.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache

from sqlalchemy import JSON, Column, DateTime, Float, String, Table, Text, create_engine, delete, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app import config
from app.signals.schema import HumanSignal, RawPayload

# JSONB on Postgres, plain JSON elsewhere (SQLite tests).
JsonColumn = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


raw_payloads = Table(
    "raw_payloads",
    Base.metadata,
    Column("id", String, primary_key=True),
    Column("source", String, index=True),
    Column("payload", JsonColumn),
    Column("fetched_at", DateTime(timezone=True)),
)

human_signals = Table(
    "human_signals",
    Base.metadata,
    Column("id", String, primary_key=True),  # "{source}:{source_id}"
    Column("source", String, index=True),
    Column("source_family", String),
    Column("kind", String),
    Column("source_id", String),
    Column("author_handle", String),
    Column("text", Text),
    Column("language", String, default="en"),
    Column("sentiment", Float, nullable=True),
    Column("topics", JsonColumn),
    Column("engagement", JsonColumn),
    Column("region", JsonColumn),
    Column("observed_at", DateTime(timezone=True), index=True),
    Column("fetched_at", DateTime(timezone=True)),
    Column("url", String, nullable=True),
    Column("extra", JsonColumn),
)


@lru_cache(maxsize=1)
def get_engine():
    return create_engine(config.DATABASE_URL)


@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(get_engine())


@contextmanager
def session():
    s: Session = get_session_factory()()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def save_raw(raw: RawPayload) -> None:
    with session() as s:
        s.execute(
            raw_payloads.insert().values(
                id=raw.id, source=raw.source, payload=raw.payload, fetched_at=raw.fetched_at
            )
        )


def _signal_row(signal: HumanSignal) -> dict:
    return {
        "id": signal.id,
        "source": signal.source,
        "source_family": signal.source_family,
        "kind": signal.kind,
        "source_id": signal.source_id,
        "author_handle": signal.author_handle,
        "text": signal.text,
        "language": signal.language,
        "sentiment": signal.sentiment,
        "topics": signal.topics,
        "engagement": signal.engagement,
        "region": signal.region.model_dump() if signal.region else None,
        "observed_at": signal.observed_at,
        "fetched_at": signal.fetched_at,
        "url": signal.url,
        "extra": signal.extra,
    }


def upsert_signal(signal: HumanSignal) -> None:
    """Insert or refresh one signal, keyed on its stable "{source}:{source_id}"
    id — re-running an adapter never duplicates."""
    row = _signal_row(signal)
    with session() as s:
        exists = s.execute(select(human_signals.c.id).where(human_signals.c.id == signal.id)).first()
        if exists:
            s.execute(human_signals.update().where(human_signals.c.id == signal.id).values(**row))
        else:
            s.execute(human_signals.insert().values(**row))


def purge_deleted(source: str, source_ids: list[str]) -> int:
    """Reddit terms: remove content within 48h of the author deleting it."""
    if not source_ids:
        return 0
    with session() as s:
        result = s.execute(
            delete(human_signals).where(
                human_signals.c.source == source,
                human_signals.c.source_id.in_(source_ids),
            )
        )
        return result.rowcount or 0


def count_signals(source: str | None = None) -> int:
    with session() as s:
        stmt = select(func.count()).select_from(human_signals)
        if source:
            stmt = stmt.where(human_signals.c.source == source)
        return s.execute(stmt).scalar_one()


def signals_since(source: str, since: datetime, *, limit: int = 500) -> list[HumanSignal]:
    with session() as s:
        rows = s.execute(
            select(human_signals)
            .where(human_signals.c.source == source, human_signals.c.observed_at >= since)
            .order_by(human_signals.c.observed_at.desc())
            .limit(limit)
        ).mappings()
        return [HumanSignal.model_validate(dict(r)) for r in rows]
