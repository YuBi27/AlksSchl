import pytest
from datetime import datetime, timezone, timedelta, date
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_financial_empty(client: AsyncClient):
    resp = await client.get("/stats/financial")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_confirmed"] == 0.0
    assert data["debtors_count"] == 0
    assert data["monthly_revenue"] == []


@pytest.mark.asyncio
async def test_financial_with_payments(client: AsyncClient):
    user = await client.post("/auth/start", json={"telegram_id": 800001, "username": "payer_a"})
    user_id = user.json()["id"]

    today = date.today()
    resp = await client.post("/payments", json={
        "user_id": user_id,
        "amount": 1500.0,
        "period_start": today.replace(day=1).isoformat(),
        "period_end": today.isoformat(),
        "payment_type": "monthly",
        "status": "confirmed",
    })
    payment_id = resp.json()["id"]
    await client.patch(f"/payments/{payment_id}/status", json={"status": "confirmed"})

    resp2 = await client.get("/stats/financial?days=30")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["confirmed_count"] >= 1


@pytest.mark.asyncio
async def test_attendance_empty(client: AsyncClient):
    resp = await client.get("/stats/attendance")
    assert resp.status_code == 200
    data = resp.json()
    assert data["by_group"] == []
    assert data["by_student"] == []


@pytest.mark.asyncio
async def test_attendance_with_data(client: AsyncClient):
    grp = await client.post("/groups", json={"name": "Analytics Group", "level": "A1"})
    group_id = grp.json()["id"]

    user = await client.post("/auth/start", json={"telegram_id": 800002, "username": "stu_att"})
    user_id = user.json()["id"]
    await client.post(f"/students/{user_id}/groups", json={"group_ids": [group_id]})

    lesson_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    lesson_resp = await client.post("/lessons", json={
        "group_id": group_id,
        "scheduled_at": lesson_time,
        "duration_min": 60,
    })
    lesson_id = lesson_resp.json()["id"]

    await client.post("/attendances", json={
        "lesson_id": lesson_id,
        "student_user_id": user_id,
        "status": "present",
    })

    resp = await client.get(f"/stats/attendance?days=30&group_id={group_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["by_group"]) == 1
    assert data["by_group"][0]["percent"] == 100
    assert len(data["by_student"]) == 1
    assert data["by_student"][0]["percent"] == 100


@pytest.mark.asyncio
async def test_performance_empty(client: AsyncClient):
    resp = await client.get("/stats/performance")
    assert resp.status_code == 200
    data = resp.json()
    assert data["homework"]["assigned_count"] == 0
    assert data["quizzes"]["attempts_count"] == 0
    assert data["student_ranking"] == []


@pytest.mark.asyncio
async def test_performance_with_quiz_data(client: AsyncClient):
    teacher = await client.post("/auth/start", json={"telegram_id": 800003, "username": "t_perf"})
    teacher_id = teacher.json()["id"]
    student = await client.post("/auth/start", json={"telegram_id": 800004, "username": "s_perf"})
    student_id = student.json()["id"]
    await client.patch(f"/users/{student_id}/status", json={"status": "active"})

    quiz = await client.post("/quizzes", json={"title": "Perf Quiz", "creator_id": teacher_id})
    quiz_id = quiz.json()["id"]
    q_resp = await client.post(f"/quizzes/{quiz_id}/questions", json={
        "order_idx": 0,
        "question_type": "single",
        "text": "Q?",
        "options": [
            {"text": "wrong", "is_correct": False},
            {"text": "right", "is_correct": True},
        ],
    })
    q_id = q_resp.json()["id"]
    correct_id = next(o["id"] for o in q_resp.json()["options"] if o["is_correct"])

    attempt = await client.post("/quiz-attempts", json={"quiz_id": quiz_id, "student_user_id": student_id})
    attempt_id = attempt.json()["id"]
    await client.post(f"/quiz-attempts/{attempt_id}/answer", json={
        "question_id": q_id,
        "selected_options": [correct_id],
    })
    await client.post(f"/quiz-attempts/{attempt_id}/finish")

    resp = await client.get("/stats/performance?days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["quizzes"]["completed_count"] >= 1
    assert data["quizzes"]["avg_score_pct"] == 100


@pytest.mark.asyncio
async def test_invalid_days(client: AsyncClient):
    resp = await client.get("/stats/financial?days=5")
    assert resp.status_code == 400
    resp2 = await client.get("/stats/attendance?days=400")
    assert resp2.status_code == 400
