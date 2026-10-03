"""Week-long funnel simulation: exposure -> notice -> need -> price/belief/loyalty -> purchase."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

import numpy as np

from app.config import WALK_RADIUS_M
from app.schemas import (
    DAYS, SLOTS, Agent, AgentOutcome, FunnelCounts, Outcome, ProductInput, ReasonCode,
    ReasonStat, SegmentStat, Store, TraceEvent,
)
from app.simulation import categories as cat
from app.simulation.funnel import (
    StoreIndex, build_funnel, build_reasons, build_segments, select_stocking_stores,
)

TRACE_CAP = 25
NOTICE_SCALE = 0.08        # per-exposed-slot scaling of the shelf-notice probability
SALIENCE_BASE = {1: 0.12, 2: 0.24, 3: 0.36, 4: 0.48, 5: 0.6}
REPEAT_BUY_P = 0.25
MAX_NEED_ELSEWHERE_TRACES = 3
MAX_EXPOSURE_TRACES = 5


@dataclass
class FunnelRun:
    stores_stocking: list[Store]
    outcomes: list[AgentOutcome]
    traces: dict[str, list[TraceEvent]]
    funnel: FunnelCounts
    reasons: list[ReasonStat]
    segments: list[SegmentStat]


def _ad_awareness(product: ProductInput, agent: Agent) -> float:
    s = sum(agent.media.get(ch, 0.0) for ch in product.marketing_channels) * product.marketing_intensity
    return min(1.0, s)


def _simulate_agent(idx: int, agent: Agent, product: ProductInput, index: StoreIndex):
    rng = np.random.default_rng([product.seed, idx, 1])
    n = len(DAYS) * len(SLOTS)
    u = rng.random((n, 6))  # need, notice, price, belief, loyalty, repeat
    t = agent.traits
    ad = _ad_awareness(product, agent)
    base = SALIENCE_BASE[product.packaging_salience] * (0.6 + 0.8 * t.attention)
    base *= (1 + 2.5 * ad) * (1 + 0.5 * t.novelty_seeking)
    p_notice = min(0.9, base * NOTICE_SCALE)
    p_aware_seen = min(0.95, 0.35 + 3 * p_notice)

    price_rej, ratio = cat.price_reject_prob(product, agent)
    belief_rej, belief_txt = cat.belief_reject_prob(product, agent)
    loyal_p = cat.loyalty_stay_prob(agent)

    trace: list[TraceEvent] = []

    def log(ev: TraceEvent, force: bool = False):
        if force or len(trace) < TRACE_CAP:
            trace.append(ev)

    exposures = 0
    noticed = False
    purchases = 0
    n_consider = 0
    need_elsewhere = 0
    fails: Counter = Counter()
    seen_store_days: set = set()
    expo_traces = elsewhere_traces = 0
    k = 0
    for day in DAYS:
        dt = "weekday" if day in ("mon", "tue", "wed", "thu", "fri") else "weekend"
        for entry in agent.schedule[dt]:
            row = u[k]
            k += 1
            if entry.activity == "sleeping":
                continue
            need = row[0] < cat.need_prob(product.category, agent, entry, dt)
            hit = index.nearest_within(entry.location.lat, entry.location.lon, WALK_RADIUS_M)
            where = f"{entry.place} ({entry.activity})"
            if hit is None:
                if need:
                    need_elsewhere += 1
                    if elsewhere_traces < MAX_NEED_ELSEWHERE_TRACES:
                        elsewhere_traces += 1
                        log(TraceEvent(
                            day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                            step="need", passed=False,
                            detail=f"Wanted {_category_noun(product)} while {entry.activity} at "
                                   f"{entry.place}, but no store stocking it was within walking distance."))
                continue
            store, dist = hit
            exposures += 1
            if (store.id, day) not in seen_store_days and expo_traces < MAX_EXPOSURE_TRACES:
                seen_store_days.add((store.id, day))
                expo_traces += 1
                log(TraceEvent(
                    day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                    store_id=store.id, step="exposure", passed=True,
                    detail=f"Within {int(dist)} m of {store.brand or store.name} while {entry.activity} "
                           f"at {entry.place}; the product is stocked there."))
            seen_now = row[1] < (p_aware_seen if noticed else p_notice)
            if seen_now and not noticed:
                noticed = True
                log(TraceEvent(
                    day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                    store_id=store.id, step="notice", passed=True,
                    detail=f"Spotted the product (packaging salience {product.packaging_salience}/5"
                           f"{', helped by ads they had seen' if ad > 0.15 else ''}) at "
                           f"{store.brand or store.name} while {entry.activity} at {entry.place}."))
            if not seen_now:
                if need and not noticed:
                    log(TraceEvent(
                        day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                        store_id=store.id, step="notice", passed=False,
                        detail=f"Wanted {_category_noun(product)} while {entry.activity} near "
                               f"{store.brand or store.name} but did not notice the product on the shelf."))
                continue
            if not need:
                continue

            # Consideration
            n_consider += 1
            log(TraceEvent(
                day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                store_id=store.id, step="need", passed=True,
                detail=f"Wanted {_category_noun(product)} while {entry.activity} at "
                       f"{entry.place}, near {store.brand or store.name} which stocks the product."))
            if purchases > 0:
                if row[5] < REPEAT_BUY_P:
                    purchases += 1
                    log(TraceEvent(
                        day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                        store_id=store.id, step="purchase", passed=True,
                        detail=f"Bought it again (purchase #{purchases}) at {store.brand or store.name}."), True)
                continue
            if row[2] < price_rej:
                fails["price"] += 1
                log(TraceEvent(
                    day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                    store_id=store.id, step="price", passed=False,
                    detail=f"Put off by the price of {product.price_gbp:.2f} GBP "
                           f"({ratio:.1f}x the usual {cat.REF_PRICE.get(product.category, 2.0):.2f} GBP for the category; "
                           f"price sensitivity {t.price_sensitivity:.2f}, {agent.income_band} income)."))
                continue
            if row[3] < belief_rej:
                fails["belief"] += 1
                log(TraceEvent(
                    day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                    store_id=store.id, step="belief", passed=False,
                    detail=f"Passed on it because {belief_txt}."))
                continue
            if row[4] < loyal_p:
                fails["loyalty"] += 1
                log(TraceEvent(
                    day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                    store_id=store.id, step="loyalty", passed=False,
                    detail=f"Reached for their usual brand instead (brand loyalty {t.brand_loyalty:.2f}, "
                           f"novelty seeking {t.novelty_seeking:.2f})."))
                continue
            purchases += 1
            log(TraceEvent(
                day=day, slot=entry.slot, place=entry.place, activity=entry.activity,
                store_id=store.id, step="purchase", passed=True,
                detail=f"Bought it at {store.brand or store.name} for {product.price_gbp:.2f} GBP "
                       f"while {entry.activity} at {entry.place}."), True)

    if purchases > 0:
        outcome, reason = Outcome.bought, ReasonCode.BOUGHT
    elif fails:
        step = fails.most_common(1)[0][0]
        outcome = Outcome.rejected
        reason = {"price": ReasonCode.TOO_EXPENSIVE, "belief": ReasonCode.BELIEF_CONFLICT,
                  "loyalty": ReasonCode.LOYAL_TO_EXISTING}[step]
    elif noticed:
        outcome = Outcome.no_need
        reason = ReasonCode.NOT_THERE_WHEN_NEEDED if need_elsewhere > 0 else ReasonCode.NO_NEED
    elif exposures > 0:
        outcome, reason = Outcome.not_noticed, ReasonCode.DIDNT_NOTICE
    else:
        outcome, reason = Outcome.never_exposed, ReasonCode.NO_STORE_NEARBY

    ao = AgentOutcome(
        agent_id=agent.id, lat=agent.home.lat, lon=agent.home.lon, outcome=outcome, reason=reason,
        exposures=exposures, noticed=noticed, purchases=purchases,
    )
    return ao, trace, noticed and n_consider > 0


def _category_noun(product: ProductInput) -> str:
    noun = product.category.replace("_", " ").replace(" rtd", " (ready-to-drink)")
    return f"{'an' if noun[0] in 'aeiou' else 'a'} {noun}"


def run_funnel(product: ProductInput, agents: list[Agent], stores: list[Store]) -> FunnelRun:
    stocking = select_stocking_stores(product, stores)
    index = StoreIndex(stocking)
    outcomes: list[AgentOutcome] = []
    traces: dict[str, list[TraceEvent]] = {}
    needed: list[bool] = []
    for i, agent in enumerate(agents):
        ao, tr, nd = _simulate_agent(i, agent, product, index)
        outcomes.append(ao)
        traces[agent.id] = tr
        needed.append(nd)
    return FunnelRun(
        stores_stocking=stocking,
        outcomes=outcomes,
        traces=traces,
        funnel=build_funnel(outcomes, needed),
        reasons=build_reasons(outcomes),
        segments=build_segments(agents, outcomes),
    )
