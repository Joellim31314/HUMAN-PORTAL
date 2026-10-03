"""Real area scoring: run the population funnel per London borough and rank
opportunity from actual simulated outcomes — no LLM, seconds per product.

This is the layer that makes the map honest: the same engine that powers
MISO scores every area with the user's real product inputs (category, price,
claims, audience) against the census population and store POIs.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import store
from app.api.simulations import run_funnel
from app.schemas import ProductInput

router = APIRouter(prefix="/api/areas", tags=["areas"])

# Must match frontend AREA_BOROUGH (sim-api.ts).
BOROUGHS = [
    "Waltham Forest",
    "Southwark",
    "Camden",
    "Newham",
    "Hackney",
    "Lambeth",
    "Kingston upon Thames",
]


@router.post("/score")
def score_areas(product: ProductInput):
    agents, stores = store.load_agents(), store.load_stores()
    runs = []
    for borough in BOROUGHS:
        scoped = product.model_copy(
            update={
                "stockists": product.stockists.model_copy(
                    update={"boroughs": [borough]}
                )
            }
        )
        run = run_funnel(scoped, agents, stores)
        f = run.funnel
        runs.append(
            {
                "borough": borough,
                "bought": f.bought,
                "exposed": f.exposed,
                "noticed": f.noticed,
                "needed": f.needed,
                "total": f.total,
                "stores_stocking": len(run.stores_stocking),
            }
        )
    best = max((r["bought"] for r in runs), default=0) or 1
    for r in runs:
        r["score"] = round(100 * r["bought"] / best)
    ranked = sorted(runs, key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
    return {"product": product.name, "areas": ranked}
