import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_stats_overview_empty(client: AsyncClient):
    resp = await client.get("/stats/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_students"] == 0
    assert data["pending_students"] == 0
    assert data["total_groups"] == 0
    assert data["lessons_today"] == 0
    assert data["lessons_this_week"] == 0
    assert data["overdue_homework"] == 0
    assert data["hw_due_this_week"] == 0
    assert data["attendance_by_group"] == []


@pytest.mark.asyncio
async def test_stats_counts_students(client: AsyncClient):
    # Create active student
    u1 = await client.post("/auth/start", json={"telegram_id": 333001, "username": "s1"})
    uid1 = u1.json()["id"]
    await client.patch(f"/users/{uid1}/status", json={"status": "active"})

    # Create pending student (default status)
    await client.post("/auth/start", json={"telegram_id": 333002, "username": "s2"})

    resp = await client.get("/stats/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_students"] == 1
    assert data["pending_students"] == 1


@pytest.mark.asyncio
async def test_stats_counts_groups(client: AsyncClient):
    await client.post("/groups", json={"name": "Група A", "level": "A1"})
    await client.post("/groups", json={"name": "Група B", "level": "B1"})
    resp = await client.get("/stats/overview")
    assert resp.json()["total_groups"] == 2
