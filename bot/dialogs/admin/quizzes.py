from typing import Any, Optional
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ContentType, BufferedInputFile
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput


def _trunc(text: str, max_len: int = 50) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


class AdminQuizSG(StatesGroup):
    quiz_list = State()
    quiz_detail = State()
    enter_title = State()
    enter_description = State()
    enter_time_limit = State()
    question_list = State()
    select_qtype = State()
    enter_qtext = State()
    enter_options = State()
    mark_correct = State()
    assign_target = State()
    assign_group = State()
    assign_student = State()
    assign_deadline = State()
    assign_confirm = State()
    results_list = State()
    result_detail = State()
    import_upload = State()
    import_confirm = State()


def _creator_id(manager: DialogManager) -> int:
    return manager.middleware_data["user_data"]["id"]


# ---- Getters ----

async def get_quiz_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    creator_id = _creator_id(dialog_manager)
    quizzes = await api_client.list_quizzes(creator_id=creator_id)
    items = [
        (str(q["id"]), _trunc(f"📝 {q['title']} ({len(q.get('questions', []))} пит.)"))
        for q in quizzes
    ]
    return {"quizzes": items}


async def get_quiz_detail(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    quiz_id = dialog_manager.dialog_data.get("quiz_id")
    quiz = await api_client.get_quiz(quiz_id)
    return {
        "title": quiz["title"],
        "description": quiz.get("description") or "—",
        "time_limit": f"{quiz['time_limit_min']} хв" if quiz.get("time_limit_min") else "Без ліміту",
        "q_count": len(quiz.get("questions", [])),
        "quiz_id": quiz_id,
    }


async def get_question_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    quiz_id = dialog_manager.dialog_data.get("quiz_id")
    quiz = await api_client.get_quiz(quiz_id)
    type_icon = {"single": "🔘", "multi": "☑️", "text": "✏️"}
    items = [
        (str(i), _trunc(f"{type_icon.get(q['question_type'], '?')} {q['text']}"))
        for i, q in enumerate(quiz.get("questions", []))
    ]
    return {"questions": items}


async def get_enter_options(dialog_manager: DialogManager, **kwargs) -> dict:
    opts = dialog_manager.dialog_data.get("pending_options", [])
    summary = "\n".join(f"{i+1}. {o}" for i, o in enumerate(opts)) or "—"
    return {"entered_count": len(opts), "options_summary": summary, "can_finish": len(opts) >= 2}


async def get_mark_correct(dialog_manager: DialogManager, **kwargs) -> dict:
    opts = dialog_manager.dialog_data.get("pending_options", [])
    correct = dialog_manager.dialog_data.get("correct_indices", [])
    items = [(str(i), ("✅ " if i in correct else "⬜ ") + o) for i, o in enumerate(opts)]
    return {"options": items, "can_save": len(correct) > 0}


async def get_assign_groups(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    groups = await api_client.get_groups()
    items = [(str(g["id"]), _trunc(g["name"])) for g in groups]
    return {"groups": items}


async def get_assign_students(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    students = await api_client.get_students()
    items = [
        (str(s["id"]), _trunc(s.get("full_name") or s.get("username") or f"ID {s['id']}"))
        for s in students
    ]
    return {"students": items}


async def get_assign_confirm(dialog_manager: DialogManager, **kwargs) -> dict:
    dd = dialog_manager.dialog_data
    target = dd.get("assign_target_name", "—")
    deadline = dd.get("assign_deadline_str") or "Без дедлайну"
    return {"assign_target": target, "assign_deadline": deadline}


async def get_results_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    quiz_id = dialog_manager.dialog_data.get("quiz_id")
    results = await api_client.list_quiz_results(quiz_id=quiz_id)
    items = []
    for i, r in enumerate(results):
        name = r.get("student_name") or f"Учень #{r['student_user_id']}"
        score_str = f"{r['score']:.0f}/{r['max_score']:.0f}"
        items.append((str(i), _trunc(f"{name} — {score_str}")))
    dialog_manager.dialog_data["results_cache"] = results
    return {"results": items}


async def get_result_detail(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    attempt_id = dialog_manager.dialog_data.get("result_attempt_id")
    attempt = await api_client.get_quiz_attempt(attempt_id)
    quiz = await api_client.get_quiz(attempt["quiz_id"])
    q_map = {q["id"]: q for q in quiz["questions"]}
    lines = []
    for ans in attempt.get("answers", []):
        q = q_map.get(ans["question_id"], {})
        q_text = (q.get("text") or "")[:40]
        if q.get("question_type") == "text":
            detail = f"📝 {ans.get('text_answer') or '—'}"
        elif ans.get("is_correct"):
            opt_map = {o["id"]: o["text"] for o in q.get("options", [])}
            detail = "✅ " + ", ".join(opt_map.get(i, str(i)) for i in ans.get("selected_options", []))
        else:
            opt_map = {o["id"]: o["text"] for o in q.get("options", [])}
            detail = "❌ " + ", ".join(opt_map.get(i, str(i)) for i in ans.get("selected_options", []))
        lines.append(f"{q_text}:\n  {detail}")
    return {"detail_text": "\n\n".join(lines) or "Немає відповідей"}


async def get_import_confirm(dialog_manager: DialogManager, **kwargs) -> dict:
    parsed = dialog_manager.dialog_data.get("parsed_quiz", {})
    meta = parsed.get("metadata", {})
    questions = parsed.get("questions", [])
    errors = parsed.get("errors", [])
    errors_text = ("\n⚠️ " + "\n⚠️ ".join(errors)) if errors else ""
    return {
        "quiz_title": meta.get("title", "—"),
        "q_count": len(questions),
        "errors_text": errors_text,
    }


# ---- Handlers ----

async def on_quiz_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    manager.dialog_data["quiz_id"] = int(item_id)
    await manager.switch_to(AdminQuizSG.quiz_detail)


async def on_new_quiz(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data.pop("quiz_id", None)
    await manager.switch_to(AdminQuizSG.enter_title)


async def on_title_entered(message: Message, widget: Any, manager: DialogManager, value: str) -> None:
    manager.dialog_data["quiz_title"] = value.strip()
    await manager.switch_to(AdminQuizSG.enter_description)


async def on_description_entered(message: Message, widget: Any, manager: DialogManager, value: str) -> None:
    manager.dialog_data["quiz_description"] = value.strip()
    await manager.switch_to(AdminQuizSG.enter_time_limit)


async def on_skip_description(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["quiz_description"] = None
    await manager.switch_to(AdminQuizSG.enter_time_limit)


async def on_time_limit_entered(message: Message, widget: Any, manager: DialogManager, value: str) -> None:
    try:
        manager.dialog_data["quiz_time_limit"] = int(value.strip())
    except ValueError:
        await message.answer("⚠️ Введіть ціле число хвилин, наприклад: 30")
        return
    await _create_quiz_and_go_to_questions(manager)


async def on_no_time_limit(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["quiz_time_limit"] = None
    await _create_quiz_and_go_to_questions(manager)


async def _create_quiz_and_go_to_questions(manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    quiz = await api_client.create_quiz(
        title=manager.dialog_data["quiz_title"],
        creator_id=_creator_id(manager),
        description=manager.dialog_data.get("quiz_description"),
        time_limit_min=manager.dialog_data.get("quiz_time_limit"),
    )
    manager.dialog_data["quiz_id"] = quiz["id"]
    await manager.switch_to(AdminQuizSG.question_list)


async def on_add_question(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["pending_options"] = []
    manager.dialog_data["correct_indices"] = []
    manager.dialog_data["question_text"] = ""
    await manager.switch_to(AdminQuizSG.select_qtype)


async def on_qtype_single(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["question_type"] = "single"
    await manager.switch_to(AdminQuizSG.enter_qtext)


async def on_qtype_multi(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["question_type"] = "multi"
    await manager.switch_to(AdminQuizSG.enter_qtext)


async def on_qtype_text(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["question_type"] = "text"
    await manager.switch_to(AdminQuizSG.enter_qtext)


async def on_qtext_entered(message: Message, widget: Any, manager: DialogManager, value: str) -> None:
    manager.dialog_data["question_text"] = value.strip()
    if manager.dialog_data.get("question_type") == "text":
        await _save_question(manager)
    else:
        await manager.switch_to(AdminQuizSG.enter_options)


async def on_option_entered(message: Message, widget: Any, manager: DialogManager, value: str) -> None:
    opts = manager.dialog_data.get("pending_options", [])
    opts.append(value.strip())
    manager.dialog_data["pending_options"] = opts


async def on_options_done(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminQuizSG.mark_correct)


async def on_option_toggle(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    q_type = manager.dialog_data.get("question_type", "single")
    idx = int(item_id)
    if q_type == "single":
        manager.dialog_data["correct_indices"] = [idx]
    else:
        selected = manager.dialog_data.get("correct_indices", [])
        if idx in selected:
            selected.remove(idx)
        else:
            selected.append(idx)
        manager.dialog_data["correct_indices"] = selected


async def on_save_question(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _save_question(manager)


async def _save_question(manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    quiz_id = manager.dialog_data["quiz_id"]
    q_type = manager.dialog_data["question_type"]
    q_text = manager.dialog_data["question_text"]

    quiz = await api_client.get_quiz(quiz_id)
    order_idx = len(quiz.get("questions", []))

    if q_type == "text":
        options: list[dict] = []
    else:
        pending = manager.dialog_data.get("pending_options", [])
        correct = manager.dialog_data.get("correct_indices", [])
        options = [{"text": t, "is_correct": i in correct} for i, t in enumerate(pending)]

    await api_client.add_quiz_question(
        quiz_id=quiz_id,
        order_idx=order_idx,
        question_type=q_type,
        text=q_text,
        options=options,
    )
    manager.dialog_data["pending_options"] = []
    manager.dialog_data["correct_indices"] = []
    await manager.switch_to(AdminQuizSG.question_list)


async def on_delete_quiz(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    quiz_id = manager.dialog_data.get("quiz_id")
    await api_client.delete_quiz(quiz_id)
    await manager.switch_to(AdminQuizSG.quiz_list)


async def on_assign(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminQuizSG.assign_target)


async def on_assign_to_group(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["assign_type"] = "group"
    await manager.switch_to(AdminQuizSG.assign_group)


async def on_assign_to_student(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["assign_type"] = "student"
    await manager.switch_to(AdminQuizSG.assign_student)


async def on_group_picked(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    api_client = manager.middleware_data["api_client"]
    groups = await api_client.get_groups()
    g = next((g for g in groups if str(g["id"]) == item_id), None)
    manager.dialog_data["assign_target_id"] = int(item_id)
    manager.dialog_data["assign_target_name"] = g["name"] if g else item_id
    await manager.switch_to(AdminQuizSG.assign_deadline)


async def on_student_picked(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    api_client = manager.middleware_data["api_client"]
    students = await api_client.get_students()
    s = next((s for s in students if str(s["id"]) == item_id), None)
    manager.dialog_data["assign_target_id"] = int(item_id)
    name = (s.get("full_name") or s.get("username") or item_id) if s else item_id
    manager.dialog_data["assign_target_name"] = name
    await manager.switch_to(AdminQuizSG.assign_deadline)


async def on_deadline_entered(message: Message, widget: Any, manager: DialogManager, value: str) -> None:
    manager.dialog_data["assign_deadline_str"] = value.strip() + "T23:59:59+02:00"
    await manager.switch_to(AdminQuizSG.assign_confirm)


async def on_no_deadline(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["assign_deadline_str"] = None
    await manager.switch_to(AdminQuizSG.assign_confirm)


async def on_confirm_assign(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    dd = manager.dialog_data
    assign_type = dd.get("assign_type")
    target_id = dd.get("assign_target_id")
    await api_client.create_quiz_assignment(
        quiz_id=dd["quiz_id"],
        assigned_by=_creator_id(manager),
        group_id=target_id if assign_type == "group" else None,
        student_user_id=target_id if assign_type == "student" else None,
        deadline=dd.get("assign_deadline_str"),
    )
    await manager.switch_to(AdminQuizSG.quiz_detail)


async def on_view_results(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminQuizSG.results_list)


async def on_result_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    results = manager.dialog_data.get("results_cache", [])
    idx = int(item_id)
    if idx < len(results):
        manager.dialog_data["result_attempt_id"] = results[idx]["id"]
        await manager.switch_to(AdminQuizSG.result_detail)


async def on_import_excel(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminQuizSG.import_upload)


async def on_download_template(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.services.quiz_import import generate_quiz_template
    xlsx_bytes = generate_quiz_template()
    file = BufferedInputFile(xlsx_bytes, filename="quiz_template.xlsx")
    await callback.message.answer_document(file, caption="📊 Шаблон для завантаження тестів")


async def on_xlsx_received(message: Message, widget: Any, manager: DialogManager) -> None:
    from bot.services.quiz_import import parse_quiz_xlsx
    if not message.document or not (message.document.file_name or "").endswith(".xlsx"):
        await message.answer("⚠️ Будь ласка, завантажте файл у форматі .xlsx")
        return
    file_info = await message.bot.get_file(message.document.file_id)
    buf = await message.bot.download_file(file_info.file_path)
    xlsx_bytes = buf.read() if hasattr(buf, "read") else bytes(buf)
    meta, questions, errors = parse_quiz_xlsx(xlsx_bytes)
    manager.dialog_data["parsed_quiz"] = {"metadata": meta, "questions": questions, "errors": errors}
    await manager.switch_to(AdminQuizSG.import_confirm)


async def on_save_imported(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    parsed = manager.dialog_data.get("parsed_quiz", {})
    meta = parsed.get("metadata", {})
    questions = parsed.get("questions", [])
    quiz = await api_client.create_quiz(
        title=meta.get("title", "Без назви"),
        creator_id=_creator_id(manager),
        description=meta.get("description"),
        time_limit_min=meta.get("time_limit_min"),
        shuffle_questions=meta.get("shuffle_questions", False),
    )
    for i, q in enumerate(questions):
        await api_client.add_quiz_question(
            quiz_id=quiz["id"],
            order_idx=i,
            question_type=q["type"],
            text=q["text"],
            options=q["options"],
        )
    manager.dialog_data["quiz_id"] = quiz["id"]
    await manager.switch_to(AdminQuizSG.quiz_detail)


def _back(state: State):
    async def handler(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
        await manager.switch_to(state)
    return handler


# ---- Dialog ----

dialog = Dialog(
    Window(
        Const("📝 Тести\n\nОберіть тест або створіть новий:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="quiz_sel",
                item_id_getter=lambda x: x[0],
                items="quizzes",
                on_click=on_quiz_selected,
            ),
            id="quizzes_sg", width=1, height=7,
        ),
        Row(
            Button(Const("➕ Новий тест"), id="new_quiz", on_click=on_new_quiz),
            Button(Const("📥 Імпорт Excel"), id="import_excel", on_click=on_import_excel),
        ),
        state=AdminQuizSG.quiz_list,
        getter=get_quiz_list,
    ),
    Window(
        Format("📝 <b>{title}</b>\n📄 {description}\n⏱ {time_limit}\n❓ {q_count} питань"),
        Button(Const("❓ Питання"), id="btn_questions", on_click=_back(AdminQuizSG.question_list)),
        Button(Const("📤 Призначити"), id="btn_assign", on_click=on_assign),
        Button(Const("📊 Результати"), id="btn_results", on_click=on_view_results),
        Button(Const("🗑 Видалити"), id="btn_del_quiz", on_click=on_delete_quiz),
        Button(Const("← Назад"), id="back_to_list", on_click=_back(AdminQuizSG.quiz_list)),
        state=AdminQuizSG.quiz_detail,
        getter=get_quiz_detail,
    ),
    Window(
        Const("📝 Введіть назву тесту:"),
        TextInput(id="title_input", on_success=on_title_entered),
        Button(Const("← Скасувати"), id="cancel_title", on_click=_back(AdminQuizSG.quiz_list)),
        state=AdminQuizSG.enter_title,
    ),
    Window(
        Const("📄 Введіть опис тесту (або пропустіть):"),
        TextInput(id="desc_input", on_success=on_description_entered),
        Button(Const("⏭ Пропустити"), id="skip_desc", on_click=on_skip_description),
        state=AdminQuizSG.enter_description,
    ),
    Window(
        Const("⏱ Введіть час на тест у хвилинах (або без ліміту):"),
        TextInput(id="time_input", on_success=on_time_limit_entered),
        Button(Const("∞ Без ліміту"), id="no_limit", on_click=on_no_time_limit),
        state=AdminQuizSG.enter_time_limit,
    ),
    Window(
        Const("❓ Питання тесту:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="q_sel",
                item_id_getter=lambda x: x[0],
                items="questions",
                on_click=lambda c, w, m, i: None,
            ),
            id="questions_sg", width=1, height=6,
        ),
        Row(
            Button(Const("➕ Додати питання"), id="add_q", on_click=on_add_question),
            Button(Const("← Тест"), id="back_detail", on_click=_back(AdminQuizSG.quiz_detail)),
        ),
        state=AdminQuizSG.question_list,
        getter=get_question_list,
    ),
    Window(
        Const("Оберіть тип питання:"),
        Button(Const("🔘 Один варіант (Single)"), id="q_single", on_click=on_qtype_single),
        Button(Const("☑️ Декілька варіантів (Multi)"), id="q_multi", on_click=on_qtype_multi),
        Button(Const("✏️ Текстова відповідь"), id="q_text", on_click=on_qtype_text),
        Button(Const("← Назад"), id="back_qlist", on_click=_back(AdminQuizSG.question_list)),
        state=AdminQuizSG.select_qtype,
    ),
    Window(
        Const("✏️ Введіть текст питання:"),
        TextInput(id="qtext_input", on_success=on_qtext_entered),
        Button(Const("← Назад"), id="back_qtype", on_click=_back(AdminQuizSG.select_qtype)),
        state=AdminQuizSG.enter_qtext,
    ),
    Window(
        Format("📋 Введені варіанти ({entered_count}):\n{options_summary}\n\nВведіть наступний варіант або натисніть «Готово»:"),
        TextInput(id="opt_input", on_success=on_option_entered),
        Button(Const("✅ Готово"), id="opts_done", on_click=on_options_done, when="can_finish"),
        Button(Const("← Назад"), id="back_qtext2", on_click=_back(AdminQuizSG.enter_qtext)),
        state=AdminQuizSG.enter_options,
        getter=get_enter_options,
    ),
    Window(
        Const("Відмітьте правильні варіанти:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="correct_sel",
                item_id_getter=lambda x: x[0],
                items="options",
                on_click=on_option_toggle,
            ),
            id="correct_sg", width=1, height=6,
        ),
        Button(Const("💾 Зберегти питання"), id="save_q", on_click=on_save_question, when="can_save"),
        Button(Const("← Назад"), id="back_opts", on_click=_back(AdminQuizSG.enter_options)),
        state=AdminQuizSG.mark_correct,
        getter=get_mark_correct,
    ),
    Window(
        Const("Призначити тест:"),
        Button(Const("🏫 Групі"), id="assign_group_btn", on_click=on_assign_to_group),
        Button(Const("👤 Студенту"), id="assign_student_btn", on_click=on_assign_to_student),
        Button(Const("← Назад"), id="back_detail2", on_click=_back(AdminQuizSG.quiz_detail)),
        state=AdminQuizSG.assign_target,
    ),
    Window(
        Const("Оберіть групу:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="grp_sel",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_picked,
            ),
            id="groups_sg", width=1, height=7,
        ),
        Button(Const("← Назад"), id="back_assign", on_click=_back(AdminQuizSG.assign_target)),
        state=AdminQuizSG.assign_group,
        getter=get_assign_groups,
    ),
    Window(
        Const("Оберіть студента:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="stu_sel",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=on_student_picked,
            ),
            id="students_sg", width=1, height=7,
        ),
        Button(Const("← Назад"), id="back_assign2", on_click=_back(AdminQuizSG.assign_target)),
        state=AdminQuizSG.assign_student,
        getter=get_assign_students,
    ),
    Window(
        Const("📅 Введіть дедлайн (YYYY-MM-DD) або пропустіть:"),
        TextInput(id="deadline_input", on_success=on_deadline_entered),
        Button(Const("∞ Без дедлайну"), id="no_deadline", on_click=on_no_deadline),
        state=AdminQuizSG.assign_deadline,
    ),
    Window(
        Format("📤 Призначити тест\n\nКому: {assign_target}\nДедлайн: {assign_deadline}\n\nПідтвердити?"),
        Row(
            Button(Const("✅ Так"), id="confirm_assign", on_click=on_confirm_assign),
            Button(Const("← Скасувати"), id="cancel_assign", on_click=_back(AdminQuizSG.quiz_detail)),
        ),
        state=AdminQuizSG.assign_confirm,
        getter=get_assign_confirm,
    ),
    Window(
        Const("📊 Результати тесту:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="res_sel",
                item_id_getter=lambda x: x[0],
                items="results",
                on_click=on_result_selected,
            ),
            id="results_sg", width=1, height=7,
        ),
        Button(Const("← Назад"), id="back_detail3", on_click=_back(AdminQuizSG.quiz_detail)),
        state=AdminQuizSG.results_list,
        getter=get_results_list,
    ),
    Window(
        Format("📋 Відповіді студента:\n\n{detail_text}"),
        Button(Const("← Назад"), id="back_results", on_click=_back(AdminQuizSG.results_list)),
        state=AdminQuizSG.result_detail,
        getter=get_result_detail,
    ),
    Window(
        Const("📥 Імпорт тесту з Excel\n\nЗавантажте .xlsx файл або спочатку отримайте шаблон:"),
        Button(Const("📄 Завантажити шаблон"), id="dl_template", on_click=on_download_template),
        MessageInput(on_xlsx_received, content_types=[ContentType.DOCUMENT]),
        Button(Const("← Назад"), id="back_list2", on_click=_back(AdminQuizSG.quiz_list)),
        state=AdminQuizSG.import_upload,
    ),
    Window(
        Format("📊 Знайдено <b>{q_count}</b> питань\n📝 Назва: <b>{quiz_title}</b>{errors_text}\n\nЗберегти тест?"),
        Button(Const("✅ Зберегти"), id="save_import", on_click=on_save_imported),
        Button(Const("← Скасувати"), id="cancel_import", on_click=_back(AdminQuizSG.import_upload)),
        state=AdminQuizSG.import_confirm,
        getter=get_import_confirm,
    ),
)
