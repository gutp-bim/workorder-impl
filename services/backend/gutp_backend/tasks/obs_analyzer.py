"""FUN-OBS-002/004/007 — 観測データ分析・評価 (from obs_analyzer)"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime

from gutp.events.subjects import OBS
from gutp.schemas.issue import IssueCreate, IssueStatus, IssueType
from gutp.schemas.observation import IoTEvent, Report

from .. import state

logger = logging.getLogger(__name__)

ESCALATION_THRESHOLD_SEC = int(os.getenv("ESCALATION_THRESHOLD_SEC", "1800"))
ESCALATION_CHECK_INTERVAL_SEC = int(os.getenv("ESCALATION_CHECK_INTERVAL_SEC", "60"))


async def handle_iot_event(event: IoTEvent) -> None:
    """IoTEvent を評価して Issue 生成が必要な場合は直接 state.issues に書き込む (FUN-OBS-002)."""
    if not (event.event_state and event.event_state.upper() == "ACTIVE"):
        return
    from gutp.schemas.issue import Issue
    record = Issue(
        issue_id=str(uuid.uuid4()),
        title=f"[自動] {event.iot_event_type} アラーム検知",
        issue_type=IssueType.FACILITY_ASSET,
        derived_from_id=event.iot_event_id,
        derived_from_type="IoTEvent",
        is_standard=False,
    )
    state.issues[record.issue_id] = record
    logger.info("issue created from IoTEvent: %s", record.issue_id)


async def handle_report_created(report: Report) -> None:
    """obs.report.created — Report を評価して高信頼度なら Issue を生成、pending キューに登録する (FUN-OBS-004/007)."""
    state.pending_reports[report.report_id] = (report, datetime.utcnow())
    logger.info("pending report registered: %s", report.report_id)

    if (report.report_confidence or 0) >= 70:
        from gutp.schemas.issue import Issue
        record = Issue(
            issue_id=str(uuid.uuid4()),
            title=f"[報告] {report.title}",
            issue_type=IssueType.FACILITY_ASSET,
            derived_from_id=report.report_id,
            derived_from_type="Report",
            description=report.report_comment,
            is_standard=False,
        )
        state.issues[record.issue_id] = record
        logger.info("issue created from Report: %s (confidence=%s)", record.issue_id, report.report_confidence)


async def handle_report_evaluated(report_id: str) -> None:
    """obs.report.evaluated — 評価済み Report を pending キューから除去する (FUN-OBS-007)."""
    if state.pending_reports.pop(report_id, None) is not None:
        logger.info("pending report cleared (evaluated): %s", report_id)
    for issue in state.issues.values():
        if issue.derived_from_id == report_id and issue.issue_status == IssueStatus.OPEN:
            issue.issue_status = IssueStatus.PENDING_REVIEW
            logger.info("Issue %s → PENDING_REVIEW (report=%s)", issue.issue_id, report_id)


async def escalation_loop() -> None:
    """閾値超過の未評価 Report を検出して通知する (FUN-OBS-007)."""
    from .notify import dispatch
    while True:
        await asyncio.sleep(ESCALATION_CHECK_INTERVAL_SEC)
        try:
            now = datetime.utcnow()
            to_escalate = [
                (rid, report)
                for rid, (report, received_at) in list(state.pending_reports.items())
                if (now - received_at).total_seconds() >= ESCALATION_THRESHOLD_SEC
            ]
            for rid, report in to_escalate:
                await dispatch(OBS.REPORT_ESCALATION, report.model_dump_json().encode())
                state.pending_reports.pop(rid, None)
                logger.info("escalated report: %s", rid)
        except Exception:
            logger.exception("escalation scan 失敗")
