"""IF-PAYMENT-001 — 支払い管理 (from payment_manager)"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from gutp.schemas.payment import Payment, PaymentCreate, PaymentStatus

from .. import state

router = APIRouter(tags=["payments"])


@router.post("/payments", status_code=201)
async def create_payment(body: PaymentCreate) -> Payment:
    if body.applies_to_work_order_id not in state.work_orders:
        raise HTTPException(404, detail="WorkOrder not found")
    record = Payment(payment_id=str(uuid.uuid4()), **body.model_dump())
    state.payments[record.payment_id] = record
    return record


@router.get("/payments")
async def list_payments() -> list[Payment]:
    return list(state.payments.values())


@router.get("/payments/{payment_id}")
async def get_payment(payment_id: str) -> Payment:
    record = state.payments.get(payment_id)
    if not record:
        raise HTTPException(404, detail="Payment not found")
    return record


@router.patch("/payments/{payment_id}/mark-paid")
async def mark_paid(payment_id: str) -> Payment:
    record = state.payments.get(payment_id)
    if not record:
        raise HTTPException(404, detail="Payment not found")
    record.payment_status = PaymentStatus.PAID
    return record
