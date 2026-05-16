from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_nc():
    nc = AsyncMock()
    nc.publish = AsyncMock()
    nc.subscribe = AsyncMock()
    nc.drain = AsyncMock()
    return nc


@pytest.fixture
async def ac():
    """issue-manager の AsyncClient（lifespan は起動しない）。"""
    import gutp_issue_manager.main as m

    m._issues.clear()

    from gutp_issue_manager.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
