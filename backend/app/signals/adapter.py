"""Adapter protocol: every data source sits behind one of these.

PROJECT.md requires adapters to be swappable (TikTok breaks; sources get
replaced). An adapter yields raw payloads, turns them into HumanSignals, and
`run_adapter` persists both idempotently.
"""

from __future__ import annotations

from typing import Iterable, Protocol

from app.signals.schema import HumanSignal, RawPayload


class SignalAdapter(Protocol):
    source: str

    def fetch(self) -> Iterable[RawPayload]:
        """Pull raw payloads from the source (one per API response/page)."""
        ...

    def normalize(self, raw: RawPayload) -> list[HumanSignal]:
        """Map one raw payload to zero or more human signals."""
        ...


def run_adapter(adapter: SignalAdapter, store, *, limit: int | None = None) -> int:
    """Fetch -> save raw -> normalize -> upsert signals. Returns signal count.

    Idempotent: re-running the same adapter only refreshes changed records
    (upsert keyed on source + source_id).
    """
    count = 0
    for raw in adapter.fetch():
        store.save_raw(raw)
        for signal in adapter.normalize(raw):
            store.upsert_signal(signal)
            count += 1
            if limit is not None and count >= limit:
                return count
    return count
