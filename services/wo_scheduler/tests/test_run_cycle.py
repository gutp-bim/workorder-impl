from datetime import datetime

import gutp_wo_scheduler.main as m
import httpx
import pytest
import respx
from gutp_wo_scheduler.main import ScheduleDef, run_cycle

PAST = datetime(2024, 1, 1)
FUTURE = datetime(2099, 1, 1)

_ISSUE_URL = "http://issue-manager:8000/issues"
_TICKET_URL = "http://ticket-manager:8000/tickets"
_ESTIMATE_URL = "http://ticket-manager:8000/estimates"
_APPROVE_URL = "http://ticket-manager:8000/estimates/est-001/approve"


@pytest.mark.anyio
@respx.mock
async def test_run_cycle_triggers_due_schedule():
    sched = ScheduleDef(
        schedule_id="s-001",
        title="テスト",
        interval_days=30,
        issue_type="FacilityAsset",
        next_trigger_at=PAST,
    )
    m._schedules["s-001"] = sched

    respx.post(_ISSUE_URL).mock(return_value=httpx.Response(201, json={"issue_id": "i-001"}))
    respx.post(_TICKET_URL).mock(return_value=httpx.Response(201, json={"ticket_id": "t-001"}))
    respx.post(_ESTIMATE_URL).mock(
        return_value=httpx.Response(201, json={"estimate_id": "est-001"})
    )
    respx.patch(_APPROVE_URL).mock(return_value=httpx.Response(200, json={"ok": True}))

    async with httpx.AsyncClient() as client:
        await run_cycle(client)

    assert sched.last_triggered_at is not None
    assert sched.next_trigger_at > PAST


@pytest.mark.anyio
@respx.mock
async def test_run_cycle_skips_future_schedule():
    sched = ScheduleDef(
        schedule_id="s-002",
        title="未来",
        interval_days=30,
        issue_type="FacilityAsset",
        next_trigger_at=FUTURE,
    )
    m._schedules["s-002"] = sched

    async with httpx.AsyncClient() as client:
        await run_cycle(client)

    assert sched.last_triggered_at is None


@pytest.mark.anyio
@respx.mock
async def test_run_cycle_issue_failure_stops_chain():
    sched = ScheduleDef(
        schedule_id="s-003",
        title="失敗テスト",
        interval_days=7,
        issue_type="Operations",
        next_trigger_at=PAST,
    )
    m._schedules["s-003"] = sched
    respx.post(_ISSUE_URL).mock(return_value=httpx.Response(500))

    async with httpx.AsyncClient() as client:
        await run_cycle(client)

    assert sched.last_triggered_at is None
