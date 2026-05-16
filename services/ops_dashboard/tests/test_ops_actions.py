"""FUN-OPS-003: POST /ops/actions のテスト。"""

from __future__ import annotations

import httpx
import respx


@respx.mock
async def test_action_resolve_issue(ac):
    respx.patch("http://issue-manager:8000/issues/i-001/resolve").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    resp = await ac.post("/ops/actions", json={
        "targetType": "issue",
        "targetId": "i-001",
        "action": "resolve",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted"] is True
    assert "issue-manager" in data["forwardedTo"]
    assert "i-001" in data["forwardedTo"]


async def test_action_unknown_target(ac):
    resp = await ac.post("/ops/actions", json={
        "targetType": "unknown",
        "targetId": "x",
        "action": "foo",
    })
    assert resp.status_code == 400
