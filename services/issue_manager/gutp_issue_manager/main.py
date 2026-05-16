"""
CS-ISSUE-MANAGER — Issue 管理サービス (FUN-ISSUE-001, FUN-ISSUE-002)

提供: IF-ISSUE-001 (REST CRUD), IF-ISSUE-002 (NATS issue.created / issue.resolved)
購読: IF-OBS-003 (NATS obs.report.evaluated) — Report 評価後に Issue を PENDING_REVIEW に遷移
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Literal

import nats
from fastapi import FastAPI, HTTPException
from gutp.events.subjects import ISSUE, OBS
from gutp.schemas.issue import Issue, IssueCreate, IssueStatus
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

_nc: nats.aio.client.Client | None = None
_issues: dict[str, Issue] = {}


class _ReportEvaluatedEvent(BaseModel):
    report_id: str


class ReviewBody(BaseModel):
    action: Literal["accept", "reject"]


async def _handle_report_evaluated(report_id: str) -> None:
    """obs.report.evaluated 受信時、該当 Issue を OPEN → PENDING_REVIEW に遷移させる。"""
    for issue in _issues.values():
        if issue.derived_from_id == report_id and issue.issue_status == IssueStatus.OPEN:
            issue.issue_status = IssueStatus.PENDING_REVIEW
            logger.info("Issue %s → PENDING_REVIEW (report=%s)", issue.issue_id, report_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _nc
    _nc = await nats.connect(NATS_URL)

    async def on_report_evaluated(msg: nats.aio.msg.Msg) -> None:
        try:
            event = _ReportEvaluatedEvent.model_validate_json(msg.data)
            await _handle_report_evaluated(event.report_id)
        except Exception:
            logger.exception("obs.report.evaluated の処理に失敗 (payload=%s)", msg.data[:200])

    await _nc.subscribe(OBS.REPORT_EVALUATED, cb=on_report_evaluated)
    yield
    await _nc.drain()


app = FastAPI(title="issue-manager", lifespan=lifespan)


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/issues", status_code=201)
async def create_issue(body: IssueCreate) -> Issue:
    record = Issue(issue_id=str(uuid.uuid4()), **body.model_dump())
    _issues[record.issue_id] = record
    if _nc:
        await _nc.publish(ISSUE.CREATED, record.model_dump_json().encode())
    return record


@app.get("/issues/{issue_id}")
async def get_issue(issue_id: str) -> Issue:
    record = _issues.get(issue_id)
    if not record:
        raise HTTPException(404, detail="Issue not found")
    return record


@app.get("/issues")
async def list_issues() -> list[Issue]:
    return list(_issues.values())


@app.patch("/issues/{issue_id}/review")
async def review_issue(issue_id: str, body: ReviewBody) -> Issue:
    record = _issues.get(issue_id)
    if not record:
        raise HTTPException(404, detail="Issue not found")
    if record.issue_status == IssueStatus.RESOLVED:
        raise HTTPException(409, detail="Cannot review a Resolved issue")
    if body.action == "accept":
        record.issue_status = IssueStatus.UNDER_REVIEW
    else:
        record.issue_status = IssueStatus.OPEN
    return record


@app.patch("/issues/{issue_id}/resolve")
async def resolve_issue(issue_id: str) -> Issue:
    record = _issues.get(issue_id)
    if not record:
        raise HTTPException(404, detail="Issue not found")
    if record.issue_status == IssueStatus.RESOLVED:
        return record
    record.issue_status = IssueStatus.RESOLVED
    if _nc:
        await _nc.publish(ISSUE.RESOLVED, record.model_dump_json().encode())
    return record
