import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient


def _due_at(hours: int = 48) -> str:
    return (datetime.now(tz=timezone.utc) + timedelta(hours=hours)).isoformat()


async def _make_group(client: AsyncClient, name: str = "HW Group") -> dict:
    resp = await client.post("/groups", json={"name": name})
    assert resp.status_code == 201
    return resp.json()


async def _make_user(client: AsyncClient, telegram_id: int = 77771) -> dict:
    resp = await client.post("/auth/start", json={"telegram_id": telegram_id, "username": "hwuser"})
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.asyncio
async def test_create_homework_for_group(client: AsyncClient):
    teacher = await _make_user(client, 77771)
    group = await _make_group(client)
    resp = await client.post("/homeworks", json={
        "teacher_id": teacher["id"],
        "group_id": group["id"],
        "title": "Task 1",
        "description": "Do chapter 3",
        "due_at": _due_at(),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["group_id"] == group["id"]
    assert data["student_user_id"] is None
    assert data["title"] == "Task 1"


@pytest.mark.asyncio
async def test_create_homework_for_student(client: AsyncClient):
    teacher = await _make_user(client, 77772)
    student = await _make_user(client, 77773)
    resp = await client.post("/homeworks", json={
        "teacher_id": teacher["id"],
        "student_user_id": student["id"],
        "title": "Individual Task",
        "description": "Write essay",
        "due_at": _due_at(),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["student_user_id"] == student["id"]
    assert data["group_id"] is None


@pytest.mark.asyncio
async def test_create_homework_both_targets_fails(client: AsyncClient):
    teacher = await _make_user(client, 77774)
    group = await _make_group(client, "Both Group")
    student = await _make_user(client, 77775)
    resp = await client.post("/homeworks", json={
        "teacher_id": teacher["id"],
        "group_id": group["id"],
        "student_user_id": student["id"],
        "title": "Bad HW",
        "description": "Both targets",
        "due_at": _due_at(),
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_homework_no_target_fails(client: AsyncClient):
    teacher = await _make_user(client, 77776)
    resp = await client.post("/homeworks", json={
        "teacher_id": teacher["id"],
        "title": "No Target",
        "description": "Missing target",
        "due_at": _due_at(),
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_homework(client: AsyncClient):
    teacher = await _make_user(client, 77777)
    group = await _make_group(client, "Update Group")
    hw = await client.post("/homeworks", json={
        "teacher_id": teacher["id"],
        "group_id": group["id"],
        "title": "Old Title",
        "description": "Old Desc",
        "due_at": _due_at(),
    })
    hw_id = hw.json()["id"]
    resp = await client.patch(f"/homeworks/{hw_id}", json={"title": "New Title"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_homework(client: AsyncClient):
    teacher = await _make_user(client, 77778)
    group = await _make_group(client, "Delete Group")
    hw = await client.post("/homeworks", json={
        "teacher_id": teacher["id"],
        "group_id": group["id"],
        "title": "To Delete",
        "description": "Will be deleted",
        "due_at": _due_at(),
    })
    hw_id = hw.json()["id"]
    resp = await client.delete(f"/homeworks/{hw_id}")
    assert resp.status_code == 204
    resp2 = await client.get(f"/homeworks/{hw_id}")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_upsert_grade(client: AsyncClient):
    teacher = await _make_user(client, 77779)
    student = await _make_user(client, 77780)
    hw = await client.post("/homeworks", json={
        "teacher_id": teacher["id"],
        "student_user_id": student["id"],
        "title": "Grade HW",
        "description": "Grade me",
        "due_at": _due_at(),
    })
    hw_id = hw.json()["id"]
    resp = await client.post(f"/homeworks/{hw_id}/grades", json={
        "student_user_id": student["id"],
        "graded_by": teacher["id"],
        "grade_text": "Excellent!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["grade_text"] == "Excellent!"
    assert data["student_user_id"] == student["id"]


@pytest.mark.asyncio
async def test_get_grades(client: AsyncClient):
    teacher = await _make_user(client, 77781)
    student = await _make_user(client, 77782)
    hw = await client.post("/homeworks", json={
        "teacher_id": teacher["id"],
        "student_user_id": student["id"],
        "title": "Grade List HW",
        "description": "List grades",
        "due_at": _due_at(),
    })
    hw_id = hw.json()["id"]
    await client.post(f"/homeworks/{hw_id}/grades", json={
        "student_user_id": student["id"],
        "grade_text": "Good",
    })
    resp = await client.get(f"/homeworks/{hw_id}/grades")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["grade_text"] == "Good"
