from __future__ import annotations

import gutp_payment_manager.main as m
import pytest
from gutp_payment_manager.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def clear_state():
    m._payments.clear()
    yield
    m._payments.clear()


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
