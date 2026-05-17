from __future__ import annotations

import httpx
import pytest


@pytest.fixture
async def http():
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client
