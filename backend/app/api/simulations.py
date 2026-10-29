import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app import store
from app.llm.chat import chat_with_agent
from app.llm.interviews import run_interviews
from app.llm.report import build_report
from app.schemas import (
    DAYS, SLOTS, AgentTrace, ChatReply, ChatRequest, Playback, PlaybackAgent, PlaybackStore, ProductInput,
    SimulationResult, SimulationSummary,
)

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)
_tasks: set[asyncio.Task] = set()


def run_funnel(product, agents, stores):
    from app.simulation.engine import run_funnel as engine_run
    return engine_run(product, agents, stores)


def _cache_key(product: ProductInput) -> str:
    return hashlib.sha256(product.model_dump_json().encode()).hexdigest()


async def _execute(result: SimulationResult):
    try:
        result.status = "running"
        result.progress = "Simulating 2,000 Londoners' week"
        store.save_simulation(result)
        agents, stores = store.load_agents(), store.load_stores()
        run = await asyncio.to_thread(run_funnel, result.product, agents, stores)
        result.stores_stocking = len(run.stores_stocking)
        result.funnel, result.reasons, result.segments = run.funnel, run.reasons, run.segments
        result.outcomes = run.outcomes
        store.save_traces(result.id, {aid: [e.model_dump(mode="json") for e in events]
                                     for aid, events in run.traces.items()})
        store.save_simulation(result)
        result.progress = "Interviewing agents"
        store.save_simulation(result)
        result.interviews = await run_interviews(result.product, run, {a.id: a for a in agents},
                                                  seed=result.product.seed)
        result.progress = "Writing report"
        store.save_simulation(result)
        result.report = await build_report(result.product, run, result.interviews)
        result.status, result.progress = "done", "Complete"
        store.save_simulation(result)
    except Exception as exc:
        logger.exception("Simulation %s failed", result.id)
        result.status, result.error, result.progress = "failed", str(exc), "Failed"
        store.save_simulation(result)


@router.post("/simulations", status_code=202)
async def create_simulation(product: ProductInput):
    key = _cache_key(product)
    for summary in store.list_simulations():
        if summary.status == "done":
            cached = store.get_simulation(summary.id)
            if cached is not None and _cache_key(cached.product) == key:
                return {"id": cached.id, "status": "done"}
    result = SimulationResult(id=uuid4().hex[:12], status="queued",
                              created_at=datetime.now(timezone.utc), product=product)
    store.save_simulation(result)
    task = asyncio.create_task(_execute(result))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return {"id": result.id, "status": "queued"}


@router.get("/simulations", response_model=list[SimulationSummary])
def simulations():
    return store.list_simulations()


@router.get("/simulations/{sim_id}", response_model=SimulationResult)
def simulation(sim_id: str, include_outcomes: bool = True):
    result = store.get_simulation(sim_id)
    if result is None:
        raise HTTPException(404, "Simulation not found")
    if not include_outcomes:
        return result.model_copy(update={"outcomes": []})
    return result


def _playback_kind(step: str, passed: bool) -> str | None:
    if passed:
        return {"exposure": "seen", "notice": "noticed", "purchase": "bought"}.get(step)
    if step in ("price", "belief", "loyalty"):
        return "rejected"
    return "missed" if step == "need" else None


@router.get("/simulations/{sim_id}/playback", response_model=Playback)
def playback(sim_id: str):
    from app.simulation.funnel import select_stocking_stores

    result = store.get_simulation(sim_id)
    if result is None or not result.outcomes:
        raise HTTPException(404, "Simulation not found or not finished")
    by_id = store.agents_by_id()
    traces = store.get_traces(sim_id)
    agents, events = [], []
    for o in result.outcomes:
        agent = by_id.get(o.agent_id)
        if agent is None:
            continue
        idx = len(agents)
        agents.append(PlaybackAgent(
            id=agent.id, name=agent.name, archetype=agent.archetype, outcome=o.outcome,
            **{dt: [(round(e.location.lat, 5), round(e.location.lon, 5)) for e in agent.schedule.get(dt, [])]
               for dt in ("weekday", "weekend")}))
        for ev in traces.get(agent.id, []):
            kind = _playback_kind(ev["step"], ev["passed"])
            if kind:
                events.append((idx, DAYS.index(ev["day"]) * len(SLOTS) + SLOTS.index(ev["slot"]), kind))
    stocking = select_stocking_stores(result.product, store.load_stores())
    return Playback(
        days=DAYS, slots=SLOTS, agents=agents, events=sorted(events, key=lambda e: e[1]),
        stores=[PlaybackStore(id=s.id, name=s.brand or s.name, lat=s.lat, lon=s.lon) for s in stocking])


@router.get("/simulations/{sim_id}/agents/{agent_id}", response_model=AgentTrace)
def agent_trace(sim_id: str, agent_id: str):
    trace = store.get_agent_trace(sim_id, agent_id)
    if trace is None:
        raise HTTPException(404, "Agent trace not found")
    return trace


@router.post("/simulations/{sim_id}/agents/{agent_id}/chat", response_model=ChatReply)
async def agent_chat(sim_id: str, agent_id: str, body: ChatRequest):
    trace = store.get_agent_trace(sim_id, agent_id)
    if trace is None:
        raise HTTPException(404, "Agent trace not found")
    if body.messages[-1].role != "retailer":
        raise HTTPException(422, "The last message must be the retailer's question")
    return await chat_with_agent(store.get_simulation(sim_id).product, trace, body.messages)
