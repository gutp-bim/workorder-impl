from __future__ import annotations

import pytest
from gutp_ops_dashboard.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
