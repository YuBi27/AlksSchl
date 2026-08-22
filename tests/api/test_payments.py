import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_payment(client: AsyncClient):
    user = await client.post("/auth/start", json={"telegram_id": 200001, "username": "payer1"})
    user_id = user.json()["id"]
    resp = await client.post("/payments", json={
        "user_id": user_id,
        "amount": 1500.0,
        "period_start": "2026-06-01",
        "period_end": "2026-06-30",
        "payment_type": "monthly",
        "comment": "Червень 2026",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == user_id
    assert data["payment_type"] == "monthly"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_payments_empty(client: AsyncClient):
    resp = await client.get("/payments")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_payments_filtered_by_user(client: AsyncClient):
    user = await client.post("/auth/start", json={"telegram_id": 200002, "username": "payer2"})
    user_id = user.json()["id"]
    await client.post("/payments", json={
        "user_id": user_id,
        "amount": 1500.0,
        "period_start": "2026-06-01",
        "period_end": "2026-06-30",
        "payment_type": "monthly",
    })
    resp = await client.get(f"/payments?user_id={user_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["user_id"] == user_id


@pytest.mark.asyncio
async def test_debtors_includes_student_with_overdue_payment(client: AsyncClient):
    user = await client.post("/auth/start", json={"telegram_id": 200003, "username": "debtor1"})
    user_id = user.json()["id"]
    await client.patch(f"/users/{user_id}/status", json={"status": "active"})
    # Overdue: unpaid payment whose period ended in the past
    await client.post("/payments", json={
        "user_id": user_id,
        "amount": 1500,
        "period_start": "2025-01-01",
        "period_end": "2025-01-31",
        "payment_type": "monthly",
        "status": "created",
    })

    resp = await client.get("/payments/debtors")
    assert resp.status_code == 200
    debtors = {d["id"]: d for d in resp.json()}
    assert user_id in debtors
    assert debtors[user_id]["debt_total"] == 1500.0
    assert debtors[user_id]["debt_count"] == 1


@pytest.mark.asyncio
async def test_debtors_excludes_paid_student(client: AsyncClient):
    import calendar
    from datetime import date
    today = date.today()
    first = today.replace(day=1).isoformat()
    last_day = calendar.monthrange(today.year, today.month)[1]
    last = today.replace(day=last_day).isoformat()

    user = await client.post("/auth/start", json={"telegram_id": 200004, "username": "paid1"})
    user_id = user.json()["id"]
    await client.patch(f"/users/{user_id}/status", json={"status": "active"})
    await client.post("/payments", json={
        "user_id": user_id,
        "amount": 1500.0,
        "period_start": first,
        "period_end": last,
        "payment_type": "monthly",
    })

    resp = await client.get("/payments/debtors")
    ids = [d["id"] for d in resp.json()]
    assert user_id not in ids
