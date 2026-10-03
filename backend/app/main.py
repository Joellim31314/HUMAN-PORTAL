import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config, store
from app.api import areas, population, signals, simulations


@asynccontextmanager
async def lifespan(app: FastAPI):
    for loader in (store.load_agents, store.load_stores):
        try:
            loader()
        except Exception as exc:
            logging.getLogger(__name__).warning("Population data unavailable: %s", exc)
    yield
    # Drain active jobs during graceful shutdown so persisted runs finish.
    if simulations._tasks:
        import asyncio
        await asyncio.gather(*list(simulations._tasks), return_exceptions=True)


app = FastAPI(title="HUMAN PORTAL Simulation API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(population.router)
app.include_router(simulations.router)
app.include_router(signals.router)
app.include_router(areas.router)


@app.get("/")
def root():
    return {"docs": "/docs"}
