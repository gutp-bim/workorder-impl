import pytest


@pytest.mark.anyio
async def test_create_schedule(ac):
    body = {
        "title": "空調フィルター交換",
        "interval_days": 90,
        "issue_type": "FacilityAsset",
        "next_trigger_at": "2026-07-01T00:00:00",
    }
    resp = await ac.post("/schedules", json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert data["schedule_id"].startswith("sched-")
    assert data["title"] == "空調フィルター交換"
    assert data["interval_days"] == 90
    assert data["last_triggered_at"] is None


@pytest.mark.anyio
async def test_list_schedules(ac):
    await ac.post(
        "/schedules",
        json={
            "title": "A",
            "interval_days": 30,
            "issue_type": "FacilityAsset",
            "next_trigger_at": "2026-06-01T00:00:00",
        },
    )
    resp = await ac.get("/schedules")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.anyio
async def test_delete_schedule(ac):
    r = await ac.post(
        "/schedules",
        json={
            "title": "B",
            "interval_days": 7,
            "issue_type": "Operations",
            "next_trigger_at": "2026-06-01T00:00:00",
        },
    )
    sid = r.json()["schedule_id"]
    resp = await ac.delete(f"/schedules/{sid}")
    assert resp.status_code == 204
    assert (await ac.delete(f"/schedules/{sid}")).status_code == 404
