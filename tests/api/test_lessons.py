import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient


def _future_dt(hours: int = 25) -> str:
    """ISO UTC datetime N hours from now."""
    return (datetime.now(tz=timezone.utc) + timedelta(hours=hours)).isoformat()


async def _make_group(client: AsyncClient, name: str = "Урок Група") -> dict:
    resp = await client.post("/groups", json={"name": name})
    return resp.json()


@pytest.mark.asyncio
async def test_create_lesson(client: AsyncClient):
    group = await _make_group(client)
    resp = await client.post("/lessons", json={
        "group_id": group["id"],
        "scheduled_at": _future_dt(25),
        "duration_min": 60,
        "zoom_link": "https://zoom.us/j/123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["group_id"] == group["id"]
    assert data["zoom_link"] == "https://zoom.us/j/123"
    assert data["status"] == "scheduled"


@pytest.mark.asyncio
async def test_list_lessons_by_group(client: AsyncClient):
    group = await _make_group(client, "Фільтр Група")
    await client.post("/lessons", json={
        "group_id": group["id"], "scheduled_at": _future_dt(10)
    })
    await client.post("/lessons", json={
        "group_id": group["id"], "scheduled_at": _future_dt(20)
    })
    resp = await client.get(f"/lessons?group_id={group['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_lesson(client: AsyncClient):
    group = await _make_group(client)
    create = await client.post("/lessons", json={
        "group_id": group["id"], "scheduled_at": _future_dt(5)
    })
    lid = create.json()["id"]
    resp = await client.get(f"/lessons/{lid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == lid


@pytest.mark.asyncio
async def test_get_lesson_not_found(client: AsyncClient):
    resp = await client.get("/lessons/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_lesson_zoom(client: AsyncClient):
    group = await _make_group(client)
    create = await client.post("/lessons", json={
        "group_id": group["id"], "scheduled_at": _future_dt(30)
    })
    lid = create.json()["id"]
    resp = await client.patch(f"/lessons/{lid}", json={"zoom_link": "https://zoom.us/j/456"})
    assert resp.status_code == 200
    assert resp.json()["zoom_link"] == "https://zoom.us/j/456"


@pytest.mark.asyncio
async def test_cancel_lesson(client: AsyncClient):
    group = await _make_group(client)
    create = await client.post("/lessons", json={
        "group_id": group["id"], "scheduled_at": _future_dt(48)
    })
    lid = create.json()["id"]
    resp = await client.delete(f"/lessons/{lid}")
    assert resp.status_code == 204
    get_resp = await client.get(f"/lessons/{lid}")
    assert get_resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_due_reminders_24h(client: AsyncClient):
    group = await _make_group(client, "Нагадування Група")
    # Lesson in 23 hours (within 24h window)
    await client.post("/lessons", json={
        "group_id": group["id"],
        "scheduled_at": _future_dt(23),
    })
    resp = await client.get("/lessons/due-reminders")
    assert resp.status_code == 200
    reminders = resp.json()
    assert len(reminders) >= 1
    assert reminders[0]["reminder_24h_sent"] is False


@pytest.mark.asyncio
async def test_due_reminders_excludes_past(client: AsyncClient):
    group = await _make_group(client, "Минулі")
    # Past lesson
    past = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()
    await client.post("/lessons", json={
        "group_id": group["id"], "scheduled_at": past
    })
    resp = await client.get("/lessons/due-reminders")
    lessons = resp.json()
    # Past lesson should not appear
    assert all(l["group_id"] != group["id"] for l in lessons)


@pytest.mark.asyncio
async def test_mark_reminder_sent(client: AsyncClient):
    group = await _make_group(client, "Маркер Група")
    create = await client.post("/lessons", json={
        "group_id": group["id"], "scheduled_at": _future_dt(23)
    })
    lid = create.json()["id"]
    resp = await client.patch(f"/lessons/{lid}/reminders", json={"reminder_24h_sent": True})
    assert resp.status_code == 200
    get_resp = await client.get(f"/lessons/{lid}")
    assert get_resp.json()["reminder_24h_sent"] is True
    # Should no longer appear in due-reminders
    due = await client.get("/lessons/due-reminders")
    assert all(l["id"] != lid for l in due.json())
