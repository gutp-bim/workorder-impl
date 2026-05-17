from __future__ import annotations

import gutp_wo_scheduler.main as m
import pytest
from gutp_wo_scheduler.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def clear_state():
    m._schedules.clear()
    yield
    m._schedules.clear()


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
