import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_content_not_found(client: AsyncClient):
    resp = await client.get("/bot-content/school_rules")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upsert_content_create(client: AsyncClient):
    resp = await client.put("/bot-content/school_rules", json={"value": "Не запізнюйтеся."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"] == "school_rules"
    assert data["value"] == "Не запізнюйтеся."
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_upsert_content_update(client: AsyncClient):
    await client.put("/bot-content/price_list", json={"value": "Старий текст"})
    resp = await client.put("/bot-content/price_list", json={"value": "Новий текст"})
    assert resp.status_code == 200
    assert resp.json()["value"] == "Новий текст"


@pytest.mark.asyncio
async def test_get_content_after_upsert(client: AsyncClient):
    await client.put("/bot-content/school_info", json={"value": "вул. Навчальна, 1"})
    resp = await client.get("/bot-content/school_info")
    assert resp.status_code == 200
    assert resp.json()["value"] == "вул. Навчальна, 1"


@pytest.mark.asyncio
async def test_list_teacher_profiles_empty(client: AsyncClient):
    resp = await client.get("/teacher-profiles")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_teacher_profiles(client: AsyncClient):
    user = await client.post("/auth/start", json={"telegram_id": 222001, "username": "teacher1"})
    user_id = user.json()["id"]
    await client.put(f"/users/{user_id}/status", json={"status": "active"})
    await client.post(f"/users/{user_id}/teacher-profile", json={
        "full_name": "Олена Іваненко",
        "bio": "Досвідчений викладач",
        "specialization": "Розмовна англійська",
        "experience_years": 5,
    })
    resp = await client.get("/teacher-profiles")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["full_name"] == "Олена Іваненко"
