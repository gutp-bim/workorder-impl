"""GET /ops/work-orders および POST /ops/work-orders/{wo_id}/tasks のテスト。"""

from __future__ import annotations

import httpx
import respx

_WO_LIST_URL = "http://wo-manager:8000/work-orders"
_WO_TASK_URL = "http://wo-manager:8000/work-orders/wo-001/tasks"

_WO = {
    "work_order_id": "wo-001",
    "ticket_id": "t-001",
    "title": "空調修理WO",
    "work_order_type": "CorrectiveMaintenance",
    "work_order_status": "Open",
    "description": None,
    "task_ids": [],
    "started_at": None,
    "done_at": None,
}

_TASK_BODY = {"title": "現場確認", "description": None}


@respx.mock
async def test_list_work_orders_ok(ac):
    respx.get(_WO_LIST_URL).mock(return_value=httpx.Response(200, json=[_WO]))
    resp = await ac.get("/ops/work-orders")
    assert resp.status_code == 200
    assert resp.json() == [_WO]


@respx.mock
async def test_list_work_orders_upstream_error(ac):
    respx.get(_WO_LIST_URL).mock(return_value=httpx.Response(503, text="Service Unavailable"))
    resp = await ac.get("/ops/work-orders")
    assert resp.status_code == 503
    assert "Service Unavailable" in resp.json()["detail"]


@respx.mock
async def test_list_work_orders_connection_error(ac):
    respx.get(_WO_LIST_URL).mock(side_effect=httpx.ConnectError("connection refused"))
    resp = await ac.get("/ops/work-orders")
    assert resp.status_code == 502
    assert "wo-manager" in resp.json()["detail"]


@respx.mock
async def test_add_task_ok(ac):
    wo_with_task = {**_WO, "task_ids": ["task-abc"]}
    respx.post(_WO_TASK_URL).mock(return_value=httpx.Response(201, json=wo_with_task))
    resp = await ac.post("/ops/work-orders/wo-001/tasks", json=_TASK_BODY)
    assert resp.status_code == 201
    assert resp.json()["task_ids"] == ["task-abc"]


@respx.mock
async def test_add_task_upstream_404(ac):
    respx.post(_WO_TASK_URL).mock(return_value=httpx.Response(404, text="WorkOrder not found"))
    resp = await ac.post("/ops/work-orders/wo-001/tasks", json=_TASK_BODY)
    assert resp.status_code == 404
    assert "WorkOrder not found" in resp.json()["detail"]


@respx.mock
async def test_add_task_connection_error(ac):
    respx.post(_WO_TASK_URL).mock(side_effect=httpx.ConnectError("connection refused"))
    resp = await ac.post("/ops/work-orders/wo-001/tasks", json=_TASK_BODY)
    assert resp.status_code == 502
    assert "wo-manager" in resp.json()["detail"]
