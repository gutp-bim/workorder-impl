"""
CS-NOTIFY-DISPATCHER — 通知ディスパッチャー (FUN-NOTIFY-001)

購読: IF-WO-002    wo.assigned / wo.emergency.completed（CS-WO-MANAGER）
      IF-NOTIFY-001 obs.report.escalation（CS-OBS-ANALYZER）
提供: IF-NOTIFY-002 GET /deliveries（配信履歴 ADR-003）
      NOTIFY_ADAPTER（email|slack|webhook）で配信チャネルを切り替え。
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
import nats
from fastapi import FastAPI
from gutp.events.subjects import OBS, WO

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
NOTIFY_ADAPTER = os.getenv("NOTIFY_ADAPTER", "email")
_QUEUE_GROUP = "notify-dispatcher"

_nc: nats.aio.client.Client | None = None
_delivery_log: list[dict] = []


async def _call_adapter(adapter: str, topic: str, payload: bytes) -> None:
    """アダプタごとの送信処理。失敗時は Exception を raise（リトライトリガー）。"""
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
    else:  # email: SMTP 未設定時はログのみ（graceful stub）
        logger.info("notify-dispatcher[email] <- %s: %r", topic, payload[:120])


async def dispatch(topic: str, payload: bytes) -> None:
    """FUN-NOTIFY-001 — 指数バックオフ最大3回リトライで配信し履歴を記録する。"""
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
                await asyncio.sleep(2 ** (attempt - 1))  # 1s → 2s

    _delivery_log.append({
        "delivery_id": str(uuid.uuid4()),
        "topic": topic,
        "adapter": adapter,
        "status": status,
        "attempt": attempt,
        "timestamp": datetime.utcnow().isoformat(),
    })


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _nc
    _nc = await nats.connect(NATS_URL)

    async def on_event(msg: nats.aio.msg.Msg) -> None:
        await dispatch(msg.subject, msg.data)

    await _nc.subscribe(WO.ASSIGNED, queue=_QUEUE_GROUP, cb=on_event)
    await _nc.subscribe(WO.EMERGENCY_COMPLETED, queue=_QUEUE_GROUP, cb=on_event)
    await _nc.subscribe(OBS.REPORT_ESCALATION, queue=_QUEUE_GROUP, cb=on_event)
    logger.info("notify-dispatcher ready (adapter=%s)", NOTIFY_ADAPTER)
    yield
    await _nc.drain()


app = FastAPI(title="notify-dispatcher", lifespan=lifespan)


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/deliveries")
async def list_deliveries() -> list[dict]:
    return _delivery_log
