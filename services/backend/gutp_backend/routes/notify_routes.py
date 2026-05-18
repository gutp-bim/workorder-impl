"""IF-NOTIFY-002 — 配信履歴 (from notify_dispatcher)"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["notify"])


@router.get("/deliveries")
async def list_deliveries() -> list[dict]:
    from ..tasks.notify import get_delivery_log
    return get_delivery_log()
