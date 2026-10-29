"""Export the example product's simulations as static files for the hosted demo.

    python -m app.pipeline.export_demo

Runs the full pipeline (funnel, interviews, report) once per research area and
writes everything the frontend needs into frontend/public/demo/, so the
deployed site can replay real runs without this backend. Runs already in the
simulation cache are reused, so re-exporting costs no LLM calls.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from app import config, store
from app.api import simulations
from app.api.areas import score_areas
from app.api.population import agents as agent_points
from app.llm.prompts import persona_card
from app.schemas import ProductInput, SimulationResult

OUT_DIR = config.BACKEND_DIR.parent / "frontend" / "public" / "demo"
PRODUCT_PATH = config.DATA_DIR / "demo_product.json"

# Must match frontend AREA_BOROUGH (sim-api.ts).
AREAS = {
    "walthamstow": "Waltham Forest",
    "peckham": "Southwark",
    "camden": "Camden",
    "stratford": "Newham",
    "shoreditch": "Hackney",
    "clapham": "Lambeth",
    "kingston": "Kingston upon Thames",
}


def _write(name: str, value) -> None:
    path = OUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, separators=(",", ":"), ensure_ascii=False), "utf-8")
    print(f"  {name} ({path.stat().st_size // 1024} KB)")


async def _run(product: ProductInput) -> SimulationResult:
    key = simulations._cache_key(product)
    for summary in store.list_simulations():
        cached = store.get_simulation(summary.id) if summary.status == "done" else None
        if cached is not None and simulations._cache_key(cached.product) == key:
            return cached
    result = SimulationResult(id=uuid4().hex[:12], status="queued",
                              created_at=datetime.now(timezone.utc), product=product)
    store.save_simulation(result)
    await simulations._execute(result)
    if result.status != "done":
        raise RuntimeError(f"Simulation for {product.stockists.boroughs} failed: {result.error}")
    return result


def _agent_files(result: SimulationResult) -> dict:
    by_id = store.agents_by_id()
    traces = store.get_traces(result.id)
    interviews = {i.agent_id: i for i in result.interviews}
    out = {}
    for o in result.outcomes:
        a = by_id[o.agent_id]
        interview = interviews.get(a.id)
        out[a.id] = {
            "agent": {"id": a.id, "name": a.name, "age": a.age, "borough": a.borough,
                      "archetype": a.archetype, "occupation": a.occupation,
                      "work_label": a.work_label},
            "outcome": {"outcome": o.outcome.value, "reason": o.reason.value},
            "trace": traces.get(a.id, []),
            "interview": {"quote": interview.quote} if interview else None,
        }
    return out


async def main() -> None:
    base = ProductInput.model_validate_json(PRODUCT_PATH.read_text("utf-8"))
    print(f"Exporting '{base.name}' to {OUT_DIR}")
    for slug, borough in AREAS.items():
        product = base.model_copy(update={
            "stockists": base.stockists.model_copy(update={"boroughs": [borough]})})
        print(f"{slug} ({borough})")
        result = await _run(product)
        _write(f"sims/{slug}.json", result.model_dump(mode="json"))
        _write(f"sims/{slug}.playback.json", simulations.playback(result.id).model_dump(mode="json"))
        _write(f"sims/{slug}.agents.json", _agent_files(result))
    print("shared")
    _write("agents.json", [p.model_dump(mode="json") for p in agent_points()])
    _write("personas.json", {a.id: persona_card(a) for a in store.load_agents()})
    _write("areas.json", score_areas(base))
    _write("manifest.json", {"product": base.model_dump(mode="json"), "areas": list(AREAS),
                             "generated_at": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    asyncio.run(main())
