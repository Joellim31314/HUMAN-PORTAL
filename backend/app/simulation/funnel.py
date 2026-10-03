"""Store filtering, spatial index and aggregation (funnel, reasons, segments)."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Optional

import numpy as np

from app.schemas import (
    Agent, AgentOutcome, FunnelCounts, Outcome, ProductInput, ReasonCode,
    ReasonStat, SegmentStat, Store,
)
from app.simulation.reasons import REASON_LABELS

LAT_CELL = 0.005
LON_CELL = 0.008  # ~500 m at London latitude, so +-1 cell covers a 400 m radius
_R = 6371000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _R * math.asin(math.sqrt(h))


def select_stocking_stores(product: ProductInput, stores: list[Store]) -> list[Store]:
    sk = product.stockists
    kinds = set(sk.store_kinds)
    chains = [c.lower() for c in sk.chains if c.strip()]
    boroughs = {b.lower() for b in sk.boroughs}
    matched: list[Store] = []
    for s in stores:
        if s.kind not in kinds:
            continue
        if chains:
            hay = f"{s.brand or ''} {s.name}".lower()
            if not any(c in hay for c in chains):
                continue
        if boroughs and (s.borough or "").lower() not in boroughs:
            continue
        matched.append(s)
    if sk.coverage >= 1.0 or not matched:
        return matched
    rng = np.random.default_rng([product.seed, 7919])
    keep = rng.random(len(matched)) < sk.coverage
    return [s for s, k in zip(matched, keep) if k]


class StoreIndex:
    def __init__(self, stores: list[Store]):
        self.cells: dict[tuple[int, int], list[Store]] = defaultdict(list)
        for s in stores:
            self.cells[self._key(s.lat, s.lon)].append(s)
        self._cache: dict[tuple[float, float], Optional[tuple[Store, float]]] = {}

    @staticmethod
    def _key(lat: float, lon: float) -> tuple[int, int]:
        return (math.floor(lat / LAT_CELL), math.floor(lon / LON_CELL))

    def nearest_within(self, lat: float, lon: float, radius_m: float) -> Optional[tuple[Store, float]]:
        ck = (round(lat, 6), round(lon, 6))
        if ck in self._cache:
            return self._cache[ck]
        ky, kx = self._key(lat, lon)
        best: Optional[tuple[Store, float]] = None
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for s in self.cells.get((ky + dy, kx + dx), ()):
                    d = haversine_m(lat, lon, s.lat, s.lon)
                    if d <= radius_m and (best is None or d < best[1]):
                        best = (s, d)
        self._cache[ck] = best
        return best


def build_reasons(outcomes: list[AgentOutcome]) -> list[ReasonStat]:
    total = max(1, len(outcomes))
    c = Counter(o.reason for o in outcomes)
    return [
        ReasonStat(code=code, label=REASON_LABELS[code], count=n, pct=round(100.0 * n / total, 1))
        for code, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0].value))
    ]


def build_segments(agents: list[Agent], outcomes: list[AgentOutcome]) -> list[SegmentStat]:
    dims = ["age_band", "sex", "ethnicity", "borough", "archetype", "income_band"]
    out: list[SegmentStat] = []
    for dim in dims:
        groups: dict[str, list[AgentOutcome]] = defaultdict(list)
        for a, o in zip(agents, outcomes):
            groups[str(getattr(a, dim))].append(o)
        for value in sorted(groups):
            os_ = groups[value]
            total = len(os_)
            bought = sum(1 for o in os_ if o.outcome == Outcome.bought)
            interested = sum(1 for o in os_ if o.outcome in (Outcome.rejected, Outcome.bought))
            rc = Counter(o.reason for o in os_ if o.reason != ReasonCode.BOUGHT)
            top = rc.most_common(1)[0][0] if rc else ReasonCode.BOUGHT
            out.append(SegmentStat(
                dimension=dim, value=value, total=total, interested=interested,
                bought=bought, conversion=round(bought / total, 4), top_reason=top,
            ))
    return out


def build_funnel(outcomes: list[AgentOutcome], needed_flags: list[bool]) -> FunnelCounts:
    return FunnelCounts(
        total=len(outcomes),
        exposed=sum(1 for o in outcomes if o.exposures > 0),
        noticed=sum(1 for o in outcomes if o.noticed),
        needed=sum(1 for o, n in zip(outcomes, needed_flags) if n),
        bought=sum(1 for o in outcomes if o.outcome == Outcome.bought),
    )
