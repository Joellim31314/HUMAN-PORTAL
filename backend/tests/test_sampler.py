"""Fast offline tests for the population sampler (no network)."""
import numpy as np

from app.pipeline.build_population import build_agents
from app.population.sampler import AGE_EDGES, STATUSES, age_band_of, allocate
from app.schemas import SLOTS, Agent


def _profile(code="E02000001", lat=51.52, lon=-0.1):
    return {
        "code": code, "name": "Test 001", "borough": "Camden", "lat": lat, "lon": lon,
        "adult_pop": 8000.0, "age_w": np.ones(len(AGE_EDGES)) / len(AGE_EDGES), "female_p": 0.5,
        "eth_labels": ["White British", "Bangladeshi", "African"], "eth_groups": ["White", "Asian", "Black"],
        "eth_p": np.array([0.5, 0.3, 0.2]),
        "rel_p": np.ones(8) / 8,
        "econ": {s: 1.0 for s in STATUSES},
        "occ_labels": ["Managers, directors and senior officials", "Elementary occupations"], "occ_nums": [1, 9],
        "occ_p": np.array([0.5, 0.5]),
        "trv_labels": ["bus", "underground", "wfh", "on_foot"], "trv_p": np.array([0.3, 0.3, 0.2, 0.2]),
    }


def test_allocate_sums_to_n():
    w = np.random.default_rng(0).random(1000) * 5000
    for n in (1, 2000, 2777):
        a = allocate(w, n)
        assert a.sum() == n and (a >= 0).all()


def test_allocate_proportional():
    assert list(allocate([1, 1, 2], 4)) == [1, 1, 2]


def test_age_band_mapping():
    assert age_band_of(16) == "16-24" and age_band_of(24) == "16-24"
    assert age_band_of(25) == "25-34" and age_band_of(34) == "25-34"
    assert age_band_of(35) == "35-44" and age_band_of(54) == "45-54"
    assert age_band_of(55) == "55-64" and age_band_of(64) == "55-64"
    assert age_band_of(65) == "65+" and age_band_of(94) == "65+"


def test_agents_validate_and_schedules():
    campuses = [{"name": "Test Uni", "points": [(51.52, -0.13), (51.521, -0.131)]}]
    gyms = np.array([[51.52, -0.11], [51.5, -0.1]])
    agents = build_agents([_profile(), _profile("E02000002", 51.45, -0.2)], 200, 1, campuses, gyms)
    assert len(agents) == 200
    assert len({a.id for a in agents}) == 200
    for a in agents:
        Agent.model_validate(a.model_dump())
        assert 16 <= a.age <= 94
        assert age_band_of(a.age) == a.age_band
        for day in ("weekday", "weekend"):
            assert [e.slot for e in a.schedule[day]] == SLOTS
        if a.archetype in ("office_commuter", "shift_worker", "student"):
            assert a.work is not None and a.work_label
        if a.archetype in ("retired", "carer", "wfh"):
            assert a.work is None
    assert {"student", "retired"} <= {a.archetype for a in agents}


def test_deterministic():
    p = [_profile()]
    a = build_agents(p, 30, 5, [], np.array([[51.52, -0.11]]))
    b = build_agents(p, 30, 5, [], np.array([[51.52, -0.11]]))
    assert [x.model_dump() for x in a] == [x.model_dump() for x in b]
