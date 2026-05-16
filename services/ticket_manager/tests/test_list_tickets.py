"""GET /tickets リストエンドポイントのテスト。"""

from __future__ import annotations


async def test_list_tickets_empty(ac):
    resp = await ac.get("/tickets")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_tickets(ac):
    await ac.post("/tickets", json={"title": "テスト", "addresses_issue_ids": ["i-001"]})
    resp = await ac.get("/tickets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "テスト"
