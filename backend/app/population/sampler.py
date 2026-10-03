"""Census-driven demographic sampling. Pure functions over per-MSOA profiles."""
from __future__ import annotations

import numpy as np
import pandas as pd

# 16+ age bands: (lo, hi) inclusive. Source columns are 5-year bands (15-19 scaled to 16-19).
AGE_EDGES = [(16, 19), (20, 24), (25, 29), (30, 34), (35, 39), (40, 44), (45, 49), (50, 54),
             (55, 59), (60, 64), (65, 69), (70, 74), (75, 79), (80, 84), (85, 94)]
AGE_COLS = ["Age: Aged 15 to 19 years", "Age: Aged 20 to 24 years", "Age: Aged 25 to 29 years",
            "Age: Aged 30 to 34 years", "Age: Aged 35 to 39 years", "Age: Aged 40 to 44 years",
            "Age: Aged 45 to 49 years", "Age: Aged 50 to 54 years", "Age: Aged 55 to 59 years",
            "Age: Aged 60 to 64 years", "Age: Aged 65 to 69 years", "Age: Aged 70 to 74 years",
            "Age: Aged 75 to 79 years", "Age: Aged 80 to 84 years", "Age: Aged 85 years and over"]

RELIGIONS = ["No religion", "Christian", "Buddhist", "Hindu", "Jewish", "Muslim", "Sikh", "Other religion"]

STATUSES = ["employed", "self_employed", "unemployed", "student", "retired", "carer"]
# multiplier of the MSOA's status share, by age band
_AGE_MULT = {
    "16-24": dict(employed=0.7, self_employed=0.3, unemployed=1.0, student=5.0, retired=0.0, carer=0.4),
    "25-34": dict(employed=1.1, self_employed=1.0, unemployed=0.9, student=0.35, retired=0.0, carer=1.0),
    "35-44": dict(employed=1.2, self_employed=1.1, unemployed=0.8, student=0.08, retired=0.0, carer=1.3),
    "45-54": dict(employed=1.2, self_employed=1.2, unemployed=0.8, student=0.04, retired=0.02, carer=0.9),
    "55-64": dict(employed=1.0, self_employed=1.1, unemployed=0.9, student=0.02, retired=0.6, carer=0.8),
    "65+": dict(employed=0.15, self_employed=0.2, unemployed=0.1, student=0.0, retired=8.0, carer=0.4),
}

OCC_INCOME_GROUP = {1: "high", 2: "high", 3: "mid", 4: "mid", 5: "mid", 6: "low", 7: "low", 8: "low", 9: "low"}
INCOME_PROBS = {  # P(low, mid, high)
    "high": (0.05, 0.35, 0.60), "mid": (0.20, 0.60, 0.20), "low": (0.65, 0.30, 0.05),
    "retired": (0.50, 0.35, 0.15), "student": (0.85, 0.13, 0.02), "unemployed": (0.90, 0.09, 0.01),
    "carer": (0.60, 0.30, 0.10),
}
SHIFT_PROB = {1: 0.03, 2: 0.05, 3: 0.05, 4: 0.05, 5: 0.15, 6: 0.50, 7: 0.35, 8: 0.45, 9: 0.40}

TRAVEL_MAP = {
    "Work mainly at or from home": "wfh", "Underground, metro, light rail, tram": "underground",
    "Train": "train", "Bus, minibus or coach": "bus", "Taxi": "other", "Motorcycle, scooter or moped": "other",
    "Driving a car or van": "car", "Passenger in a car or van": "car", "Bicycle": "bicycle",
    "On foot": "on_foot", "Other method of travel to work": "other",
}


def age_band_of(age: int) -> str:
    if age < 25:
        return "16-24"
    if age >= 65:
        return "65+"
    lo = 25 if age < 35 else 35 if age < 45 else 45 if age < 55 else 55
    return f"{lo}-{lo + 9}"


def allocate(weights, n: int) -> np.ndarray:
    """Largest-remainder allocation of n items proportional to weights."""
    w = np.asarray(weights, dtype=float)
    quota = w / w.sum() * n
    base = np.floor(quota).astype(int)
    rem = n - base.sum()
    if rem > 0:
        order = np.argsort(-(quota - base), kind="stable")
        base[order[:rem]] += 1
    return base


def _norm(s: str) -> str:
    return s.replace(" ", "").lower()


def _col(df: pd.DataFrame, text: str) -> pd.Series:
    key = _norm(text)
    for c in df.columns:
        if _norm(c) == key:
            return df[c]
    raise KeyError(text)


def _probs(arr) -> np.ndarray:
    a = np.clip(np.asarray(arr, dtype=float), 0, None)
    if a.sum() <= 0:
        a = np.ones_like(a)
    return a / a.sum()


def build_profiles(tables: dict[str, pd.DataFrame], centroids: dict[str, tuple[float, float]]) -> list[dict]:
    """One profile dict per London MSOA that has a centroid."""
    age, sex, eth = tables["ts007a"], tables["ts008"], tables["ts021"]
    rel, occ, trv, eco = tables["ts030"], tables["ts063"], tables["ts061"], tables["ts066"]

    eth_detail_cols = [c for c in eth.columns if c.count(":") == 2 and c.startswith("Ethnic group:") and "Total" not in c]
    eth_labels, eth_groups = [], []
    for c in eth_detail_cols:
        _, grp, det = [p.strip() for p in c.split(":")]
        g = grp.split(",")[0].split(" ")[0]  # Asian / Black / Mixed / White / Other
        eth_groups.append(g)
        eth_labels.append("White British" if det.startswith("English") else det)
    occ_cols = [c for c in occ.columns if c.split(":")[-1].strip()[:1].isdigit()]
    occ_labels = [c.split(":")[-1].strip().split(". ", 1)[1] for c in occ_cols]
    occ_nums = [int(c.split(":")[-1].strip().split(".")[0]) for c in occ_cols]
    trv_cols = [c for c in trv.columns if c.split(":")[-1].strip() in TRAVEL_MAP]
    trv_labels = [TRAVEL_MAP[c.split(":")[-1].strip()] for c in trv_cols]

    P = "Economic activity status: "
    out = []
    for code in age.index:
        if code not in centroids or code not in sex.index:
            continue
        a = age.loc[code, AGE_COLS].to_numpy(dtype=float)
        a[0] *= 0.8
        e = eco.loc[code]
        ec = lambda *parts: float(_col(eco.loc[[code]], P + ": ".join(parts)).iloc[0])  # noqa: E731
        active = "Economically active (excluding full-time students)"
        ecs = {
            "employed": ec(active, "In employment", "Employee"),
            "self_employed": ec(active, "In employment", "Self-employed with employees")
            + ec(active, "In employment", "Self-employed without employees"),
            "unemployed": ec(active, "Unemployed") + ec("Economically inactive", "Long-term sick or disabled")
            + ec("Economically inactive", "Other"),
            "student": ec("Economically active and a full-time student") + ec("Economically inactive", "Student"),
            "retired": ec("Economically inactive", "Retired"),
            "carer": ec("Economically inactive", "Looking after home or family"),
        }
        eth_p = _probs(eth.loc[code, eth_detail_cols].to_numpy(dtype=float))
        rel_p = _probs([_col(rel.loc[[code]], "Religion: " + r).iloc[0] for r in RELIGIONS])
        tr_vals = trv.loc[code, trv_cols].to_numpy(dtype=float)
        # merge duplicate labels
        tl = sorted(set(trv_labels))
        tr_p = _probs([sum(v for v, l in zip(tr_vals, trv_labels) if l == t) for t in tl])
        out.append({
            "code": code, "name": age.loc[code, "msoa_name"], "borough": age.loc[code, "borough"],
            "lat": centroids[code][0], "lon": centroids[code][1],
            "adult_pop": float(a.sum()), "age_w": _probs(a),
            "female_p": float(_col(sex.loc[[code]], "Sex: Female; measures: Value").iloc[0]
                              / _col(sex.loc[[code]], "Sex: All persons; measures: Value").iloc[0]),
            "eth_labels": eth_labels, "eth_groups": eth_groups, "eth_p": eth_p,
            "rel_p": rel_p,
            "econ": {k: max(v, 0.0) for k, v in ecs.items()},
            "occ_labels": occ_labels, "occ_nums": occ_nums,
            "occ_p": _probs(occ.loc[code, occ_cols].to_numpy(dtype=float)),
            "trv_labels": tl, "trv_p": tr_p,
        })
    return out


def sample_age(rng, prof) -> int:
    i = int(rng.choice(len(AGE_EDGES), p=prof["age_w"]))
    lo, hi = AGE_EDGES[i]
    return int(rng.integers(lo, hi + 1))


def sample_economic(rng, prof, age: int) -> str:
    mult = _AGE_MULT[age_band_of(age)]
    w = np.array([prof["econ"][s] * mult[s] for s in STATUSES]) + 1e-9
    return STATUSES[int(rng.choice(len(STATUSES), p=w / w.sum()))]


def sample_income(rng, status: str, occ_num: int | None) -> str:
    key = OCC_INCOME_GROUP[occ_num] if occ_num else {"self_employed": "mid"}.get(status, status)
    p = INCOME_PROBS[key]
    return ["low", "mid", "high"][int(rng.choice(3, p=p))]


def sample_person(rng, prof) -> dict:
    """Demographics + work attributes for one agent (no geography/traits)."""
    age = sample_age(rng, prof)
    sex = "female" if rng.random() < prof["female_p"] else "male"
    j = int(rng.choice(len(prof["eth_labels"]), p=prof["eth_p"]))
    religion = RELIGIONS[int(rng.choice(len(RELIGIONS), p=prof["rel_p"]))]
    status = sample_economic(rng, prof, age)
    occ_label = occ_num = None
    travel = None
    if status in ("employed", "self_employed"):
        k = int(rng.choice(len(prof["occ_labels"]), p=prof["occ_p"]))
        occ_label, occ_num = prof["occ_labels"][k], prof["occ_nums"][k]
        travel = prof["trv_labels"][int(rng.choice(len(prof["trv_labels"]), p=prof["trv_p"]))]
    else:
        travel = str(rng.choice(["on_foot", "bus", "underground", "car"], p=[0.4, 0.3, 0.2, 0.1]))
    income = sample_income(rng, status, occ_num)
    if status in ("employed", "self_employed"):
        if travel == "wfh":
            archetype = "wfh"
        elif rng.random() < SHIFT_PROB[occ_num]:
            archetype = "shift_worker"
        else:
            archetype = "office_commuter"
    else:
        archetype = {"student": "student", "retired": "retired", "carer": "carer", "unemployed": "carer"}[status]
        if status == "unemployed":
            archetype = "carer" if rng.random() < 0.3 else "retired"  # jobless: daytime-at-home/local pattern
    return {
        "age": age, "age_band": age_band_of(age), "sex": sex,
        "ethnicity": prof["eth_groups"][j], "ethnicity_detail": prof["eth_labels"][j],
        "religion": religion, "economic_status": status, "occupation": occ_label, "occ_num": occ_num,
        "income_band": income, "archetype": archetype, "travel_mode": travel,
    }
