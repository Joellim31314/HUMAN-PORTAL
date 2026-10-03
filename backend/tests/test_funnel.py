import time
from collections import Counter

from app.schemas import Outcome, ProductInput, ReasonCode, Stockists
from app.simulation.engine import run_funnel
from app.simulation.reasons import REASON_LABELS
from tests.conftest import HOME, WORK, make_agent, make_population, make_store, make_stores


def prod(**kw):
    d = dict(name="Volt", category="energy_drink", description="x", price_gbp=1.8,
             stockists=Stockists(coverage=1.0), packaging_salience=3)
    d.update(kw)
    return ProductInput(**d)


def _everywhere(n=300, traits=None, **agent_kw):
    tr = dict(attention=0.95)
    tr.update(traits or {})
    agents = [make_agent(id=f"a{i}", traits=tr, **agent_kw) for i in range(n)]
    mid = ((HOME[0] + WORK[0]) / 2, (HOME[1] + WORK[1]) / 2)
    stores = [make_store(1, *HOME), make_store(2, *WORK), make_store(3, *mid)]
    return agents, stores


def test_labels_cover_all_reasons():
    assert set(REASON_LABELS) == set(ReasonCode)


def test_determinism():
    pop, stores = make_population(100), make_stores(500)
    p = prod(stockists=Stockists(coverage=0.5))
    a = run_funnel(p, pop, stores)
    b = run_funnel(p, pop, stores)
    assert [o.model_dump() for o in a.outcomes] == [o.model_dump() for o in b.outcomes]
    c = run_funnel(prod(seed=1, stockists=Stockists(coverage=0.5)), pop, stores)
    assert [o.model_dump() for o in a.outcomes] != [o.model_dump() for o in c.outcomes]


def test_no_stores():
    pop = make_population(50)
    r = run_funnel(prod(), pop, [])
    assert all(o.outcome == Outcome.never_exposed and o.reason == ReasonCode.NO_STORE_NEARBY for o in r.outcomes)
    assert r.funnel.exposed == 0 and r.funnel.bought == 0
    assert r.reasons[0].code == ReasonCode.NO_STORE_NEARBY and r.reasons[0].pct == 100.0


def test_stockist_filters():
    stores = [make_store(1, brand="Tesco Express"), make_store(2, brand="Co-op", borough="Camden"),
              make_store(3, brand=None, name="TESCO Metro", kind="supermarket")]
    r = run_funnel(prod(stockists=Stockists(chains=["tesco"], coverage=1.0)), [make_agent()], stores)
    assert {s.id for s in r.stores_stocking} == {"osm-node-1", "osm-node-3"}
    r = run_funnel(prod(stockists=Stockists(boroughs=["camden"], coverage=1.0)), [make_agent()], stores)
    assert [s.id for s in r.stores_stocking] == ["osm-node-2"]
    r = run_funnel(prod(stockists=Stockists(store_kinds=["supermarket"], coverage=1.0)), [make_agent()], stores)
    assert [s.id for s in r.stores_stocking] == ["osm-node-3"]


def test_not_there_when_needed():
    agents = [make_agent(id=f"a{i}", traits=dict(attention=0.9)) for i in range(300)]
    stores = [make_store(1, *HOME)]  # only near home; commute/work are ~7 km away
    r = run_funnel(prod(packaging_salience=5), agents, stores)
    no_need = [o for o in r.outcomes if o.outcome == Outcome.no_need]
    assert len(no_need) > 30
    ntwn = sum(1 for o in no_need if o.reason == ReasonCode.NOT_THERE_WHEN_NEEDED)
    assert ntwn > 0.6 * len(no_need)
    top_fail = Counter(o.reason for o in r.outcomes if o.outcome != Outcome.bought).most_common(1)[0][0]
    assert top_fail == ReasonCode.NOT_THERE_WHEN_NEEDED
    some = [t for tr in r.traces.values() for t in tr if t.step == "need" and not t.passed]
    assert some and "no store" in some[0].detail


def test_too_expensive():
    agents, stores = _everywhere(traits=dict(price_sensitivity=0.9))
    r = run_funnel(prod(price_gbp=12.0, packaging_salience=5), agents, stores)
    rej = Counter(o.reason for o in r.outcomes if o.outcome == Outcome.rejected)
    assert rej and rej.most_common(1)[0][0] == ReasonCode.TOO_EXPENSIVE
    cheap = run_funnel(prod(price_gbp=1.5, packaging_salience=5), agents, stores)
    assert cheap.funnel.bought > r.funnel.bought


def test_halal_alcohol_belief_conflict():
    agents, stores = _everywhere(religion="Muslim", diet_flags=["halal"], age=30)
    r = run_funnel(prod(category="alcohol", price_gbp=2.5, packaging_salience=5), agents, stores)
    rej = Counter(o.reason for o in r.outcomes if o.outcome == Outcome.rejected)
    assert rej and rej.most_common(1)[0][0] == ReasonCode.BELIEF_CONFLICT
    assert r.funnel.bought < 0.1 * len(agents)


def test_caffeine_avoider():
    agents, stores = _everywhere(diet_flags=["caffeine_avoider"])
    r = run_funnel(prod(), agents, stores)
    rej = Counter(o.reason for o in r.outcomes if o.outcome == Outcome.rejected)
    assert rej.most_common(1)[0][0] == ReasonCode.BELIEF_CONFLICT


def test_salience_increases_noticing():
    pop, stores = make_population(300), make_stores(1500)
    lo = run_funnel(prod(packaging_salience=1, stockists=Stockists(coverage=0.5)), pop, stores)
    hi = run_funnel(prod(packaging_salience=5, stockists=Stockists(coverage=0.5)), pop, stores)
    assert hi.funnel.noticed > lo.funnel.noticed * 1.5


def test_ads_increase_noticing():
    pop, stores = make_population(300), make_stores(1500)
    base = run_funnel(prod(stockists=Stockists(coverage=0.5)), pop, stores)
    ads = run_funnel(prod(stockists=Stockists(coverage=0.5), marketing_channels=["tiktok", "instagram", "ooh"],
                          marketing_intensity=1.0), pop, stores)
    assert ads.funnel.noticed > base.funnel.noticed


def test_structure_and_realism():
    pop, stores = make_population(500), make_stores(5000)
    r = run_funnel(prod(stockists=Stockists(store_kinds=["convenience"], coverage=0.35)), pop, stores)
    f = r.funnel
    assert f.total == 500 and f.bought <= f.needed <= f.noticed <= f.exposed <= f.total
    assert sum(x.count for x in r.reasons) == 500
    assert [x.count for x in r.reasons] == sorted((x.count for x in r.reasons), reverse=True)
    dims = {s.dimension for s in r.segments}
    assert dims == {"age_band", "sex", "ethnicity", "borough", "archetype", "income_band"}
    assert all(len(t) <= 25 or all(e.step == "purchase" for e in t[25:]) for t in r.traces.values())
    bought = [o for o in r.outcomes if o.outcome == Outcome.bought]
    assert all(o.reason == ReasonCode.BOUGHT and o.purchases >= 1 for o in bought)
    assert all(any(t.step == "purchase" for t in r.traces[o.agent_id]) for o in bought)
    assert f.exposed / f.total > 0.05
    assert f.bought / f.total < 0.3


def test_perf():
    pop, stores = make_population(2000), make_stores(5000)
    t0 = time.time()
    run_funnel(prod(stockists=Stockists(coverage=0.35)), pop, stores)
    assert time.time() - t0 < 5
