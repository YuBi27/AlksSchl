import pytest
from httpx import AsyncClient


async def _make_group(client: AsyncClient) -> dict:
    resp = await client.post("/groups", json={"name": "Att Group"})
    assert resp.status_code == 201
    return resp.json()


async def _make_lesson(client: AsyncClient, group_id: int) -> dict:
    from datetime import datetime, timedelta, timezone
    scheduled_at = (datetime.now(tz=timezone.utc) + timedelta(hours=1)).isoformat()
    resp = await client.post("/lessons", json={"group_id": group_id, "scheduled_at": scheduled_at})
    assert resp.status_code == 201
    return resp.json()


async def _make_user(client: AsyncClient, telegram_id: int = 99991) -> dict:
    resp = await client.post("/auth/start", json={"telegram_id": telegram_id, "username": "attuser"})
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.asyncio
async def test_upsert_attendance_create(client: AsyncClient):
    group = await _make_group(client)
    lesson = await _make_lesson(client, group["id"])
    user = await _make_user(client, 88881)
    resp = await client.post("/attendances", json={
        "lesson_id": lesson["id"],
        "student_user_id": user["id"],
        "status": "present",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "present"
    assert data["lesson_id"] == lesson["id"]
    assert data["student_user_id"] == user["id"]


@pytest.mark.asyncio
async def test_upsert_attendance_update_status(client: AsyncClient):
    group = await _make_group(client)
    lesson = await _make_lesson(client, group["id"])
    user = await _make_user(client, 88882)
    await client.post("/attendances", json={
        "lesson_id": lesson["id"],
        "student_user_id": user["id"],
        "status": "present",
    })
    resp = await client.post("/attendances", json={
        "lesson_id": lesson["id"],
        "student_user_id": user["id"],
        "status": "late",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "late"


@pytest.mark.asyncio
async def test_get_attendances_by_lesson(client: AsyncClient):
    group = await _make_group(client)
    lesson = await _make_lesson(client, group["id"])
    user1 = await _make_user(client, 88883)
    user2 = await _make_user(client, 88884)
    await client.post("/attendances", json={"lesson_id": lesson["id"], "student_user_id": user1["id"], "status": "present"})
    await client.post("/attendances", json={"lesson_id": lesson["id"], "student_user_id": user2["id"], "status": "absent"})
    resp = await client.get(f"/attendances?lesson_id={lesson['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_attendances_by_student(client: AsyncClient):
    group = await _make_group(client)
    lesson = await _make_lesson(client, group["id"])
    user = await _make_user(client, 88885)
    await client.post("/attendances", json={"lesson_id": lesson["id"], "student_user_id": user["id"], "status": "excused"})
    resp = await client.get(f"/attendances?student_user_id={user['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["status"] == "excused"


@pytest.mark.asyncio
async def test_attendance_status_invalid(client: AsyncClient):
    group = await _make_group(client)
    lesson = await _make_lesson(client, group["id"])
    user = await _make_user(client, 88886)
    resp = await client.post("/attendances", json={
        "lesson_id": lesson["id"],
        "student_user_id": user["id"],
        "status": "unknown",
    })
    assert resp.status_code == 422
