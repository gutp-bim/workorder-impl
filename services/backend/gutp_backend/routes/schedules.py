"""IF-SCHEDULE-001 — 予防保全スケジュール (from wo_scheduler)"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from gutp.schemas.issue import IssueType
from pydantic import BaseModel, Field, field_validator

from .. import state

router = APIRouter(tags=["schedules"])


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


@router.post("/schedules", status_code=201)
async def create_schedule(body: ScheduleCreate) -> ScheduleDef:
    sched = ScheduleDef(schedule_id=f"sched-{uuid.uuid4()}", **body.model_dump())
    state.schedules[sched.schedule_id] = sched
    return sched


@router.get("/schedules")
async def list_schedules() -> list[ScheduleDef]:
    return list(state.schedules.values())


@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str) -> None:
    if schedule_id not in state.schedules:
        raise HTTPException(404, detail="Schedule not found")
    del state.schedules[schedule_id]
