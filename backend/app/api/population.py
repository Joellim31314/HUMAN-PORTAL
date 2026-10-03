from collections import Counter

from fastapi import APIRouter, HTTPException

from app import store
from app.llm.client import llm_available
from app.schemas import Agent, AgentPoint, Store

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    def count(loader):
        try:
            return len(loader())
        except FileNotFoundError:
            return 0
    return {"status": "ok", "agents": count(store.load_agents),
            "stores": count(store.load_stores), "llm": llm_available()}


@router.get("/agents", response_model=list[AgentPoint])
def agents():
    return [AgentPoint(id=a.id, lat=a.home.lat, lon=a.home.lon, borough=a.borough,
                       age_band=a.age_band, sex=a.sex, ethnicity=a.ethnicity,
                       archetype=a.archetype, income_band=a.income_band)
            for a in store.load_agents()]


@router.get("/agents/{agent_id}", response_model=Agent)
def agent(agent_id: str):
    value = store.agents_by_id().get(agent_id)
    if value is None:
        raise HTTPException(404, "Agent not found")
    return value


@router.get("/stores", response_model=list[Store])
def stores(kind: str | None = None, borough: str | None = None):
    return [s for s in store.load_stores()
            if (kind is None or s.kind == kind) and (borough is None or s.borough == borough)]


@router.get("/population/summary")
def summary():
    population = store.load_agents()
    return {"total": len(population), **{
        field: dict(Counter(getattr(a, field) for a in population))
        for field in ("borough", "age_band", "sex", "ethnicity", "archetype", "income_band")}}
