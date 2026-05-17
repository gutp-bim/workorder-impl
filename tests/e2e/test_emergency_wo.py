"""E2E: 緊急 WO フロー — POST /work-orders/emergency → complete-emergency。

前提: docker compose up で全サービスが起動済みであること。
"""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.conftest import WO_MANAGER_URL


@pytest.mark.anyio
async def test_emergency_wo_flow(http: httpx.AsyncClient):
    """緊急 WO を発行し、完了まで一連の状態遷移を検証する。"""
    # 1. 緊急 WO を発行（即 InProgress になる）
    create_resp = await http.post(
        f"{WO_MANAGER_URL}/work-orders/emergency",
        json={
            "reason": "E2E テスト: 設備緊急停止",
            "tasks": [{"title": "緊急点検"}],
        },
    )
    assert create_resp.status_code == 201
    wo = create_resp.json()
    wo_id = wo["work_order_id"]
    assert wo["work_order_status"] == "InProgress", f"Expected InProgress, got {wo['work_order_status']}"
    assert wo["work_order_type"] == "EmergencyMaintenance"
    assert wo["started_at"] is not None

    # 2. 緊急 WO 完了
    complete_resp = await http.patch(f"{WO_MANAGER_URL}/work-orders/{wo_id}/complete-emergency")
    assert complete_resp.status_code == 200
    completed_wo = complete_resp.json()
    assert completed_wo["work_order_status"] == "Completed"
    assert completed_wo["done_at"] is not None
