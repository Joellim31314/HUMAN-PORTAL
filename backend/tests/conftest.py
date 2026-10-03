"""Synthetic fixtures shared by simulation/API tests (plain factories + pytest fixtures)."""

from __future__ import annotations

import numpy as np
import pytest

from app.schemas import Agent, GeoPoint, ScheduleEntry, Store, Traits

HOME = (51.5074, -0.1278)
WORK = (51.5450, -0.0400)  # ~7 km from HOME


def _mid(a, b, f=0.5):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def make_schedule(home=HOME, work=WORK) -> dict:
    mid = _mid(home, work)

    def e(slot, place, act, loc):
        return ScheduleEntry(slot=slot, place=place, activity=act, location=GeoPoint(lat=loc[0], lon=loc[1]))

    weekday = [
        e("early_morning", "home", "relaxing", home),
        e("morning", "transit", "commuting", mid),
        e("midday", "work", "working", work),
        e("afternoon", "work", "working", work),
        e("evening", "transit", "commuting", mid),
        e("late_evening", "home", "relaxing", home),
        e("night", "home", "sleeping", home),
    ]
    weekend = [
        e("early_morning", "home", "sleeping", home),
        e("morning", "home", "relaxing", home),
        e("midday", "local", "shopping", home),
        e("afternoon", "central", "socialising", _mid(home, work, 0.2)),
        e("evening", "central", "socialising", _mid(home, work, 0.2)),
        e("late_evening", "home", "relaxing", home),
        e("night", "home", "sleeping", home),
    ]
    return {"weekday": weekday, "weekend": weekend}


def make_agent(**overrides) -> Agent:
    """Build a valid Agent; overrides may include traits=dict(...), home=(lat, lon), work=(lat, lon)."""
    home = overrides.pop("home", HOME)
    work = overrides.pop("work", WORK)
    trait_over = overrides.pop("traits", {})
    traits = dict(openness=0.5, conscientiousness=0.5, extraversion=0.5, agreeableness=0.5,
                  neuroticism=0.5, attention=0.5, price_sensitivity=0.5, health_consciousness=0.3,
                  brand_loyalty=0.3, novelty_seeking=0.5)
    traits.update(trait_over)
    schedule = overrides.pop("schedule", None) or make_schedule(home, work)
    data = dict(
        id="a00001", name="Test Agent", age=28, age_band="25-34", sex="female", ethnicity="White",
        ethnicity_detail="English", religion="No religion", economic_status="employed",
        occupation="Professional", income_band="mid", archetype="office_commuter",
        travel_mode="underground", msoa_code="E02000001", msoa_name="City", borough="Westminster",
        home=GeoPoint(lat=home[0], lon=home[1]), work=GeoPoint(lat=work[0], lon=work[1]),
        work_label="Central", traits=Traits(**traits), media={"tiktok": 0.3, "instagram": 0.3},
        diet_flags=[], schedule=schedule,
    )
    data.update(overrides)
    return Agent(**data)


def make_store(i: int = 1, lat: float = HOME[0], lon: float = HOME[1], **overrides) -> Store:
    data = dict(id=f"osm-node-{i}", name=f"Shop {i}", brand="Tesco Express", kind="convenience",
                lat=lat, lon=lon, borough="Westminster")
    data.update(overrides)
    return Store(**data)


def make_population(n: int = 200, seed: int = 0, **overrides) -> list[Agent]:
    """Agents spread randomly over London with varied traits/archetypes."""
    rng = np.random.default_rng(seed)
    out = []
    boroughs = ["Westminster", "Camden", "Hackney", "Lambeth", "Newham"]
    archetypes = ["office_commuter", "shift_worker", "student", "wfh", "retired", "carer"]
    ethn = ["White", "Asian", "Black", "Mixed", "Other"]
    for i in range(n):
        home = (51.40 + rng.random() * 0.20, -0.25 + rng.random() * 0.35)
        work = (51.40 + rng.random() * 0.20, -0.25 + rng.random() * 0.35)
        age = int(rng.integers(18, 70))
        band = ("16-24" if age < 25 else "25-34" if age < 35 else "35-44" if age < 45
                else "45-54" if age < 55 else "55-64" if age < 65 else "65+")
        tr = {k: float(rng.random()) for k in (
            "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism",
            "attention", "price_sensitivity", "health_consciousness", "brand_loyalty", "novelty_seeking")}
        flags = [f for f, p in (("vegetarian", 0.07), ("health_conscious", 0.15),
                                ("caffeine_avoider", 0.06)) if rng.random() < p]
        out.append(make_agent(
            id=f"a{i:05d}", home=home, work=work, age=age, age_band=band,
            sex="female" if rng.random() < 0.5 else "male",
            ethnicity=ethn[int(rng.integers(0, 5))], borough=boroughs[int(rng.integers(0, 5))],
            archetype=archetypes[int(rng.integers(0, 6))],
            income_band=["low", "mid", "high"][int(rng.integers(0, 3))],
            religion="Muslim" if rng.random() < 0.1 else "No religion",
            diet_flags=flags,
            media={"tiktok": float(rng.random()), "instagram": float(rng.random()), "ooh": float(rng.random())},
            traits=tr, **overrides))
    return out


def make_stores(n: int = 5000, seed: int = 1) -> list[Store]:
    rng = np.random.default_rng(seed)
    brands = ["Tesco Express", "Sainsburys Local", "Co-op", None]
    return [make_store(i, 51.40 + rng.random() * 0.20, -0.25 + rng.random() * 0.35,
                       kind="convenience" if rng.random() < 0.8 else "supermarket",
                       brand=brands[int(rng.integers(0, 4))])
            for i in range(n)]


@pytest.fixture
def agent():
    return make_agent()


@pytest.fixture
def population():
    return make_population(200)


@pytest.fixture
def stores():
    return make_stores(1000)
