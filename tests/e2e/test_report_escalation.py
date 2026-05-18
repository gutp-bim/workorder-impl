"""E2E: Report 投入 → Issue 生成 → レビューフロー検証。

前提: docker compose up で全サービスが起動済みであること。
"""

from __future__ import annotations

import asyncio
import os

import httpx
import pytest

ISSUE_MANAGER_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
OBS_COLLECTOR_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

_POLL_INTERVAL = 0.5
_POLL_TIMEOUT = 15.0


@pytest.mark.anyio
async def test_report_creates_issue_and_review_flow(http: httpx.AsyncClient):
    """Report 投入後に Issue が生成され、レビュー遷移が動作することを検証する。"""
    before_count = len((await http.get(f"{ISSUE_MANAGER_URL}/issues")).json())

    # 1. Report を obs-collector へ投入
    report_resp = await http.post(
        f"{OBS_COLLECTOR_URL}/ingest/report",
        json={
            "title": "E2E テスト報告",
            "report_comment": "空調から異音がしている",
            "report_confidence": 80,
        },
    )
    assert report_resp.status_code == 202, f"obs-collector returned {report_resp.status_code}"

    # 2. Report に対応する Issue が生成されるまでポーリング
    deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT
    issue = None
    while asyncio.get_event_loop().time() < deadline:
        issues = (await http.get(f"{ISSUE_MANAGER_URL}/issues")).json()
        report_issues = [i for i in issues if i.get("derived_from_type") == "Report"]
        if len(report_issues) > 0 and len(issues) > before_count:
            issue = report_issues[-1]
            break
        await asyncio.sleep(_POLL_INTERVAL)

    assert issue is not None, "Report に対応する Issue が生成されませんでした"
    issue_id = issue["issue_id"]
    assert issue["issue_status"] in ("Open", "PendingReview")

    # 3. Issue が PendingReview でなければ obs.report.evaluated イベント到達を待つ
    if issue["issue_status"] == "Open":
        deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT
        while asyncio.get_event_loop().time() < deadline:
            current = (await http.get(f"{ISSUE_MANAGER_URL}/issues/{issue_id}")).json()
            if current["issue_status"] == "PendingReview":
                issue = current
                break
            await asyncio.sleep(_POLL_INTERVAL)

    # 4. レビュー承認（PendingReview → UnderReview）
    if issue["issue_status"] == "PendingReview":
        review_resp = await http.patch(
            f"{ISSUE_MANAGER_URL}/issues/{issue_id}/review",
            json={"action": "accept"},
        )
        assert review_resp.status_code == 200
        assert review_resp.json()["issue_status"] == "UnderReview"
