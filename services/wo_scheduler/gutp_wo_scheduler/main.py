"""
CS-WO-SCHEDULER — 予防保全スケジューラー (FUN-SCHEDULE-001, FUN-SCHEDULE-002)

SOI-WOM 所属（ADR-004）。定期バッチで予防保全スケジュールを評価し、
条件成立時に StandardIssue → 定型Ticket → Estimate → approve を自動発行する。
スケジュール CRUD（FUN-SCHEDULE-002 / IF-SCHEDULE-001）も担う。

依存: IF-ISSUE-001 (issue-manager), IF-TICKET-001 (ticket-manager)
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import FastAPI, HTTPException
from gutp.schemas.issue import IssueType
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

ISSUE_MANAGER_URL = os.getenv("ISSUE_MANAGER_URL", "http://issue-manager:8000")
TICKET_MANAGER_URL = os.getenv("TICKET_MANAGER_URL", "http://ticket-manager:8000")
SCHEDULE_INTERVAL_SEC = int(os.getenv("SCHEDULE_INTERVAL_SEC", "300"))

_schedules: dict[str, ScheduleDef] = {}


class ScheduleCreate(BaseModel):
    title: str
    interval_days: int = Field(gt=0)
    issue_type: IssueType
    next_trigger_at: datetime

    @field_validator("next_trigger_at")
    @classmethod
    def normalize_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class ScheduleDef(ScheduleCreate):
    schedule_id: str
    last_triggered_at: datetime | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cycle_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="CS-WO-SCHEDULER", version="0.1.0", lifespan=lifespan)


async def _cycle_loop() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            try:
                await run_cycle(client)
            except Exception as exc:
                logger.warning("_cycle_loop: run_cycle raised %s", exc)
            await asyncio.sleep(SCHEDULE_INTERVAL_SEC)


async def run_cycle(client: httpx.AsyncClient) -> None:
    """due なスケジュールを評価し Issue→Ticket→Estimate チェーンを発行する (FUN-SCHEDULE-001)。"""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    due = [s for s in _schedules.values() if s.next_trigger_at <= now]
    for sched in due:
        await _trigger_schedule(client, sched, now)


async def _trigger_schedule(
    client: httpx.AsyncClient, sched: ScheduleDef, now: datetime
) -> None:
    r = await client.post(
        f"{ISSUE_MANAGER_URL}/issues",
        json={
            "title": sched.title,
            "issue_type": sched.issue_type,
            "derived_from_id": None,
            "derived_from_type": None,
            "description": f"予防保全スケジュール '{sched.title}' による自動起票",
            "detected_at": now.isoformat(),
            "is_standard": True,
        },
    )
    if r.status_code != 201:
        logger.warning("_trigger_schedule: issue creation failed %d", r.status_code)
        return
    issue_id = r.json()["issue_id"]

    r = await client.post(
        f"{TICKET_MANAGER_URL}/tickets",
        json={"title": sched.title, "addresses_issue_ids": [issue_id]},
    )
    if r.status_code != 201:
        logger.warning("_trigger_schedule: ticket creation failed %d", r.status_code)
        return
    ticket_id = r.json()["ticket_id"]

    r = await client.post(
        f"{TICKET_MANAGER_URL}/estimates",
        json={
            "ticket_id": ticket_id,
            "title": sched.title,
            "estimated_cost": "0",
            "estimated_duration": "P1D",
        },
    )
    if r.status_code != 201:
        logger.warning("_trigger_schedule: estimate creation failed %d", r.status_code)
        return
    estimate_id = r.json()["estimate_id"]

    r = await client.patch(f"{TICKET_MANAGER_URL}/estimates/{estimate_id}/approve")
    if r.status_code != 200:
        logger.warning("_trigger_schedule: estimate approve failed %d", r.status_code)
        return

    sched.last_triggered_at = now
    sched.next_trigger_at = now + timedelta(days=sched.interval_days)
    logger.info("_trigger_schedule: schedule '%s' triggered", sched.schedule_id)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/schedules", status_code=201)
async def create_schedule(body: ScheduleCreate) -> ScheduleDef:
    sched = ScheduleDef(schedule_id=f"sched-{uuid.uuid4()}", **body.model_dump())
    _schedules[sched.schedule_id] = sched
    return sched


@app.get("/schedules")
async def list_schedules() -> list[ScheduleDef]:
    return list(_schedules.values())


@app.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str) -> None:
    if schedule_id not in _schedules:
        raise HTTPException(404, detail="Schedule not found")
    del _schedules[schedule_id]
