"""FUN-NOTIFY-001 — 通知ディスパッチャー (from notify_dispatcher)"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

_delivery_log: list[dict] = []


async def _call_adapter(adapter: str, topic: str, payload: bytes) -> None:
    if adapter == "slack":
        url = os.getenv("SLACK_WEBHOOK_URL", "")
        if not url:
            raise RuntimeError("SLACK_WEBHOOK_URL not configured")
        async with httpx.AsyncClient() as client:
            r = await client.post(url, content=payload, headers={"Content-Type": "application/json"})
            r.raise_for_status()
    elif adapter == "webhook":
        url = os.getenv("WEBHOOK_URL", "")
        if not url:
            raise RuntimeError("WEBHOOK_URL not configured")
        async with httpx.AsyncClient() as client:
            r = await client.post(url, content=payload, headers={"Content-Type": "application/json"})
            r.raise_for_status()
    else:
        logger.info("notify[email] <- %s: %r", topic, payload[:120])


async def dispatch(topic: str, payload: bytes) -> None:
    """指数バックオフ最大3回リトライで配信し履歴を記録する。"""
    adapter = os.getenv("NOTIFY_ADAPTER", "email")
    status = "error"
    attempt = 0
    for attempt in range(1, 4):
        try:
            await _call_adapter(adapter, topic, payload)
            status = "success"
            break
        except Exception as exc:
            logger.warning("dispatch attempt %d/3 failed (%s): %s", attempt, topic, exc)
            if attempt < 3:
                await asyncio.sleep(2 ** (attempt - 1))

    _delivery_log.append({
        "delivery_id": str(uuid.uuid4()),
        "topic": topic,
        "adapter": adapter,
        "status": status,
        "attempt": attempt,
        "timestamp": datetime.utcnow().isoformat(),
    })


def get_delivery_log() -> list[dict]:
    return _delivery_log
