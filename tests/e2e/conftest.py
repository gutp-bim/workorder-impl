from __future__ import annotations

import os

import httpx
import pytest

OBS_COLLECTOR_URL = os.getenv("OBS_COLLECTOR_URL", "http://localhost:8001")
ISSUE_MANAGER_URL = os.getenv("ISSUE_MANAGER_URL", "http://localhost:8002")
TICKET_MANAGER_URL = os.getenv("TICKET_MANAGER_URL", "http://localhost:8003")
WO_MANAGER_URL = os.getenv("WO_MANAGER_URL", "http://localhost:8004")
WO_SCHEDULER_URL = os.getenv("WO_SCHEDULER_URL", "http://localhost:8008")


@pytest.fixture
async def http():
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client
