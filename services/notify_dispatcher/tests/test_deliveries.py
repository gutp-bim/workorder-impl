"""GET /deliveries エンドポイントのユニットテスト。"""

from __future__ import annotations

import gutp_notify_dispatcher.main as m


async def test_get_deliveries_empty(ac):
    """配信履歴なし → GET /deliveries → 200, []。"""
    resp = await ac.get("/deliveries")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_deliveries_after_dispatch(ac, monkeypatch):
    """dispatch 後 GET /deliveries → エントリ1件。"""
    monkeypatch.setenv("NOTIFY_ADAPTER", "email")
    await m.dispatch("wo.assigned", b"{}")

    resp = await ac.get("/deliveries")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["topic"] == "wo.assigned"
    assert data[0]["status"] == "success"
