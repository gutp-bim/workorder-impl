"""E2E: IoTEvent → Issue → Ticket → Estimate → approve → WO メインフロー。

前提: docker compose up で全サービスが起動済みであること。
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

import httpx
import pytest

ISSUE_MANAGER_URL = os.getenv("ISSUE_MANAGER_URL", "http://localhost:8002")
OBS_COLLECTOR_URL = os.getenv("OBS_COLLECTOR_URL", "http://localhost:8001")
TICKET_MANAGER_URL = os.getenv("TICKET_MANAGER_URL", "http://localhost:8003")
WO_MANAGER_URL = os.getenv("WO_MANAGER_URL", "http://localhost:8004")

_POLL_INTERVAL = 0.5
_POLL_TIMEOUT = 15.0


async def _poll_new_issue(http: httpx.AsyncClient, before_count: int) -> dict:
    """issue-manager に before_count より多い Issue が現れるまでポーリングする。"""
    deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT
    while asyncio.get_event_loop().time() < deadline:
        resp = await http.get(f"{ISSUE_MANAGER_URL}/issues")
        issues = resp.json()
        if len(issues) > before_count:
            return issues[-1]
        await asyncio.sleep(_POLL_INTERVAL)
    raise TimeoutError("Timed out waiting for new issue to appear in issue-manager")


@pytest.mark.anyio
async def test_iot_event_to_work_order(http: httpx.AsyncClient):
    """IoT イベント投入から WO 生成までのフルチェーンを検証する。"""
    # 事前の Issue 件数を記録
    before = (await http.get(f"{ISSUE_MANAGER_URL}/issues")).json()
    before_count = len(before)

    # 1. IoT イベントを obs-collector へ投入
    iot_resp = await http.post(
        f"{OBS_COLLECTOR_URL}/ingest/iot-event",
        json={
            "iot_event_type": "gutp:SmokeAlarm",
            "event_state": "ACTIVE",
            "source_id": "sensor-e2e-001",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert iot_resp.status_code == 202, f"obs-collector returned {iot_resp.status_code}"

    # 2. obs-analyzer が Issue を生成するのを待つ
    issue = await _poll_new_issue(http, before_count)
    issue_id = issue["issue_id"]
    assert issue["issue_status"] == "Open"

    # 3. Ticket 作成
    ticket_resp = await http.post(
        f"{TICKET_MANAGER_URL}/tickets",
        json={"title": "E2E テスト修理チケット", "addresses_issue_ids": [issue_id]},
    )
    assert ticket_resp.status_code == 201
    ticket_id = ticket_resp.json()["ticket_id"]

    # 4. Estimate 作成
    est_resp = await http.post(
        f"{TICKET_MANAGER_URL}/estimates",
        json={
            "ticket_id": ticket_id,
            "title": "E2E テスト見積",
            "estimated_cost": "10000",
            "estimated_duration": "P1D",
        },
    )
    assert est_resp.status_code == 201
    estimate_id = est_resp.json()["estimate_id"]

    # 5. Estimate 承認（→ wo-manager が WO を自動生成）
    approve_resp = await http.patch(f"{TICKET_MANAGER_URL}/estimates/{estimate_id}/approve")
    assert approve_resp.status_code == 200

    # 6. WO が生成されるまでポーリング
    deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT
    wo = None
    while asyncio.get_event_loop().time() < deadline:
        wos = (await http.get(f"{WO_MANAGER_URL}/work-orders")).json()
        matched = [w for w in wos if w.get("ticket_id") == ticket_id]
        if matched:
            wo = matched[0]
            break
        await asyncio.sleep(_POLL_INTERVAL)

    assert wo is not None, "WO が wo-manager に生成されませんでした"
    assert wo["work_order_status"] in ("Open", "InProgress")
