import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_quiz(client: AsyncClient):
    user = await client.post("/auth/start", json={"telegram_id": 500001, "username": "teacher1"})
    creator_id = user.json()["id"]

    resp = await client.post("/quizzes", json={
        "title": "Test Quiz",
        "creator_id": creator_id,
        "time_limit_min": 30,
        "shuffle_questions": False,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Quiz"
    quiz_id = data["id"]

    resp2 = await client.get(f"/quizzes/{quiz_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == quiz_id
    assert resp2.json()["questions"] == []


@pytest.mark.asyncio
async def test_add_question_and_options(client: AsyncClient):
    user = await client.post("/auth/start", json={"telegram_id": 500002, "username": "teacher2"})
    creator_id = user.json()["id"]
    quiz = await client.post("/quizzes", json={"title": "Q Quiz", "creator_id": creator_id})
    quiz_id = quiz.json()["id"]

    resp = await client.post(f"/quizzes/{quiz_id}/questions", json={
        "order_idx": 0,
        "question_type": "single",
        "text": "What is 2+2?",
        "options": [
            {"text": "3", "is_correct": False},
            {"text": "4", "is_correct": True},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["question_type"] == "single"
    assert len(data["options"]) == 2

    detail = await client.get(f"/quizzes/{quiz_id}")
    assert len(detail.json()["questions"]) == 1


@pytest.mark.asyncio
async def test_quiz_attempt_and_finish(client: AsyncClient):
    t = await client.post("/auth/start", json={"telegram_id": 500003, "username": "t3"})
    quiz = await client.post("/quizzes", json={"title": "Score Quiz", "creator_id": t.json()["id"]})
    quiz_id = quiz.json()["id"]

    q_resp = await client.post(f"/quizzes/{quiz_id}/questions", json={
        "order_idx": 0,
        "question_type": "single",
        "text": "Pick correct",
        "options": [
            {"text": "wrong", "is_correct": False},
            {"text": "right", "is_correct": True},
        ],
    })
    q_id = q_resp.json()["id"]
    correct_opt_id = next(o["id"] for o in q_resp.json()["options"] if o["is_correct"])

    s = await client.post("/auth/start", json={"telegram_id": 500004, "username": "s4"})
    student_id = s.json()["id"]

    attempt = await client.post("/quiz-attempts", json={"quiz_id": quiz_id, "student_user_id": student_id})
    assert attempt.status_code == 201
    attempt_id = attempt.json()["id"]

    ans = await client.post(f"/quiz-attempts/{attempt_id}/answer", json={
        "question_id": q_id,
        "selected_options": [correct_opt_id],
    })
    assert ans.status_code == 200

    finish = await client.post(f"/quiz-attempts/{attempt_id}/finish")
    assert finish.status_code == 200
    result = finish.json()
    assert result["status"] == "completed"
    assert float(result["score"]) == 1.0
    assert float(result["max_score"]) == 1.0


@pytest.mark.asyncio
async def test_assignment_create_and_list(client: AsyncClient):
    t = await client.post("/auth/start", json={"telegram_id": 500005, "username": "t5"})
    quiz = await client.post("/quizzes", json={"title": "Assigned Quiz", "creator_id": t.json()["id"]})
    quiz_id = quiz.json()["id"]

    s = await client.post("/auth/start", json={"telegram_id": 500006, "username": "s6"})
    student_id = s.json()["id"]

    resp = await client.post("/quiz-assignments", json={
        "quiz_id": quiz_id,
        "assigned_by": t.json()["id"],
        "student_user_id": student_id,
    })
    assert resp.status_code == 201
    assignment_id = resp.json()["id"]

    list_resp = await client.get(f"/quiz-assignments?student_user_id={student_id}")
    assert list_resp.status_code == 200
    ids = [a["id"] for a in list_resp.json()]
    assert assignment_id in ids


@pytest.mark.asyncio
async def test_list_quizzes(client: AsyncClient):
    t = await client.post("/auth/start", json={"telegram_id": 500007, "username": "t7"})
    creator_id = t.json()["id"]

    await client.post("/quizzes", json={"title": "Quiz A", "creator_id": creator_id})
    await client.post("/quizzes", json={"title": "Quiz B", "creator_id": creator_id})

    resp = await client.get(f"/quizzes?creator_id={creator_id}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_delete_quiz(client: AsyncClient):
    t = await client.post("/auth/start", json={"telegram_id": 500008, "username": "t8"})
    quiz = await client.post("/quizzes", json={"title": "To Delete", "creator_id": t.json()["id"]})
    quiz_id = quiz.json()["id"]

    del_resp = await client.delete(f"/quizzes/{quiz_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/quizzes/{quiz_id}")
    assert get_resp.status_code == 404
