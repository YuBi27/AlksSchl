from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput


class TeacherStudentSG(StatesGroup):
    student_list = State()
    student_card = State()
    student_note = State()


def _teacher_id(manager: DialogManager) -> int:
    return (
        manager.dialog_data.get("teacher_override_id")
        or manager.middleware_data["user_data"]["id"]
    )


async def on_start(start_data: dict, manager: DialogManager) -> None:
    if isinstance(start_data, dict) and "teacher_override_id" in start_data:
        manager.dialog_data["teacher_override_id"] = start_data["teacher_override_id"]


async def get_students(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    students = await api_client.get_students(status="active")
    items = [(str(s["id"]), s.get("full_name") or f"Учень #{s['id']}") for s in students]
    return {"students": items}


async def on_student_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["student_id"] = int(item_id)
    await manager.switch_to(TeacherStudentSG.student_card)


async def get_student_card(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    student_id = dialog_manager.dialog_data.get("student_id", 0)
    student = await api_client.get_student(student_id)
    attendances = await api_client.get_attendances(student_user_id=student_id)
    att_sorted = sorted(attendances, key=lambda a: a.get("created_at", ""), reverse=True)[:5]
    status_emoji = {"present": "✅", "late": "🕐", "absent": "❌", "excused": "📋"}
    att_text = " ".join(status_emoji.get(a["status"], "—") for a in att_sorted) or "—"
    homeworks = await api_client.get_homeworks(student_user_id=student_id)
    grades = []
    for hw in homeworks:
        g = await api_client.get_homework_grades(hw["id"])
        grades.extend(g)
    graded_ids = {g["student_user_id"] for g in grades}
    pending_count = sum(1 for hw in homeworks if student_id not in graded_ids)
    card_text = (
        f"👤 {student['full_name']}\n\n"
        f"Останні відвідування: {att_text}\n"
        f"Невиконані ДЗ: {pending_count}"
    )
    return {"student_card_text": card_text}


async def on_note_click(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(TeacherStudentSG.student_note)


async def on_note_submitted(
    message: Message, widget: Any, manager: DialogManager, text: str
) -> None:
    api_client = manager.middleware_data["api_client"]
    teacher_id = _teacher_id(manager)
    student_id = manager.dialog_data.get("student_id", 0)
    await api_client.create_teacher_note({
        "teacher_id": teacher_id,
        "student_user_id": student_id,
        "text": text,
    })
    await message.answer("✅ Нотатку збережено.")
    await manager.switch_to(TeacherStudentSG.student_card)


dialog = Dialog(
    Window(
        Const("👤 Оберіть учня:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="student_select",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=on_student_selected,
            ),
            id="student_scroll",
            width=1,
            height=7,
        ),
        state=TeacherStudentSG.student_list,
        getter=get_students,
    ),
    Window(
        Format("{student_card_text}"),
        Button(Const("💬 Нотатка"), id="btn_note", on_click=on_note_click),
        Button(Const("← Назад"), id="btn_back_list", on_click=lambda c, b, m: m.switch_to(TeacherStudentSG.student_list)),
        state=TeacherStudentSG.student_card,
        getter=get_student_card,
    ),
    Window(
        Const("💬 Введіть нотатку про учня:"),
        TextInput(id="note_input", on_success=on_note_submitted),
        Button(Const("← Назад"), id="btn_back_card", on_click=lambda c, b, m: m.switch_to(TeacherStudentSG.student_card)),
        state=TeacherStudentSG.student_note,
    ),
    on_start=on_start,
)
