from typing import Any, Optional
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput


def _trunc(text: str, max_len: int = 50) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


class StudentQuizSG(StatesGroup):
    quiz_list = State()
    quiz_intro = State()
    question_step = State()
    quiz_done = State()
    answer_review = State()


# ---- Getters ----

async def get_quiz_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_data = dialog_manager.middleware_data["user_data"]
    user_id = user_data["id"]

    assignments = await api_client.list_quiz_assignments_for_student(user_id)

    completed_attempts = await api_client.list_quiz_attempts(student_user_id=user_id, status="completed")
    in_progress_attempts = await api_client.list_quiz_attempts(student_user_id=user_id, status="in_progress")
    completed_quiz_ids = {a["quiz_id"] for a in completed_attempts}
    in_progress_quiz_ids = {a["quiz_id"] for a in in_progress_attempts}

    items = []
    all_assignments = []
    seen_quiz_ids: set[int] = set()

    for a in assignments:
        qid = a["quiz_id"]
        if qid in seen_quiz_ids:
            continue
        seen_quiz_ids.add(qid)
        all_assignments.append(a)

        if qid in completed_quiz_ids:
            icon = "✅"
        elif qid in in_progress_quiz_ids:
            icon = "🔄"
        else:
            icon = "⏳"

        try:
            quiz = await api_client.get_quiz(qid)
            title = quiz["title"]
        except Exception:
            title = f"Тест #{qid}"

        deadline_str = ""
        if a.get("deadline"):
            deadline_str = f" | до {a['deadline'][:10]}"

        items.append((str(len(items)), _trunc(f"{icon} {title}{deadline_str}")))

    dialog_manager.dialog_data["assignments_list"] = all_assignments
    return {"quizzes": items, "has_quizzes": bool(items)}


async def get_quiz_intro(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    assignment_idx = dialog_manager.dialog_data.get("selected_assignment_idx", 0)
    assignments = dialog_manager.dialog_data.get("assignments_list", [])
    assignment = assignments[assignment_idx] if assignment_idx < len(assignments) else {}
    quiz_id = assignment.get("quiz_id") or dialog_manager.dialog_data.get("quiz_id")
    quiz = await api_client.get_quiz(quiz_id)
    dialog_manager.dialog_data["quiz_id"] = quiz_id

    user_id = dialog_manager.middleware_data["user_data"]["id"]
    active_attempts = await api_client.list_quiz_attempts(
        quiz_id=quiz_id, student_user_id=user_id, status="in_progress"
    )
    has_active = bool(active_attempts)

    return {
        "title": quiz["title"],
        "description": quiz.get("description") or "",
        "q_count": len(quiz.get("questions", [])),
        "time_limit": f"⏱ {quiz['time_limit_min']} хв" if quiz.get("time_limit_min") else "",
        "btn_label": "▶️ Продовжити" if has_active else "▶️ Почати тест",
    }


async def get_question_step(dialog_manager: DialogManager, **kwargs) -> dict:
    questions = dialog_manager.dialog_data.get("quiz_questions", [])
    idx = dialog_manager.dialog_data.get("current_q_idx", 0)

    if idx >= len(questions):
        return {
            "q_text": "", "q_num": 0, "q_total": 0,
            "is_single": False, "is_multi": False, "is_text": False,
            "single_options": [], "multi_options": [], "has_multi_selection": False,
        }

    q = questions[idx]
    q_type = q["question_type"]
    multi_sel = dialog_manager.dialog_data.get("multi_selected", [])

    result: dict = {
        "q_text": q["text"],
        "q_num": idx + 1,
        "q_total": len(questions),
        "is_single": q_type == "single",
        "is_multi": q_type == "multi",
        "is_text": q_type == "text",
        "single_options": [],
        "multi_options": [],
        "has_multi_selection": bool(multi_sel),
    }

    if q_type == "single":
        result["single_options"] = [(str(opt["id"]), opt["text"]) for opt in q.get("options", [])]
    elif q_type == "multi":
        result["multi_options"] = [
            (str(opt["id"]), ("✅ " if opt["id"] in multi_sel else "⬜ ") + opt["text"])
            for opt in q.get("options", [])
        ]

    return result


async def get_quiz_done(dialog_manager: DialogManager, **kwargs) -> dict:
    result = dialog_manager.dialog_data.get("quiz_result", {})
    score = float(result.get("score", 0))
    max_score = float(result.get("max_score", 0))
    pct = int(score / max_score * 100) if max_score > 0 else 0

    elapsed = ""
    if result.get("started_at") and result.get("finished_at"):
        from datetime import datetime
        start = datetime.fromisoformat(result["started_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(result["finished_at"].replace("Z", "+00:00"))
        secs = int((end - start).total_seconds())
        elapsed = f"\n⏱ Час: {secs // 60}:{secs % 60:02d}"

    return {
        "score": f"{score:.0f}",
        "max_score": f"{max_score:.0f}",
        "pct": pct,
        "elapsed": elapsed,
    }


async def get_answer_review(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    attempt_id = dialog_manager.dialog_data.get("attempt_id")
    attempt = await api_client.get_quiz_attempt(attempt_id)
    quiz = await api_client.get_quiz(attempt["quiz_id"])
    q_map = {q["id"]: q for q in quiz["questions"]}
    lines = []
    for ans in attempt.get("answers", []):
        q = q_map.get(ans["question_id"], {})
        q_text = (q.get("text") or "")[:40]
        if q.get("question_type") == "text":
            status = "📝"
            detail = ans.get("text_answer") or "—"
        elif ans.get("is_correct"):
            status = "✅"
            opt_map = {o["id"]: o["text"] for o in q.get("options", [])}
            detail = ", ".join(opt_map.get(i, str(i)) for i in ans.get("selected_options", []))
        else:
            status = "❌"
            opt_map = {o["id"]: o["text"] for o in q.get("options", [])}
            detail = ", ".join(opt_map.get(i, str(i)) for i in ans.get("selected_options", []))
        lines.append(f"{status} {q_text}: {detail}")
    return {"review_text": "\n".join(lines) or "Немає відповідей"}


# ---- Handlers ----

async def on_quiz_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    manager.dialog_data["selected_assignment_idx"] = int(item_id)
    await manager.switch_to(StudentQuizSG.quiz_intro)


async def on_start_quiz(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    user_id = manager.middleware_data["user_data"]["id"]
    quiz_id = manager.dialog_data["quiz_id"]
    assignment_idx = manager.dialog_data.get("selected_assignment_idx", 0)
    assignments = manager.dialog_data.get("assignments_list", [])
    assignment = assignments[assignment_idx] if assignment_idx < len(assignments) else {}
    assignment_id = assignment.get("id")

    active_attempts = await api_client.list_quiz_attempts(
        quiz_id=quiz_id, student_user_id=user_id, status="in_progress"
    )
    if active_attempts:
        attempt = active_attempts[0]
    else:
        attempt = await api_client.start_quiz_attempt(quiz_id, user_id, assignment_id)

    quiz = await api_client.get_quiz(quiz_id)
    questions = quiz["questions"]
    answered_ids = {a["question_id"] for a in attempt.get("answers", [])}
    first_unanswered = next(
        (i for i, q in enumerate(questions) if q["id"] not in answered_ids),
        len(questions),
    )

    manager.dialog_data["attempt_id"] = attempt["id"]
    manager.dialog_data["quiz_questions"] = questions
    manager.dialog_data["current_q_idx"] = first_unanswered
    manager.dialog_data["multi_selected"] = []

    if first_unanswered >= len(questions):
        result = await api_client.finish_quiz_attempt(attempt["id"])
        manager.dialog_data["quiz_result"] = result
        await manager.switch_to(StudentQuizSG.quiz_done)
    else:
        await manager.switch_to(StudentQuizSG.question_step)


async def on_single_answer(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    await _submit_answer(manager, selected_options=[int(item_id)])


async def on_multi_toggle(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    selected = manager.dialog_data.get("multi_selected", [])
    opt_id = int(item_id)
    if opt_id in selected:
        selected.remove(opt_id)
    else:
        selected.append(opt_id)
    manager.dialog_data["multi_selected"] = selected


async def on_multi_confirm(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    selected = manager.dialog_data.get("multi_selected", [])
    await _submit_answer(manager, selected_options=selected)


async def on_text_answer(message: Message, widget: Any, manager: DialogManager, value: str) -> None:
    await _submit_answer(manager, selected_options=[], text_answer=value.strip())


async def _submit_answer(
    manager: DialogManager,
    selected_options: list[int],
    text_answer: Optional[str] = None,
) -> None:
    api_client = manager.middleware_data["api_client"]
    questions = manager.dialog_data["quiz_questions"]
    idx = manager.dialog_data["current_q_idx"]
    q = questions[idx]

    await api_client.save_quiz_answer(
        attempt_id=manager.dialog_data["attempt_id"],
        question_id=q["id"],
        selected_options=selected_options,
        text_answer=text_answer,
    )

    next_idx = idx + 1
    manager.dialog_data["current_q_idx"] = next_idx
    manager.dialog_data["multi_selected"] = []

    if next_idx >= len(questions):
        result = await api_client.finish_quiz_attempt(manager.dialog_data["attempt_id"])
        manager.dialog_data["quiz_result"] = result
        await manager.switch_to(StudentQuizSG.quiz_done)
    else:
        await manager.switch_to(StudentQuizSG.question_step)


async def on_view_review(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(StudentQuizSG.answer_review)


def _back(state: State):
    async def handler(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
        await manager.switch_to(state)
    return handler


# ---- Dialog ----

dialog = Dialog(
    Window(
        Const("📝 Мої тести"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="quiz_sel",
                item_id_getter=lambda x: x[0],
                items="quizzes",
                on_click=on_quiz_selected,
            ),
            id="quizzes_sg", width=1, height=7,
        ),
        state=StudentQuizSG.quiz_list,
        getter=get_quiz_list,
    ),
    Window(
        Format("📝 <b>{title}</b>\n{description}\n{time_limit}\n❓ {q_count} питань"),
        Button(Format("{btn_label}"), id="start_quiz", on_click=on_start_quiz),
        Button(Const("← Назад"), id="back_list", on_click=_back(StudentQuizSG.quiz_list)),
        state=StudentQuizSG.quiz_intro,
        getter=get_quiz_intro,
    ),
    Window(
        Format("Питання {q_num} з {q_total}\n\n<b>{q_text}</b>"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="single_sel",
                item_id_getter=lambda x: x[0],
                items="single_options",
                on_click=on_single_answer,
                when="is_single",
            ),
            id="single_sg", width=1, height=6, when="is_single",
        ),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="multi_sel",
                item_id_getter=lambda x: x[0],
                items="multi_options",
                on_click=on_multi_toggle,
                when="is_multi",
            ),
            id="multi_sg", width=1, height=5, when="is_multi",
        ),
        Button(
            Const("✅ Підтвердити вибір"), id="multi_confirm",
            on_click=on_multi_confirm,
            when="is_multi",
        ),
        TextInput(id="text_answer", on_success=on_text_answer),
        state=StudentQuizSG.question_step,
        getter=get_question_step,
    ),
    Window(
        Format("✅ Тест завершено!\n\n🏆 Результат: {score}/{max_score} балів ({pct}%){elapsed}"),
        Button(Const("📋 Переглянути відповіді"), id="view_review", on_click=on_view_review),
        Button(Const("🏠 До списку тестів"), id="back_list2", on_click=_back(StudentQuizSG.quiz_list)),
        state=StudentQuizSG.quiz_done,
        getter=get_quiz_done,
    ),
    Window(
        Format("📋 Мої відповіді:\n\n{review_text}"),
        Button(Const("← Назад"), id="back_done", on_click=_back(StudentQuizSG.quiz_done)),
        state=StudentQuizSG.answer_review,
        getter=get_answer_review,
    ),
)
