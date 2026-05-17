"""E2E: 予防保全スケジューラー — スケジュール登録 → サイクル評価 → Issue 生成。

前提:
  - docker compose up で全サービスが起動済みであること。
  - SCHEDULE_INTERVAL_SEC=5 で wo-scheduler が起動していること（e2e_test.sh が設定）。
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from tests.e2e.conftest import ISSUE_MANAGER_URL, WO_SCHEDULER_URL

_SCHEDULE_INTERVAL = int(os.getenv("SCHEDULE_INTERVAL_SEC", "300"))
_POLL_INTERVAL = 0.5
_POLL_TIMEOUT = _SCHEDULE_INTERVAL + 10.0


@pytest.mark.anyio
async def test_scheduler_creates_issue(http: httpx.AsyncClient):
    """過去 next_trigger_at のスケジュールが評価され Issue が生成されることを検証する。"""
    before_issues = (await http.get(f"{ISSUE_MANAGER_URL}/issues")).json()
    before_standard_count = sum(1 for i in before_issues if i.get("is_standard"))

    # 1. next_trigger_at を1時間前に設定してスケジュールを登録
    past_trigger = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    sched_resp = await http.post(
        f"{WO_SCHEDULER_URL}/schedules",
        json={
            "title": "E2E テスト: 空調フィルター交換",
            "interval_days": 90,
            "issue_type": "FacilityAsset",
            "next_trigger_at": past_trigger,
        },
    )
    assert sched_resp.status_code == 201
    sched = sched_resp.json()
    assert sched["schedule_id"].startswith("sched-")

    # 2. スケジュールサイクルが実行され Issue が生成されるまでポーリング
    deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT
    new_issue = None
    while asyncio.get_event_loop().time() < deadline:
        issues = (await http.get(f"{ISSUE_MANAGER_URL}/issues")).json()
        standard_issues = [i for i in issues if i.get("is_standard")]
        if len(standard_issues) > before_standard_count:
            new_issue = standard_issues[-1]
            break
        await asyncio.sleep(_POLL_INTERVAL)

    assert new_issue is not None, (
        f"予防保全スケジュールによる Issue が {_POLL_TIMEOUT}s 以内に生成されませんでした"
    )
    assert "E2E テスト" in new_issue["title"] or new_issue["is_standard"]

    # 3. スケジュールの last_triggered_at が更新されていることを確認
    schedules = (await http.get(f"{WO_SCHEDULER_URL}/schedules")).json()
    target = next((s for s in schedules if s["schedule_id"] == sched["schedule_id"]), None)
    assert target is not None
    assert target["last_triggered_at"] is not None, "last_triggered_at が更新されていません"
