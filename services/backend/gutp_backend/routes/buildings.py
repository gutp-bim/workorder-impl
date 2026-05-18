"""IF-BUILDING-002 — 建物構成レジストリ (from building_registry)"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from .. import state

router = APIRouter(tags=["buildings"])


@router.get("/topology/buildings")
async def list_buildings() -> list[dict]:
    return state.topology.get_all_buildings()


@router.get("/topology/buildings/{building_dt_id}/floors")
async def list_floors(building_dt_id: str) -> list[dict]:
    result = state.topology.get_floors(building_dt_id)
    if not result and not any(b["dt_id"] == building_dt_id for b in state.topology.get_all_buildings()):
        raise HTTPException(404, detail="Building not found")
    return result


@router.get("/topology/spaces")
async def list_spaces(building_dt_id: str | None = None) -> list[dict]:
    return state.topology.get_spaces(building_dt_id)


@router.get("/topology/devices")
async def list_devices(building_dt_id: str | None = None) -> list[dict]:
    return state.topology.get_devices(building_dt_id)


@router.post("/topology/sync", status_code=202)
async def trigger_sync() -> dict:
    from gutp.clients.building_os import BuildingOSClient

    async def _do():
        async with BuildingOSClient() as c:
            await state.topology.sync_once(c)

    asyncio.create_task(_do())
    return {"status": "sync triggered"}
