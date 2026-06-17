import pytest
from httpx import AsyncClient


async def _make_user(client: AsyncClient, telegram_id: int = 66661) -> dict:
    resp = await client.post("/auth/start", json={"telegram_id": telegram_id, "username": "noteuser"})
    assert resp.status_code == 200
    return resp.json()


async def _make_lesson(client: AsyncClient, group_id: int) -> dict:
    from datetime import datetime, timedelta, timezone
    scheduled_at = (datetime.now(tz=timezone.utc) + timedelta(hours=2)).isoformat()
    resp = await client.post("/lessons", json={"group_id": group_id, "scheduled_at": scheduled_at})
    assert resp.status_code == 201
    return resp.json()


async def _make_group(client: AsyncClient, name: str = "Note Group") -> dict:
    resp = await client.post("/groups", json={"name": name})
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_create_student_note(client: AsyncClient):
    teacher = await _make_user(client, 66661)
    student = await _make_user(client, 66662)
    resp = await client.post("/teacher-notes", json={
        "teacher_id": teacher["id"],
        "student_user_id": student["id"],
        "text": "Needs improvement in pronunciation",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["student_user_id"] == student["id"]
    assert data["text"] == "Needs improvement in pronunciation"


@pytest.mark.asyncio
async def test_create_lesson_note(client: AsyncClient):
    teacher = await _make_user(client, 66663)
    group = await _make_group(client)
    lesson = await _make_lesson(client, group["id"])
    resp = await client.post("/teacher-notes", json={
        "teacher_id": teacher["id"],
        "lesson_id": lesson["id"],
        "text": "Good energy today",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["lesson_id"] == lesson["id"]


@pytest.mark.asyncio
async def test_create_note_no_target_fails(client: AsyncClient):
    teacher = await _make_user(client, 66664)
    resp = await client.post("/teacher-notes", json={
        "teacher_id": teacher["id"],
        "text": "No target",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_note(client: AsyncClient):
    teacher = await _make_user(client, 66665)
    student = await _make_user(client, 66666)
    create = await client.post("/teacher-notes", json={
        "teacher_id": teacher["id"],
        "student_user_id": student["id"],
        "text": "Delete me",
    })
    note_id = create.json()["id"]
    resp = await client.delete(f"/teacher-notes/{note_id}")
    assert resp.status_code == 204
