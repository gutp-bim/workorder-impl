"""notify-dispatcher テスト共通フィクスチャ。"""

from __future__ import annotations

from unittest.mock import AsyncMock

import gutp_notify_dispatcher.main as m
import pytest
from gutp_notify_dispatcher.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def clear_state():
    m._delivery_log.clear()
    yield
    m._delivery_log.clear()


@pytest.fixture
def mock_nc():
    nc = AsyncMock()
    nc.publish = AsyncMock()
    nc.subscribe = AsyncMock()
    nc.drain = AsyncMock()
    return nc


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
