"""backend — 統合バックエンドサービス (nats + building_registry + obs + issue + ticket + wo + payment + notify)"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import nats
from fastapi import FastAPI

from . import state
from .routes import (
    buildings,
    issues,
    notify_routes,
    obs,
    payments,
    schedules,
    tickets,
    workorders,
)
from .tasks import obs_analyzer, wo_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # NATS（外部連携用。内部通信は直接関数呼び出し）
    try:
        state.nc = await asyncio.wait_for(
            nats.connect(NATS_URL, max_reconnect_attempts=1),
            timeout=5.0,
        )
        logger.info("NATS connected: %s", NATS_URL)
    except Exception:
        logger.warning("NATS unavailable, continuing without it")

    # ビルトポロジー初回同期
    from gutp.clients.building_os import BuildingOSClient
    try:
        async with BuildingOSClient() as c:
            await state.topology.sync_once(c)
    except Exception:
        logger.warning("Initial building sync failed — registry is empty")

    # バックグラウンドタスク起動
    async def _building_loop():
        from gutp.clients.building_os import BuildingOSClient
        async with BuildingOSClient() as c:
            await state.topology.run_sync_loop(c)

    t_building = asyncio.create_task(_building_loop())
    t_escalation = asyncio.create_task(obs_analyzer.escalation_loop())
    t_scheduler = asyncio.create_task(wo_scheduler.cycle_loop())

    yield

    for t in (t_building, t_escalation, t_scheduler):
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass

    if state.nc:
        await state.nc.drain()


app = FastAPI(title="backend", version="0.1.0", lifespan=lifespan)

for r in (buildings.router, obs.router, issues.router, tickets.router,
          workorders.router, payments.router, schedules.router, notify_routes.router):
    app.include_router(r)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
