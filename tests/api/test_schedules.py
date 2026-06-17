import pytest
from httpx import AsyncClient


async def _make_group(client: AsyncClient, name: str = "Тест Група") -> dict:
    resp = await client.post("/groups", json={"name": name, "level": "B1"})
    return resp.json()


@pytest.mark.asyncio
async def test_list_schedules_empty(client: AsyncClient):
    group = await _make_group(client)
    resp = await client.get(f"/schedules?group_id={group['id']}")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_schedule_generates_lessons(client: AsyncClient):
    group = await _make_group(client, "Вівторок Група")
    resp = await client.post("/schedules", json={
        "group_id": group["id"],
        "day_of_week": 1,  # Tuesday
        "start_time": "17:00",
        "duration_min": 60,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["group_id"] == group["id"]
    assert data["day_of_week"] == 1
    assert data["start_time"].startswith("17:00")
    assert data["is_active"] is True

    # Verify lessons were generated
    gid = group["id"]
    lessons_resp = await client.get(f"/lessons?group_id={gid}")
    assert lessons_resp.status_code == 200
    lessons = lessons_resp.json()
    assert len(lessons) >= 7   # At least 7 Tuesdays in 8 weeks
    assert len(lessons) <= 9   # At most 9
    assert all(l["status"] == "scheduled" for l in lessons)


@pytest.mark.asyncio
async def test_get_schedule(client: AsyncClient):
    group = await _make_group(client)
    create = await client.post("/schedules", json={
        "group_id": group["id"], "day_of_week": 0, "start_time": "10:00"
    })
    sid = create.json()["id"]
    resp = await client.get(f"/schedules/{sid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sid


@pytest.mark.asyncio
async def test_get_schedule_not_found(client: AsyncClient):
    resp = await client.get("/schedules/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_schedule(client: AsyncClient):
    group = await _make_group(client)
    create = await client.post("/schedules", json={
        "group_id": group["id"], "day_of_week": 2, "start_time": "09:00"
    })
    sid = create.json()["id"]
    resp = await client.patch(f"/schedules/{sid}", json={"start_time": "11:00", "duration_min": 90})
    assert resp.status_code == 200
    assert resp.json()["start_time"].startswith("11:00")
    assert resp.json()["duration_min"] == 90


@pytest.mark.asyncio
async def test_delete_schedule(client: AsyncClient):
    group = await _make_group(client)
    create = await client.post("/schedules", json={
        "group_id": group["id"], "day_of_week": 3, "start_time": "16:00"
    })
    sid = create.json()["id"]
    resp = await client.delete(f"/schedules/{sid}")
    assert resp.status_code == 204
    # Schedule deactivated, not deleted
    get_resp = await client.get(f"/schedules/{sid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_generate_upcoming(client: AsyncClient):
    group = await _make_group(client)
    await client.post("/schedules", json={
        "group_id": group["id"], "day_of_week": 4, "start_time": "18:00"
    })
    resp = await client.post("/schedules/generate-upcoming")
    assert resp.status_code == 200
    assert "generated" in resp.json()
