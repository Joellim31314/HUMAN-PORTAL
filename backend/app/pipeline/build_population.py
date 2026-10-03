"""End-to-end: fetch (cached) -> sample -> write data/processed/agents.json + stores.json.

Run from backend/:  .venv/Scripts/python -m app.pipeline.build_population
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

import numpy as np

from app.config import AGENTS_PATH, POPULATION_SEED, POPULATION_SIZE, PROCESSED_DIR, STORES_PATH
from app.pipeline.fetch_census import fetch_all
from app.pipeline.fetch_centroids import fetch_centroids
from app.pipeline.fetch_pois import element_point, fetch_pois
from app.population.geography import haversine_m, home_point, nearest_point, pick_campus, pick_work
from app.population.names import make_name
from app.population.sampler import AGE_EDGES, allocate, build_profiles, sample_person
from app.population.schedules import build_schedule
from app.population.traits import make_diet, make_media, make_traits
from app.schemas import Agent, GeoPoint, Store


def build_stores(profiles: list[dict]) -> list[Store]:
    cent = np.array([[p["lat"], p["lon"]] for p in profiles])
    stores: list[Store] = []
    for e in fetch_pois("shops"):
        pt = element_point(e)
        if pt is None:
            continue
        d = haversine_m(pt[0], pt[1], cent[:, 0], cent[:, 1])
        j = int(np.argmin(d))
        if d[j] > 3000:
            continue
        tags = e.get("tags", {})
        kind = tags.get("shop")
        if kind not in ("convenience", "supermarket"):
            continue
        brand = tags.get("brand") or None
        stores.append(Store(
            id=f"osm-{e['type']}-{e['id']}", name=tags.get("name") or brand or "Local shop", brand=brand,
            kind=kind, lat=round(pt[0], 5), lon=round(pt[1], 5), borough=profiles[j]["borough"]))
    return stores


def build_campuses() -> list[dict]:
    groups: dict[str, list] = defaultdict(list)
    for e in fetch_pois("unis"):
        name = e.get("tags", {}).get("name")
        pt = element_point(e)
        if name and pt:
            groups[name].append(pt)
    return [{"name": n, "points": pts} for n, pts in groups.items()]


def build_agents(profiles: list[dict], n: int, seed: int, campuses: list[dict], gyms: np.ndarray) -> list[Agent]:
    rng = np.random.default_rng(seed)
    counts = allocate([p["adult_pop"] for p in profiles], n)
    agents: list[Agent] = []
    idx = 0
    for prof, cnt in zip(profiles, counts):
        for _ in range(int(cnt)):
            person = sample_person(rng, prof)
            age, arch = person["age"], person["archetype"]
            home = home_point(rng, (prof["lat"], prof["lon"]))
            traits = make_traits(rng, age, person["income_band"])
            commuter = arch in ("office_commuter", "shift_worker", "student") and person["travel_mode"] in (
                "underground", "train", "bus")
            media = make_media(rng, age, commuter)
            diet = make_diet(rng, age, person["religion"], traits.health_consciousness)
            name = make_name(person["ethnicity"], person["ethnicity_detail"], person["religion"], person["sex"], rng)

            work = work_label = None
            if arch in ("office_commuter", "shift_worker"):
                work, work_label = pick_work(rng, home, arch, person["travel_mode"])
            elif arch == "student":
                res = pick_campus(rng, home, campuses)
                work, work_label = res if res else pick_work(rng, home, "office_commuter", person["travel_mode"])
            gym = None
            gp = float(np.clip(0.55 * traits.health_consciousness - 0.1 + (0.1 if age < 45 else 0)
                               + 0.15 * (traits.extraversion - 0.5), 0.02, 0.6))
            if rng.random() < gp:
                gym = nearest_point(home, gyms)
            sched = build_schedule(rng, arch, home, work, gym, jobless=person["economic_status"] == "unemployed")

            agents.append(Agent(
                id=f"a{idx:05d}", name=name, age=age, age_band=person["age_band"], sex=person["sex"],
                ethnicity=person["ethnicity"], ethnicity_detail=person["ethnicity_detail"],
                religion=person["religion"], economic_status=person["economic_status"],
                occupation=person["occupation"], income_band=person["income_band"], archetype=arch,
                travel_mode=person["travel_mode"], msoa_code=prof["code"], msoa_name=prof["name"],
                borough=prof["borough"], home=GeoPoint(lat=round(home[0], 5), lon=round(home[1], 5)),
                work=GeoPoint(lat=round(work[0], 5), lon=round(work[1], 5)) if work else None,
                work_label=work_label, traits=traits, media=media, diet_flags=diet, schedule=sched))
            idx += 1
    return agents


def _pct(counter: Counter, total: int, top: int | None = None) -> str:
    items = counter.most_common(top)
    return ", ".join(f"{k} {100 * v / total:.1f}%" for k, v in items)


def summarise(agents: list[Agent], profiles: list[dict], stores: list[Store]) -> None:
    n = len(agents)
    print(f"\n=== {n} agents, {len(stores)} stores ===")
    print("Top boroughs:", ", ".join(f"{k} {v}" for k, v in Counter(a.borough for a in agents).most_common(5)))
    print("Sex:", _pct(Counter(a.sex for a in agents), n))

    w = np.array([p["adult_pop"] for p in profiles])
    w = w / w.sum()
    from app.population.sampler import age_band_of
    census_age = Counter()
    for p, wi in zip(profiles, w):
        for (lo, hi), aw in zip(AGE_EDGES, p["age_w"]):
            census_age[age_band_of((lo + hi) // 2)] += wi * aw
    sim = Counter(a.age_band for a in agents)
    print("Age band  sim vs census:", "; ".join(
        f"{b} {100 * sim[b] / n:.1f}/{100 * census_age[b]:.1f}" for b in ["16-24", "25-34", "35-44", "45-54", "55-64", "65+"]))
    census_eth = Counter()
    for p, wi in zip(profiles, w):
        for g, pr in zip(p["eth_groups"], p["eth_p"]):
            census_eth[g] += wi * pr
    sim = Counter(a.ethnicity for a in agents)
    print("Ethnicity sim vs census:", "; ".join(
        f"{g} {100 * sim[g] / n:.1f}/{100 * census_eth[g]:.1f}" for g in ["White", "Asian", "Black", "Mixed", "Other"]))
    print("Archetype:", _pct(Counter(a.archetype for a in agents), n))
    print("Economic status:", _pct(Counter(a.economic_status for a in agents), n))
    print("Income:", _pct(Counter(a.income_band for a in agents), n))
    print("Religion:", _pct(Counter(a.religion for a in agents), n, 5))
    print("Travel:", _pct(Counter(a.travel_mode for a in agents), n))
    print("Work places:", _pct(Counter(a.work_label for a in agents if a.work_label), sum(1 for a in agents if a.work_label), 8))
    print("Diet flags:", _pct(Counter(f for a in agents for f in a.diet_flags), n))
    print("Stores by kind:", dict(Counter(s.kind for s in stores)),
          "| branded:", sum(1 for s in stores if s.brand))
    print("Top brands:", Counter(s.brand for s in stores if s.brand).most_common(6))


def main() -> None:
    print("Loading census tables...")
    tables = fetch_all()
    centroids = fetch_centroids()
    profiles = build_profiles(tables, centroids)
    print(f"{len(profiles)} London MSOAs")
    campuses = build_campuses()
    gyms = np.array([pt for e in fetch_pois("gyms") if (pt := element_point(e))])
    print(f"{len(campuses)} named university sites, {len(gyms)} gyms")

    stores = build_stores(profiles)
    agents = build_agents(profiles, POPULATION_SIZE, POPULATION_SEED, campuses, gyms)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    AGENTS_PATH.write_text(json.dumps([a.model_dump(mode="json") for a in agents], separators=(",", ":")), encoding="utf-8")
    STORES_PATH.write_text(json.dumps([s.model_dump(mode="json") for s in stores], separators=(",", ":")), encoding="utf-8")
    print(f"wrote {AGENTS_PATH} ({AGENTS_PATH.stat().st_size / 1e6:.2f} MB), {STORES_PATH} ({STORES_PATH.stat().st_size / 1e6:.2f} MB)")
    summarise(agents, profiles, stores)


if __name__ == "__main__":
    main()
