import pytest
from httpx import AsyncClient


async def _make_student(client: AsyncClient, tg_id: int, full_name: str, phone: str) -> dict:
    """Helper: create user + student profile, return user dict."""
    auth = await client.post("/auth/start", json={"telegram_id": tg_id, "username": None})
    user = auth.json()
    await client.post(
        f"/users/{user['id']}/student-profile",
        json={"full_name": full_name, "phone": phone},
    )
    return user


@pytest.mark.asyncio
async def test_list_students_empty(client: AsyncClient):
    resp = await client.get("/students")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_students_returns_students(client: AsyncClient):
    await _make_student(client, 111111, "Іваненко Дмитро", "+380991111111")
    resp = await client.get("/students")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["full_name"] == "Іваненко Дмитро"


@pytest.mark.asyncio
async def test_search_by_name(client: AsyncClient):
    await _make_student(client, 222222, "Петренко Марія", "+380992222222")
    await _make_student(client, 333333, "Сидоренко Олег", "+380993333333")
    resp = await client.get("/students?search=Петренко")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["full_name"] == "Петренко Марія"


@pytest.mark.asyncio
async def test_search_by_phone(client: AsyncClient):
    await _make_student(client, 444444, "Коваль Юлія", "+380994444444")
    resp = await client.get("/students?search=4444444")
    results = resp.json()
    assert len(results) == 1
    assert results[0]["phone"] == "+380994444444"


@pytest.mark.asyncio
async def test_get_student(client: AsyncClient):
    user = await _make_student(client, 555555, "Мороз Артем", "+380995555555")
    resp = await client.get(f"/students/{user['id']}")
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Мороз Артем"


@pytest.mark.asyncio
async def test_get_student_not_found(client: AsyncClient):
    resp = await client.get("/students/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_set_level(client: AsyncClient):
    user = await _make_student(client, 666666, "Лисенко Ірина", "+380996666666")
    resp = await client.patch(f"/students/{user['id']}/level", json={"level": "B2"})
    assert resp.status_code == 204
    detail = await client.get(f"/students/{user['id']}")
    assert detail.json()["english_level"] == "B2"


@pytest.mark.asyncio
async def test_set_level_pre_a1(client: AsyncClient):
    user = await _make_student(client, 666667, "Мала Соня", "+380996666667")
    resp = await client.patch(f"/students/{user['id']}/level", json={"level": "preA1"})
    assert resp.status_code == 204
    detail = await client.get(f"/students/{user['id']}")
    assert detail.json()["english_level"] == "preA1"


@pytest.mark.asyncio
async def test_filter_by_level(client: AsyncClient):
    u1 = await _make_student(client, 777777, "Рівень B1", "+380997777771")
    u2 = await _make_student(client, 888888, "Рівень C1", "+380997777772")
    await client.patch(f"/students/{u1['id']}/level", json={"level": "B1"})
    await client.patch(f"/students/{u2['id']}/level", json={"level": "C1"})
    resp = await client.get("/students?level=B1")
    assert len(resp.json()) == 1
    assert resp.json()[0]["english_level"] == "B1"


@pytest.mark.asyncio
async def test_delete_removes_student(client: AsyncClient):
    user = await _make_student(client, 999999, "Видалений", "+380997777773")
    resp = await client.delete(f"/students/{user['id']}")
    assert resp.status_code == 204
    # Hard delete: student is gone so they can re-apply from scratch
    detail = await client.get(f"/students/{user['id']}")
    assert detail.status_code == 404


@pytest.mark.asyncio
async def test_assign_groups(client: AsyncClient):
    user = await _make_student(client, 1111110, "Груповий", "+380997777774")
    grp = await client.post("/groups", json={"name": "Тест Група"})
    gid = grp.json()["id"]
    resp = await client.post(
        f"/students/{user['id']}/groups", json={"group_ids": [gid]}
    )
    assert resp.status_code == 204
    filtered = await client.get(f"/students?group_id={gid}")
    assert len(filtered.json()) == 1


@pytest.mark.asyncio
async def test_remove_from_group(client: AsyncClient):
    user = await _make_student(client, 1111111, "Видалити з групи", "+380997777775")
    grp = await client.post("/groups", json={"name": "Ще Група"})
    gid = grp.json()["id"]
    await client.post(f"/students/{user['id']}/groups", json={"group_ids": [gid]})
    resp = await client.delete(f"/students/{user['id']}/groups/{gid}")
    assert resp.status_code == 204
    filtered = await client.get(f"/students?group_id={gid}")
    assert len(filtered.json()) == 0
