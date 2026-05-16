"""GET /payments リストエンドポイントのテスト。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import gutp_payment_manager.main as m
from gutp.schemas.payment import Payment, PaymentStatus


async def test_list_payments_empty(ac):
    resp = await ac.get("/payments")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_payments(ac):
    p = Payment(
        payment_id="p-001",
        applies_to_work_order_id="wo-001",
        paid_to="agent-001",
        payment_amount=Decimal("1000"),
        currency="JPY",
        paid_at=datetime(2024, 1, 1),
        payment_status=PaymentStatus.PENDING,
    )
    m._payments["p-001"] = p
    resp = await ac.get("/payments")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["payment_id"] == "p-001"
