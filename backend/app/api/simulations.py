import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app import store
from app.llm.interviews import run_interviews
from app.llm.report import build_report
from app.schemas import AgentTrace, ProductInput, SimulationResult, SimulationSummary

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


@router.get("/simulations/{sim_id}/agents/{agent_id}", response_model=AgentTrace)
def agent_trace(sim_id: str, agent_id: str):
    trace = store.get_agent_trace(sim_id, agent_id)
    if trace is None:
        raise HTTPException(404, "Agent trace not found")
    return trace
