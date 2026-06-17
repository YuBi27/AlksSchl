import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_import_valid(client: AsyncClient):
    rows = [
        {"full_name": "Імпорт Перший", "phone": "+380501111111", "level": "A1", "group_name": "Група A1"},
        {"full_name": "Імпорт Другий", "phone": "+380502222222", "level": "B1"},
    ]
    resp = await client.post("/students/import", json=rows)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 2
    assert data["skipped"] == 0
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_import_duplicate_phone(client: AsyncClient):
    rows = [{"full_name": "Перший", "phone": "+380503333333", "level": "A2"}]
    await client.post("/students/import", json=rows)
    rows2 = [{"full_name": "Дублікат", "phone": "+380503333333", "level": "B2"}]
    resp = await client.post("/students/import", json=rows2)
    data = resp.json()
    assert data["created"] == 0
    assert data["skipped"] == 1


@pytest.mark.asyncio
async def test_import_invalid_level(client: AsyncClient):
    rows = [{"full_name": "Невідомий рівень", "phone": "+380504444444", "level": "X9"}]
    resp = await client.post("/students/import", json=rows)
    data = resp.json()
    assert data["created"] == 1
    assert len(data["errors"]) == 1
    students = await client.get("/students?search=Невідомий")
    assert students.json()[0]["english_level"] is None


@pytest.mark.asyncio
async def test_import_creates_missing_group(client: AsyncClient):
    rows = [{"full_name": "Автогрупа Учень", "phone": "+380505555555", "group_name": "Автогрупа"}]
    resp = await client.post("/students/import", json=rows)
    assert resp.json()["created"] == 1
    groups = await client.get("/groups")
    assert any(g["name"] == "Автогрупа" for g in groups.json())


@pytest.mark.asyncio
async def test_import_missing_fields(client: AsyncClient):
    rows = [{"full_name": "", "phone": "+380506666666"}]
    resp = await client.post("/students/import", json=rows)
    data = resp.json()
    assert data["created"] == 0
    assert len(data["errors"]) == 1
