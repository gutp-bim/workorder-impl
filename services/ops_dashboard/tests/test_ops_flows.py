"""FUN-OPS-001: GET /ops/flows および GET /ops/problems のテスト。"""

from __future__ import annotations

import httpx
import respx

_ISSUE_URL = "http://backend:8000/issues"
_TICKET_URL = "http://backend:8000/tickets"
_WO_URL = "http://backend:8000/work-orders"
_PAY_URL = "http://backend:8000/payments"

_ISSUE = {
    "issue_id": "i-001",
    "issue_status": "Open",
    "issue_type": "FacilityAsset",
    "title": "空調故障",
    "derived_from_id": None,
    "derived_from_type": None,
    "is_standard": True,
    "description": None,
    "detected_at": "2024-01-01T00:00:00",
}

_TICKET = {
    "ticket_id": "t-001",
    "title": "空調修理チケット",
    "addresses_issue_ids": ["i-001"],
    "priority": 50,
    "due_at": None,
    "budget": None,
    "currency": "JPY",
    "description": None,
    "ticket_status": "Open",
    "estimated_cost": None,
    "actual_cost": None,
    "created_at": "2024-01-01T00:00:00",
}

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

_WO_COMPLETED = {**_WO, "work_order_status": "Completed"}

_PAYMENT = {
    "payment_id": "p-001",
    "applies_to_work_order_id": "wo-001",
    "paid_to": "agent-001",
    "payment_amount": "1000",
    "currency": "JPY",
    "paid_at": "2024-01-02T00:00:00",
    "payment_status": "Paid",
}


def _mock_all(issues=None, tickets=None, wos=None, payments=None):
    respx.get(_ISSUE_URL).mock(return_value=httpx.Response(200, json=issues or []))
    respx.get(_TICKET_URL).mock(return_value=httpx.Response(200, json=tickets or []))
    respx.get(_WO_URL).mock(return_value=httpx.Response(200, json=wos or []))
    respx.get(_PAY_URL).mock(return_value=httpx.Response(200, json=payments or []))


@respx.mock
async def test_list_flows_empty(ac):
    _mock_all()
    resp = await ac.get("/ops/flows")
    assert resp.status_code == 200
    assert resp.json()["flows"] == []


@respx.mock
async def test_list_flows_pending_review(ac):
    issue = {**_ISSUE, "issue_status": "PendingReview"}
    _mock_all(issues=[issue])
    resp = await ac.get("/ops/flows")
    assert resp.status_code == 200
    flows = resp.json()["flows"]
    assert len(flows) == 1
    assert "pending_review" in flows[0]["problem_flags"]


@respx.mock
async def test_list_flows_chain(ac):
    _mock_all(issues=[_ISSUE], tickets=[_TICKET], wos=[_WO])
    resp = await ac.get("/ops/flows")
    assert resp.status_code == 200
    flow = resp.json()["flows"][0]
    assert flow["flow_id"] == "i-001"
    assert flow["issue"]["issue_id"] == "i-001"
    assert len(flow["tickets"]) == 1
    assert flow["tickets"][0]["ticket_id"] == "t-001"
    assert len(flow["work_orders"]) == 1
    assert flow["work_orders"][0]["work_order_id"] == "wo-001"


@respx.mock
async def test_list_flows_unpaid(ac):
    _mock_all(issues=[_ISSUE], tickets=[_TICKET], wos=[_WO_COMPLETED])
    resp = await ac.get("/ops/flows")
    assert resp.status_code == 200
    flows = resp.json()["flows"]
    assert len(flows) == 1
    assert "unpaid" in flows[0]["problem_flags"]


@respx.mock
async def test_list_problems(ac):
    issue_ok = {**_ISSUE, "issue_id": "i-ok", "issue_status": "Open"}
    issue_prob = {**_ISSUE, "issue_id": "i-prob", "issue_status": "PendingReview"}
    _mock_all(issues=[issue_ok, issue_prob])
    resp = await ac.get("/ops/problems")
    assert resp.status_code == 200
    problems = resp.json()["problems"]
    assert len(problems) == 1
    assert problems[0]["flow_id"] == "i-prob"
