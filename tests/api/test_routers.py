import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_auth_start_creates_student(client):
    resp = await client.post("/auth/start", json={"telegram_id": 999001, "username": "newuser"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["telegram_id"] == 999001
    # "new" = ще заповнює форму; "pending" ставиться лише після подання заявки,
    # інакше blocked-роутер перехоплює текстові повідомлення і реєстрація обривається на ПІБ
    assert data["status"] == "new"
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_auth_start_idempotent(client):
    await client.post("/auth/start", json={"telegram_id": 999002, "username": "bob"})
    resp = await client.post("/auth/start", json={"telegram_id": 999002, "username": "bob"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_language(client):
    await client.post("/auth/start", json={"telegram_id": 999003, "username": "carol"})
    resp = await client.patch("/users/999003/language", json={"language": "en"})
    assert resp.status_code == 200
    assert resp.json()["language"] == "en"


@pytest.mark.asyncio
async def test_invite_code_not_found(client):
    resp = await client.get("/invite-codes/NONEXISTENT")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_agreement(client):
    user_resp = await client.post("/auth/start", json={"telegram_id": 999004, "username": "dave"})
    user_id = user_resp.json()["id"]
    resp = await client.post("/agreements", json={
        "user_id": user_id, "telegram_id": 999004, "type": "rules"
    })
    assert resp.status_code == 200
    assert resp.json()["type"] == "rules"


@pytest.mark.asyncio
async def test_get_user_by_id(client):
    user_resp = await client.post("/auth/start", json={"telegram_id": 999005, "username": "eve"})
    user_id = user_resp.json()["id"]
    resp = await client.get(f"/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["telegram_id"] == 999005
