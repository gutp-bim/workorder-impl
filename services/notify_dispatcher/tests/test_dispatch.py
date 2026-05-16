"""FUN-NOTIFY-001: dispatch() アダプタ・リトライのユニットテスト。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import gutp_notify_dispatcher.main as m
import httpx
import respx


@respx.mock
async def test_dispatch_slack_success(monkeypatch):
    """SLACK_WEBHOOK_URL 設定・HTTP 200 → status='success', attempt=1。"""
    monkeypatch.setenv("NOTIFY_ADAPTER", "slack")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://hooks.slack.test/xxx")
    respx.post("http://hooks.slack.test/xxx").mock(return_value=httpx.Response(200))

    await m.dispatch("wo.assigned", b"{}")

    assert len(m._delivery_log) == 1
    record = m._delivery_log[0]
    assert record["status"] == "success"
    assert record["attempt"] == 1
    assert record["adapter"] == "slack"
    assert record["topic"] == "wo.assigned"


@respx.mock
async def test_dispatch_slack_http_error_retries(monkeypatch):
    """HTTP 500 → 最大3回試行 → status='error'、asyncio.sleep が2回呼ばれる。"""
    monkeypatch.setenv("NOTIFY_ADAPTER", "slack")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://hooks.slack.test/xxx")
    respx.post("http://hooks.slack.test/xxx").mock(return_value=httpx.Response(500))

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await m.dispatch("wo.assigned", b"{}")
        assert mock_sleep.await_count == 2  # 1s wait + 2s wait

    record = m._delivery_log[-1]
    assert record["status"] == "error"
    assert record["attempt"] == 3


@respx.mock
async def test_dispatch_slack_missing_url(monkeypatch):
    """SLACK_WEBHOOK_URL 未設定 → status='error'。"""
    monkeypatch.setenv("NOTIFY_ADAPTER", "slack")
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await m.dispatch("wo.assigned", b"{}")

    assert m._delivery_log[-1]["status"] == "error"


@respx.mock
async def test_dispatch_webhook_success(monkeypatch):
    """WEBHOOK_URL 設定・HTTP 200 → status='success'。"""
    monkeypatch.setenv("NOTIFY_ADAPTER", "webhook")
    monkeypatch.setenv("WEBHOOK_URL", "http://my.webhook.test/notify")
    respx.post("http://my.webhook.test/notify").mock(return_value=httpx.Response(200))

    await m.dispatch("wo.emergency.completed", b"{}")

    record = m._delivery_log[-1]
    assert record["status"] == "success"
    assert record["adapter"] == "webhook"


async def test_dispatch_email_stub(monkeypatch):
    """email adapter（SMTP 未設定）→ エラーなし・status='success'。"""
    monkeypatch.setenv("NOTIFY_ADAPTER", "email")
    monkeypatch.delenv("SMTP_HOST", raising=False)

    await m.dispatch("obs.report.escalation", b"{}")

    record = m._delivery_log[-1]
    assert record["status"] == "success"
    assert record["adapter"] == "email"


async def test_dispatch_records_delivery_log(monkeypatch):
    """dispatch 後 _delivery_log に必須フィールドが揃ったエントリが追加される。"""
    monkeypatch.setenv("NOTIFY_ADAPTER", "email")

    await m.dispatch("wo.assigned", b"{}")

    assert len(m._delivery_log) == 1
    record = m._delivery_log[0]
    for field in ("delivery_id", "topic", "adapter", "status", "attempt", "timestamp"):
        assert field in record
