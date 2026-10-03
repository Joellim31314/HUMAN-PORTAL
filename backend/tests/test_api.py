import asyncio
import subprocess
import sys
import time
from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import config, store
from app.api import simulations
from app.main import app
from app.schemas import (
    Agent, AgentOutcome, FunnelCounts, GeoPoint, Outcome, ReasonCode, ReasonStat,
    SegmentStat, Store, TraceEvent, Traits,
)


@dataclass
class FakeFunnelRun:
    stores_stocking: list
    outcomes: list
    traces: dict
    funnel: FunnelCounts
    reasons: list
    segments: list


@pytest.fixture
def api(monkeypatch, tmp_path):
    home = GeoPoint(lat=51.51, lon=-.03)
    people = [Agent(
        id=f"a{i}", name=f"Person {i}", age=29 if i == 0 else 20,
        age_band="25-34" if i == 0 else "16-24", sex="female",
        ethnicity="Asian", ethnicity_detail="Bangladeshi", religion="Muslim",
        economic_status="employed", occupation="Office worker", income_band="mid",
        archetype="office_commuter", travel_mode="underground", msoa_code="E001",
        msoa_name="Example", borough="Tower Hamlets", home=home, work=home,
        work_label="Canary Wharf", traits=Traits(**{field: .5 for field in Traits.model_fields}),
        media={"instagram": .7}, diet_flags=["halal"], schedule={"weekday": [], "weekend": []},
    ) for i in range(3)]
    shops = [Store(id="s1", name="Tesco", brand="Tesco", kind="convenience",
                   lat=home.lat, lon=home.lon, borough="Tower Hamlets")]
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "")
    monkeypatch.setattr(config, "SIM_CACHE_DIR", tmp_path)
    monkeypatch.setattr(store, "_simulations", {})
    monkeypatch.setattr(store, "_traces", {})
    monkeypatch.setattr(store, "load_agents", lambda: people)
    monkeypatch.setattr(store, "agents_by_id", lambda: {a.id: a for a in people})
    monkeypatch.setattr(store, "load_stores", lambda: shops)
    outcomes = [AgentOutcome(agent_id=a.id, lat=home.lat, lon=home.lon,
                             outcome=outcome, reason=reason, exposures=1, noticed=True,
                             purchases=int(outcome == Outcome.bought))
                for a, outcome, reason in zip(people,
                    [Outcome.bought, Outcome.rejected, Outcome.no_need],
                    [ReasonCode.BOUGHT, ReasonCode.TOO_EXPENSIVE, ReasonCode.NO_NEED])]
    traces = {a.id: [TraceEvent(day="mon", slot="midday", place="work", activity="working",
                               store_id="s1", step="purchase" if i == 0 else "price",
                               passed=i == 0, detail="Purchased" if i == 0 else "Price too high")]
              for i, a in enumerate(people)}
    run = FakeFunnelRun(shops, outcomes, traces,
                       FunnelCounts(total=3, exposed=3, noticed=3, needed=2, bought=1),
                       [ReasonStat(code=o.reason, label=o.reason.value, count=1, pct=100 / 3)
                        for o in outcomes],
                       [SegmentStat(dimension="borough", value="Tower Hamlets", total=30,
                                    interested=20, bought=10, conversion=1 / 3,
                                    top_reason=ReasonCode.TOO_EXPENSIVE)])
    monkeypatch.setattr(simulations, "run_funnel", lambda *args: run)
    with TestClient(app) as client:
        yield client


def test_population(api):
    assert api.get("/api/health").json() == {"status": "ok", "agents": 3, "stores": 1, "llm": False}
    points = api.get("/api/agents").json()
    assert len(points) == 3 and points[0]["lat"] == 51.51
    assert "traits" not in points[0]
    assert api.get("/api/agents/a0").json()["work_label"] == "Canary Wharf"
    assert api.get("/api/agents/missing").status_code == 404
    assert len(api.get("/api/stores?kind=convenience&borough=Tower%20Hamlets").json()) == 1
    assert api.get("/api/stores?kind=supermarket").json() == []
    summary = api.get("/api/population/summary").json()
    assert summary["total"] == 3 and summary["borough"] == {"Tower Hamlets": 3}


def test_simulation_and_cache(api):
    product = {"name": "Demo drink", "category": "soft_drink", "description": "A drink", "price_gbp": 2}
    response = api.post("/api/simulations", json=product)
    assert response.status_code == 202
    sim_id = response.json()["id"]
    assert len(sim_id) == 12
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = api.get(f"/api/simulations/{sim_id}").json()
        if result["status"] in {"done", "failed"}:
            break
        time.sleep(.01)
    assert result["status"] == "done", result
    assert result["report"]["source"] == "template"
    assert len(result["interviews"]) == 3
    assert all(i["source"] == "template" for i in result["interviews"])
    assert result["stores_stocking"] == 1 and len(result["outcomes"]) == 3
    assert api.get(f"/api/simulations/{sim_id}?include_outcomes=false").json()["outcomes"] == []
    assert len(api.get(f"/api/simulations/{sim_id}").json()["outcomes"]) == 3
    trace = api.get(f"/api/simulations/{sim_id}/agents/a0").json()
    assert trace["agent"]["id"] == "a0" and trace["trace"][0]["step"] == "purchase"
    assert trace["interview"]["source"] == "template"
    assert api.get(f"/api/simulations/{sim_id}/agents/missing").status_code == 404
    assert api.get("/api/simulations/missing").status_code == 404
    assert api.post("/api/simulations", json=product).json() == {"id": sim_id, "status": "done"}
    assert len(api.get("/api/simulations").json()) == 1
    # Exercise disk persistence rather than only the in-memory cache.
    store._simulations.clear()
    store._traces.clear()
    assert api.get(f"/api/simulations/{sim_id}/agents/a0").status_code == 200


def test_simulation_failure(api, monkeypatch):
    def fail(*args):
        raise RuntimeError("Demo engine failure")
    monkeypatch.setattr(simulations, "run_funnel", fail)
    response = api.post("/api/simulations", json={"name": "Fail", "category": "snack",
                                                "description": "Test", "price_gbp": 1})
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = api.get(f"/api/simulations/{response.json()['id']}").json()
        if result["status"] == "failed":
            break
        time.sleep(.01)
    assert result["status"] == "failed" and result["error"] == "Demo engine failure"


def test_import_without_engine():
    code = '''
import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "app.simulation.engine":
        raise ImportError("engine still being built")
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
import app.main
assert app.main.app.title == "HUMAN PORTAL Simulation API"
'''
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("responses, expected, call_count", [
    (["not JSON", '{"quote":"No thanks"}'], {"quote": "No thanks"}, 2),
    (["[]", "null"], None, 2),
    ([RuntimeError("API unavailable")], None, 1),
])
def test_llm_json_fallback(monkeypatch, responses, expected, call_count):
    from app.llm import client
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == "test-key"
            self.chat = SimpleNamespace(completions=self)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def create(self, **kwargs):
            calls.append(kwargs)
            value = responses[len(calls) - 1]
            if isinstance(value, Exception):
                raise value
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=value))])

    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(client, "AsyncOpenAI", FakeClient)
    assert asyncio.run(client.chat_json("system", "user")) == expected
    assert len(calls) == call_count
    assert calls[0]["response_format"] == {"type": "json_object"}


def test_llm_timeout(monkeypatch):
    from app.llm import client

    class SlowClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=self)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def create(self, **kwargs):
            await asyncio.sleep(1)

    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(config, "LLM_TIMEOUT_S", .01)
    monkeypatch.setattr(client, "AsyncOpenAI", SlowClient)
    assert asyncio.run(client.chat_json("system", "user")) is None
