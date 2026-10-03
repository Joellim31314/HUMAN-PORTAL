"""File-backed persistence: the built population plus cached simulation runs.

Postgres is the long-term plan (see PROJECT.md); for the demo, JSON files keep
setup at zero.
"""

from __future__ import annotations

import json
from functools import lru_cache

from app import config
from app.schemas import Agent, AgentTrace, SimulationResult, SimulationSummary, Store

_simulations: dict[str, SimulationResult] = {}
_traces: dict[str, dict[str, list[dict]]] = {}


@lru_cache(maxsize=1)
def load_agents() -> list[Agent]:
    if not config.AGENTS_PATH.exists():
        raise FileNotFoundError(
            f"{config.AGENTS_PATH} missing - run `python -m app.pipeline.build_population`"
        )
    return [Agent.model_validate(a) for a in json.loads(config.AGENTS_PATH.read_text("utf-8"))]


@lru_cache(maxsize=1)
def agents_by_id() -> dict[str, Agent]:
    return {a.id: a for a in load_agents()}


@lru_cache(maxsize=1)
def load_stores() -> list[Store]:
    if not config.STORES_PATH.exists():
        raise FileNotFoundError(
            f"{config.STORES_PATH} missing - run `python -m app.pipeline.build_population`"
        )
    return [Store.model_validate(s) for s in json.loads(config.STORES_PATH.read_text("utf-8"))]


def _sim_path(sim_id: str):
    return config.SIM_CACHE_DIR / f"{sim_id}.json"


def _trace_path(sim_id: str):
    return config.SIM_CACHE_DIR / f"{sim_id}.traces.json"


def save_simulation(result: SimulationResult) -> None:
    _simulations[result.id] = result
    config.SIM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _sim_path(result.id).write_text(result.model_dump_json(), "utf-8")


def get_simulation(sim_id: str) -> SimulationResult | None:
    if sim_id in _simulations:
        return _simulations[sim_id]
    path = _sim_path(sim_id)
    if path.exists():
        result = SimulationResult.model_validate_json(path.read_text("utf-8"))
        _simulations[sim_id] = result
        return result
    return None


def list_simulations() -> list[SimulationSummary]:
    if config.SIM_CACHE_DIR.exists():
        for path in config.SIM_CACHE_DIR.glob("*.json"):
            if not path.name.endswith(".traces.json"):
                get_simulation(path.stem)
    return sorted(
        (
            SimulationSummary(id=r.id, status=r.status, product_name=r.product.name, created_at=r.created_at)
            for r in _simulations.values()
        ),
        key=lambda s: s.created_at,
        reverse=True,
    )


def save_traces(sim_id: str, traces: dict[str, list[dict]]) -> None:
    """traces: agent_id -> list of TraceEvent dicts."""
    _traces[sim_id] = traces
    config.SIM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _trace_path(sim_id).write_text(json.dumps(traces), "utf-8")


def get_agent_trace(sim_id: str, agent_id: str) -> AgentTrace | None:
    result = get_simulation(sim_id)
    agent = agents_by_id().get(agent_id)
    if result is None or agent is None:
        return None
    if sim_id not in _traces and _trace_path(sim_id).exists():
        _traces[sim_id] = json.loads(_trace_path(sim_id).read_text("utf-8"))
    outcome = next((o for o in result.outcomes if o.agent_id == agent_id), None)
    if outcome is None:
        return None
    interview = next((i for i in result.interviews if i.agent_id == agent_id), None)
    return AgentTrace.model_validate(
        {
            "agent": agent,
            "outcome": outcome,
            "trace": _traces.get(sim_id, {}).get(agent_id, []),
            "interview": interview,
        }
    )
