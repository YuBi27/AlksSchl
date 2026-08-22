from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

KYIV_TZ = ZoneInfo("Europe/Kyiv")


class TeacherLessonSG(StatesGroup):
    list_groups = State()
    lesson_list = State()
    lesson_card = State()
    attendance = State()
    attendance_status = State()
    lesson_note = State()


STATUS_LABELS = {
    "present": "✅ Присутній",
    "late": "🕐 Запізнення",
    "absent": "❌ Відсутній",
    "excused": "📋 Поважна",
    None: "— Не вказано",
}


def _teacher_id(manager: DialogManager) -> int:
    return (
        manager.dialog_data.get("teacher_override_id")
        or manager.middleware_data["user_data"]["id"]
    )


async def on_start(start_data: dict, manager: DialogManager) -> None:
    if isinstance(start_data, dict) and "teacher_override_id" in start_data:
        manager.dialog_data["teacher_override_id"] = start_data["teacher_override_id"]


def _trunc(text: str, max_len: int = 58) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


async def get_groups(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    teacher_id = _teacher_id(dialog_manager)
    own = await api_client.get_groups(teacher_id=teacher_id)
    all_g = await api_client.get_groups()
    seen = {g["id"] for g in own}
    groups = own + [g for g in all_g if g["id"] not in seen and g.get("teacher_id") is None]
    items = [(str(g["id"]), _trunc(g["name"])) for g in groups]
    return {"groups": items}


async def on_group_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["group_id"] = int(item_id)
    await manager.switch_to(TeacherLessonSG.lesson_list)


async def get_lessons(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("group_id", 0)
    now = datetime.now(tz=timezone.utc)
    from_dt = (now - timedelta(days=7)).isoformat()
    to_dt = (now + timedelta(days=7)).isoformat()
    lessons = await api_client.get_lessons(group_id=group_id, from_dt=from_dt, to_dt=to_dt)
    items = []
    for l in sorted(lessons, key=lambda x: x["scheduled_at"]):
        dt = datetime.fromisoformat(l["scheduled_at"]).astimezone(KYIV_TZ)
        label = dt.strftime("%d.%m %H:%M")
        items.append((str(l["id"]), label))
    return {"lessons": items}


async def on_lesson_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["lesson_id"] = int(item_id)
    await manager.switch_to(TeacherLessonSG.lesson_card)


async def get_lesson_card(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    lesson_id = dialog_manager.dialog_data.get("lesson_id", 0)
    attendances = await api_client.get_attendances(lesson_id=lesson_id)
    counts = {"present": 0, "late": 0, "absent": 0, "excused": 0}
    for a in attendances:
        if a["status"] in counts:
            counts[a["status"]] += 1
    summary = f"✅ {counts['present']} / 🕐 {counts['late']} / ❌ {counts['absent']} / 📋 {counts['excused']}"
    return {"attendance_summary": summary}


async def on_attendance_click(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(TeacherLessonSG.attendance)


async def on_lesson_note_click(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(TeacherLessonSG.lesson_note)


async def get_attendance_students(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    lesson_id = dialog_manager.dialog_data.get("lesson_id", 0)
    group_id = dialog_manager.dialog_data.get("group_id", 0)
    students = await api_client.get_group_students(group_id)
    attendances = await api_client.get_attendances(lesson_id=lesson_id)
    att_map = {a["student_user_id"]: a["status"] for a in attendances}
    items = []
    for s in students:
        uid = s["id"]
        status = att_map.get(uid)
        name = s.get("full_name") or f"Учень #{uid}"
        label = _trunc(f"{name} — {STATUS_LABELS.get(status, '— ?')}")
        items.append((str(uid), label))
    return {"students": items}


async def on_student_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["attendance_student_id"] = int(item_id)
    await manager.switch_to(TeacherLessonSG.attendance_status)


async def on_status_present(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _save_attendance(callback, manager, "present")


async def on_status_late(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _save_attendance(callback, manager, "late")


async def on_status_absent(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _save_attendance(callback, manager, "absent")


async def on_status_excused(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _save_attendance(callback, manager, "excused")


async def _save_attendance(callback: CallbackQuery, manager: DialogManager, status: str) -> None:
    api_client = manager.middleware_data["api_client"]
    lesson_id = manager.dialog_data.get("lesson_id", 0)
    student_id = manager.dialog_data.get("attendance_student_id", 0)
    await api_client.upsert_attendance(lesson_id, student_id, status)
    await callback.answer("✅ Збережено")
    await manager.switch_to(TeacherLessonSG.attendance)


async def on_lesson_note_submitted(
    message: Message, widget: Any, manager: DialogManager, text: str
) -> None:
    api_client = manager.middleware_data["api_client"]
    teacher_id = _teacher_id(manager)
    lesson_id = manager.dialog_data.get("lesson_id", 0)
    await api_client.create_teacher_note({
        "teacher_id": teacher_id,
        "lesson_id": lesson_id,
        "text": text,
    })
    await message.answer("✅ Коментар збережено.")
    await manager.switch_to(TeacherLessonSG.lesson_card)


dialog = Dialog(
    Window(
        Const("📋 Оберіть групу:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="groups_select",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_selected,
            ),
            id="groups_scroll",
            width=1,
            height=7,
        ),
        state=TeacherLessonSG.list_groups,
        getter=get_groups,
    ),
    Window(
        Const("📅 Оберіть заняття:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="lessons_select",
                item_id_getter=lambda x: x[0],
                items="lessons",
                on_click=on_lesson_selected,
            ),
            id="lessons_scroll",
            width=1,
            height=7,
        ),
        Button(Const("← Назад"), id="btn_back_groups", on_click=lambda c, b, m: m.switch_to(TeacherLessonSG.list_groups)),
        state=TeacherLessonSG.lesson_list,
        getter=get_lessons,
    ),
    Window(
        Format("Заняття\n\n{attendance_summary}"),
        Row(
            Button(Const("✅ Відвідуваність"), id="btn_attendance", on_click=on_attendance_click),
            Button(Const("💬 Коментар"), id="btn_lesson_note", on_click=on_lesson_note_click),
        ),
        Button(Const("← Назад"), id="btn_back_lessons", on_click=lambda c, b, m: m.switch_to(TeacherLessonSG.lesson_list)),
        state=TeacherLessonSG.lesson_card,
        getter=get_lesson_card,
    ),
    Window(
        Const("👥 Оберіть учня:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="att_students",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=on_student_selected,
            ),
            id="att_students_scroll",
            width=1,
            height=7,
        ),
        Button(Const("← Назад"), id="btn_back_card", on_click=lambda c, b, m: m.switch_to(TeacherLessonSG.lesson_card)),
        state=TeacherLessonSG.attendance,
        getter=get_attendance_students,
    ),
    Window(
        Const("Оберіть статус:"),
        Button(Const("✅ Присутній"), id="btn_present", on_click=on_status_present),
        Button(Const("🕐 Запізнення"), id="btn_late", on_click=on_status_late),
        Button(Const("❌ Відсутній"), id="btn_absent", on_click=on_status_absent),
        Button(Const("📋 Поважна"), id="btn_excused", on_click=on_status_excused),
        state=TeacherLessonSG.attendance_status,
    ),
    Window(
        Const("💬 Введіть коментар до заняття:"),
        TextInput(id="lesson_note_input", on_success=on_lesson_note_submitted),
        Button(Const("← Назад"), id="btn_back_lesson_card", on_click=lambda c, b, m: m.switch_to(TeacherLessonSG.lesson_card)),
        state=TeacherLessonSG.lesson_note,
    ),
    on_start=on_start,
)
