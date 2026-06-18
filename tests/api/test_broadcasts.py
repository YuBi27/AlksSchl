import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_broadcast(client: AsyncClient):
    resp = await client.post("/broadcasts", json={
        "target_type": "all_students",
        "target_id": None,
        "message_type": "text",
        "text": "Hello all students!",
        "file_id": None,
        "recipient_count": 5,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["target_type"] == "all_students"
    assert data["recipient_count"] == 5
    assert data["message_type"] == "text"
    assert "id" in data
    assert "sent_at" in data


@pytest.mark.asyncio
async def test_list_broadcasts_empty(client: AsyncClient):
    resp = await client.get("/broadcasts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_broadcasts_with_data(client: AsyncClient):
    await client.post("/broadcasts", json={
        "target_type": "group",
        "target_id": 1,
        "message_type": "photo",
        "text": "Check this out",
        "file_id": "AgACAgIxxxxx",
        "recipient_count": 3,
    })
    resp = await client.get("/broadcasts")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["target_type"] == "group"


@pytest.mark.asyncio
async def test_list_broadcasts_filtered_by_sender(client: AsyncClient):
    user = await client.post("/auth/start", json={"telegram_id": 111001, "username": "sender"})
    sender_id = user.json()["id"]

    await client.post("/broadcasts", json={
        "sender_id": sender_id,
        "target_type": "all_students",
        "message_type": "text",
        "text": "Filtered",
        "recipient_count": 2,
    })
    await client.post("/broadcasts", json={
        "sender_id": None,
        "target_type": "all_students",
        "message_type": "text",
        "text": "Other",
        "recipient_count": 1,
    })

    resp = await client.get(f"/broadcasts?sender_id={sender_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["text"] == "Filtered"
