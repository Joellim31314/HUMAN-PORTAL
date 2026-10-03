"""Category knowledge: reference prices, need profiles and belief rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from app.schemas import Agent, ProductInput, ScheduleEntry

REF_PRICE: dict[str, float] = {
    "energy_drink": 1.60, "soft_drink": 1.40, "coffee_rtd": 2.20, "snack": 1.20,
    "healthy_snack": 1.80, "confectionery": 1.00, "ready_meal": 4.00, "alcohol": 2.50,
    "other": 2.00,
}

CAFFEINATED = {"energy_drink", "coffee_rtd"}
SUGARY = {"energy_drink", "soft_drink", "confectionery"}
ANIMAL_RISK = {"snack", "ready_meal", "confectionery"}
HALAL_RISK = {"ready_meal", "snack"}


@dataclass
class Profile:
    base: float
    act: dict[str, float]
    slot: dict[str, float]
    extra: Optional[Callable[[Agent, ScheduleEntry, str], float]] = None


def _energy_extra(a: Agent, e: ScheduleEntry, day_type: str) -> float:
    m = (1.3 if a.age < 35 else 0.9 if a.age < 55 else 0.4) * (1 - 0.5 * a.traits.health_consciousness)
    if a.archetype == "shift_worker" and e.slot in ("night", "early_morning") and e.activity == "working":
        m *= 1.8
    return m


def _coffee_extra(a: Agent, e: ScheduleEntry, day_type: str) -> float:
    return 1.2 if a.age >= 25 else 0.9


def _soft_extra(a: Agent, e: ScheduleEntry, day_type: str) -> float:
    return (1.2 if a.age < 35 else 1.0) * (1 - 0.4 * a.traits.health_consciousness)


def _snack_extra(a: Agent, e: ScheduleEntry, day_type: str) -> float:
    return 1.0 + 0.3 * (1 - a.traits.conscientiousness)


def _healthy_extra(a: Agent, e: ScheduleEntry, day_type: str) -> float:
    return 0.4 + 1.6 * a.traits.health_consciousness


def _confect_extra(a: Agent, e: ScheduleEntry, day_type: str) -> float:
    return (1.2 if a.age < 30 else 1.0) * (1 - 0.3 * a.traits.health_consciousness)


def _meal_extra(a: Agent, e: ScheduleEntry, day_type: str) -> float:
    m = 1.0
    if a.archetype in ("office_commuter", "shift_worker"):
        m *= 1.4
    if a.archetype in ("wfh", "retired", "carer"):
        m *= 0.7
    return m


def _alcohol_extra(a: Agent, e: ScheduleEntry, day_type: str) -> float:
    if a.age < 18:
        return 0.0
    m = 1.6 if day_type == "weekend" else 0.8
    return m * (1.2 if a.age < 45 else 1.0)


_ALL = ("sleeping", "commuting", "working", "studying", "exercising",
        "socialising", "relaxing", "shopping", "caring")


def _act(**kw: float) -> dict[str, float]:
    d = {k: 0.0 for k in _ALL}
    d.update(kw)
    return d


PROFILES: dict[str, Profile] = {
    "energy_drink": Profile(
        0.06,
        _act(commuting=1.5, studying=1.3, working=1.0, exercising=1.4, socialising=0.6,
             relaxing=0.3, shopping=0.8, caring=0.4),
        dict(early_morning=1.2, morning=1.5, midday=0.9, afternoon=1.4, evening=0.9,
             late_evening=0.5, night=1.0),
        _energy_extra),
    "soft_drink": Profile(
        0.06,
        _act(commuting=0.8, studying=0.8, working=0.8, exercising=1.4, socialising=1.5,
             relaxing=0.6, shopping=1.0, caring=0.5),
        dict(early_morning=0.4, morning=0.7, midday=1.5, afternoon=1.4, evening=0.9,
             late_evening=0.7, night=0.2),
        _soft_extra),
    "coffee_rtd": Profile(
        0.06,
        _act(commuting=1.6, studying=1.0, working=1.3, exercising=0.3, socialising=0.6,
             relaxing=0.4, shopping=0.8, caring=0.6),
        dict(early_morning=1.6, morning=1.8, midday=1.0, afternoon=0.8, evening=0.4,
             late_evening=0.1, night=0.1),
        _coffee_extra),
    "snack": Profile(
        0.06,
        _act(commuting=1.3, studying=1.4, working=1.0, exercising=0.4, socialising=0.8,
             relaxing=0.7, shopping=1.0, caring=0.6),
        dict(early_morning=0.4, morning=0.7, midday=1.0, afternoon=1.5, evening=1.2,
             late_evening=0.6, night=0.3),
        _snack_extra),
    "healthy_snack": Profile(
        0.05,
        _act(commuting=0.8, studying=0.8, working=1.2, exercising=1.8, socialising=0.4,
             relaxing=0.4, shopping=0.8, caring=0.6),
        dict(early_morning=0.8, morning=1.0, midday=1.2, afternoon=1.3, evening=0.9,
             late_evening=0.3, night=0.1),
        _healthy_extra),
    "confectionery": Profile(
        0.05,
        _act(commuting=1.2, studying=1.2, working=0.8, exercising=0.2, socialising=0.9,
             relaxing=0.8, shopping=1.2, caring=0.6),
        dict(early_morning=0.3, morning=0.6, midday=1.0, afternoon=1.5, evening=1.2,
             late_evening=0.8, night=0.3),
        _confect_extra),
    "ready_meal": Profile(
        0.06,
        _act(commuting=1.4, studying=0.6, working=1.0, exercising=0.1, socialising=0.3,
             relaxing=0.8, shopping=1.5, caring=0.6),
        dict(early_morning=0.1, morning=0.2, midday=1.3, afternoon=0.7, evening=2.2,
             late_evening=1.4, night=0.3),
        _meal_extra),
    "alcohol": Profile(
        0.05,
        _act(commuting=0.6, working=0.1, studying=0.1, exercising=0.0, socialising=2.0,
             relaxing=0.9, shopping=1.0, caring=0.1),
        dict(early_morning=0.0, morning=0.0, midday=0.1, afternoon=0.4, evening=1.3,
             late_evening=2.2, night=0.6),
        _alcohol_extra),
    "other": Profile(
        0.04,
        _act(commuting=1.0, studying=1.0, working=1.0, exercising=0.8, socialising=1.0,
             relaxing=0.8, shopping=1.5, caring=0.8),
        dict(early_morning=0.6, morning=1.0, midday=1.2, afternoon=1.2, evening=1.2,
             late_evening=0.8, night=0.2),
        None),
}


def need_prob(category: str, agent: Agent, entry: ScheduleEntry, day_type: str) -> float:
    """Probability the agent wants this category during this schedule slot."""
    p = PROFILES.get(category, PROFILES["other"])
    a = p.act.get(entry.activity, 0.0)
    if a == 0.0:
        return 0.0
    v = p.base * a * p.slot.get(entry.slot, 1.0)
    if p.extra:
        v *= p.extra(agent, entry, day_type)
    return min(0.9, max(0.0, v))


# --- price -----------------------------------------------------------------


def price_reject_prob(product: ProductInput, agent: Agent) -> tuple[float, float]:
    ref = REF_PRICE.get(product.category, 2.0)
    ratio = product.price_gbp / ref
    ps = agent.traits.price_sensitivity
    income = {"low": 1.3, "mid": 1.0, "high": 0.7}[agent.income_band]
    p = (0.04 + max(0.0, ratio - 0.8) * 0.35 * (0.4 + 1.2 * ps)) * income
    return min(0.98, max(0.0, p)), ratio


# --- beliefs ---------------------------------------------------------------


def belief_conflicts(product: ProductInput, agent: Agent) -> list[tuple[float, str]]:
    """List of (reject probability, human reason). Combined multiplicatively."""
    cat, claims, flags = product.category, set(product.claims), set(agent.diet_flags)
    out: list[tuple[float, str]] = []
    is_alcohol = cat == "alcohol" or "alcoholic" in claims
    caffeinated = cat in CAFFEINATED or "caffeinated" in claims
    muslim = agent.religion == "Muslim" or "halal" in flags

    if muslim and is_alcohol:
        out.append((0.97, "alcohol is not permitted by their faith"))
    if muslim and cat in HALAL_RISK and "halal" not in claims:
        out.append((0.35, "it is not marked halal"))
    if (agent.religion == "Jewish" or "kosher" in flags) and cat in HALAL_RISK and "kosher" not in claims:
        out.append((0.3, "it is not marked kosher"))
    if "caffeine_avoider" in flags and caffeinated:
        out.append((0.9, "they avoid caffeine"))
    if cat in SUGARY and not ({"sugar_free", "low_calorie"} & claims):
        if flags & {"health_conscious", "low_sugar"}:
            out.append((0.75, "it is sugary and they watch their sugar intake"))
        elif agent.traits.health_consciousness > 0.5:
            out.append((0.3 * agent.traits.health_consciousness, "it does not fit a healthy lifestyle"))
    if cat in ANIMAL_RISK:
        if "vegan" in flags and not ({"vegan", "plant_based"} & claims):
            out.append((0.85, "it is not vegan"))
        elif "vegetarian" in flags and not ({"vegetarian", "vegan", "plant_based"} & claims):
            out.append((0.6, "it is not clearly vegetarian"))
    return out


def belief_reject_prob(product: ProductInput, agent: Agent) -> tuple[float, str]:
    conf = belief_conflicts(product, agent)
    if not conf:
        return 0.0, ""
    keep = 1.0
    for p, _ in conf:
        keep *= 1 - p
    return 1 - keep, "; ".join(t for _, t in conf)


def loyalty_stay_prob(agent: Agent) -> float:
    t = agent.traits
    return max(0.0, min(0.6, 0.5 * t.brand_loyalty * (1 - 0.6 * t.novelty_seeking)))
