from __future__ import annotations

from unittest.mock import AsyncMock

import gutp_ticket_manager.main as m
import pytest
from gutp_ticket_manager.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def clear_state():
    m._tickets.clear()
    m._estimates.clear()
    yield
    m._tickets.clear()
    m._estimates.clear()


@pytest.fixture
async def ac():
    m._nc = AsyncMock()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
