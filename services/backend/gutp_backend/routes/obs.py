"""IF-OBS-001/002/003 — 観測データ収集 (from obs_collector)"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from gutp.connectors.rest.router import make_rest_router
from gutp.connectors.base import IngressEvent
from gutp.schemas.observation import IoTEvent, IoTEventCreate, Report, ReportCreate

from .. import state

router = APIRouter(tags=["obs"])


async def handle_ingress(event: IngressEvent) -> None:
    if event.event_type == "IoTEvent":
        body = IoTEventCreate(**event.payload)
        record = IoTEvent(
            iot_event_id=str(uuid.uuid4()),
            received_at=datetime.utcnow(),
            **body.model_dump(),
        )
        state.iot_events[record.iot_event_id] = record
        from ..tasks.obs_analyzer import handle_iot_event
        await handle_iot_event(record)

    elif event.event_type == "Report":
        body = ReportCreate(**event.payload)
        record = Report(
            report_id=str(uuid.uuid4()),
            received_at=datetime.utcnow(),
            **body.model_dump(),
        )
        state.reports[record.report_id] = record
        from ..tasks.obs_analyzer import handle_report_created
        await handle_report_created(record)


router.include_router(make_rest_router(on_event=handle_ingress))


@router.get("/iot-events/{iot_event_id}")
async def get_iot_event(iot_event_id: str) -> IoTEvent:
    record = state.iot_events.get(iot_event_id)
    if not record:
        raise HTTPException(404, detail="IoTEvent not found")
    return record


@router.get("/reports/{report_id}")
async def get_report(report_id: str) -> Report:
    record = state.reports.get(report_id)
    if not record:
        raise HTTPException(404, detail="Report not found")
    return record


@router.post("/reports/{report_id}/evaluate", status_code=204)
async def evaluate_report(report_id: str) -> None:
    """obs.report.evaluated — 評価済みとしてマークし pending キューから除去する (FUN-OBS-007)."""
    from ..tasks.obs_analyzer import handle_report_evaluated
    await handle_report_evaluated(report_id)
