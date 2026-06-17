import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_groups_empty(client: AsyncClient):
    resp = await client.get("/groups")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_group(client: AsyncClient):
    resp = await client.post("/groups", json={"name": "Група B1", "level": "B1"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Група B1"
    assert data["level"] == "B1"
    assert data["student_count"] == 0


@pytest.mark.asyncio
async def test_get_group(client: AsyncClient):
    create = await client.post("/groups", json={"name": "Beginner", "level": "A1"})
    gid = create.json()["id"]
    resp = await client.get(f"/groups/{gid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Beginner"


@pytest.mark.asyncio
async def test_get_group_not_found(client: AsyncClient):
    resp = await client.get("/groups/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_group(client: AsyncClient):
    create = await client.post("/groups", json={"name": "Old"})
    gid = create.json()["id"]
    resp = await client.patch(f"/groups/{gid}", json={"name": "New", "level": "C1"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"
    assert resp.json()["level"] == "C1"


@pytest.mark.asyncio
async def test_delete_group(client: AsyncClient):
    create = await client.post("/groups", json={"name": "To Delete"})
    gid = create.json()["id"]
    assert (await client.delete(f"/groups/{gid}")).status_code == 204
    assert (await client.get(f"/groups/{gid}")).status_code == 404


@pytest.mark.asyncio
async def test_group_students(client: AsyncClient):
    create = await client.post("/groups", json={"name": "Test Group"})
    gid = create.json()["id"]
    resp = await client.get(f"/groups/{gid}/students")
    assert resp.status_code == 200
    assert resp.json() == []
