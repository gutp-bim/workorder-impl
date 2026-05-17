"""Slice 2: Booking Conflict 検出 + confirm エンドポイントのテスト。"""

from __future__ import annotations

WO_BODY = {
    "ticket_id": "t-001",
    "title": "空調修理",
    "work_order_type": "CorrectiveMaintenance",
    "tasks": [],
}

BOOKING_BASE = {
    "assigned_to": "worker-1",
    "scheduled_start": "2024-06-01T09:00:00",
    "scheduled_end": "2024-06-01T17:00:00",
}


async def _make_wo(ac) -> str:
    resp = await ac.post("/work-orders", json=WO_BODY)
    return resp.json()["work_order_id"]


# ── Conflict 検出 ─────────────────────────────────────────────────────────────

async def test_booking_conflict_same_wo(ac):
    """同一 WO で時間帯が重複する2件目の Booking は 409 を返す。"""
    wo_id = await _make_wo(ac)
    first = await ac.post("/bookings", json={**BOOKING_BASE, "work_order_id": wo_id})
    assert first.status_code == 201

    overlapping = {**BOOKING_BASE, "work_order_id": wo_id,
                   "scheduled_start": "2024-06-01T12:00:00",
                   "scheduled_end": "2024-06-01T18:00:00"}
    second = await ac.post("/bookings", json=overlapping)
    assert second.status_code == 409


async def test_booking_no_conflict_different_times(ac):
    """同一 WO でも時間帯が重複しなければ両方 201 になる。"""
    wo_id = await _make_wo(ac)
    first = await ac.post("/bookings", json={**BOOKING_BASE, "work_order_id": wo_id})
    assert first.status_code == 201

    non_overlapping = {**BOOKING_BASE, "work_order_id": wo_id,
                       "scheduled_start": "2024-06-01T17:00:00",
                       "scheduled_end": "2024-06-01T20:00:00"}
    second = await ac.post("/bookings", json=non_overlapping)
    assert second.status_code == 201


async def test_booking_no_conflict_different_wo(ac):
    """異なる WO なら同一時間帯でも 409 にならない。"""
    wo_id_1 = await _make_wo(ac)
    wo_id_2 = await _make_wo(ac)

    first = await ac.post("/bookings", json={**BOOKING_BASE, "work_order_id": wo_id_1})
    assert first.status_code == 201

    second = await ac.post("/bookings", json={**BOOKING_BASE, "work_order_id": wo_id_2})
    assert second.status_code == 201


# ── confirm エンドポイント ────────────────────────────────────────────────────

async def test_confirm_booking_sets_wo_inprogress(ac):
    """Booking を confirm すると WO が IN_PROGRESS になり started_at が設定される。"""
    wo_id = await _make_wo(ac)
    booking_resp = await ac.post("/bookings", json={**BOOKING_BASE, "work_order_id": wo_id})
    booking_id = booking_resp.json()["booking_id"]

    confirm_resp = await ac.patch(f"/bookings/{booking_id}/confirm")
    assert confirm_resp.status_code == 200
    booking = confirm_resp.json()
    assert booking["booking_status"] == "Confirmed"

    wo_resp = await ac.get(f"/work-orders/{wo_id}")
    wo = wo_resp.json()
    assert wo["work_order_status"] == "InProgress"
    assert wo["started_at"] is not None


async def test_confirm_nonexistent_booking(ac):
    """存在しない Booking の confirm は 404 を返す。"""
    resp = await ac.patch("/bookings/nonexistent/confirm")
    assert resp.status_code == 404


async def test_confirm_booking_status_in_response(ac):
    """confirm 前は Tentative、confirm 後は Confirmed。"""
    wo_id = await _make_wo(ac)
    booking_resp = await ac.post("/bookings", json={**BOOKING_BASE, "work_order_id": wo_id})
    assert booking_resp.json()["booking_status"] == "Tentative"

    booking_id = booking_resp.json()["booking_id"]
    confirmed = await ac.patch(f"/bookings/{booking_id}/confirm")
    assert confirmed.json()["booking_status"] == "Confirmed"


def test_booking_status_conflicted_exists():
    """BookingStatus.CONFLICTED が schema に存在することを確認する。"""
    from gutp.schemas.workorder import BookingStatus

    assert BookingStatus.CONFLICTED == "Conflicted"
