from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

KYIV_TZ = ZoneInfo("Europe/Kyiv")
UTC_TZ = ZoneInfo("UTC")


class TeacherHomeworkSG(StatesGroup):
    hw_list = State()
    hw_target = State()
    hw_pick_group = State()
    hw_pick_student = State()
    hw_title = State()
    hw_description = State()
    hw_due_date = State()
    hw_detail = State()
    hw_grade = State()


def _teacher_id(manager: DialogManager) -> int:
    return (
        manager.dialog_data.get("teacher_override_id")
        or manager.middleware_data["user_data"]["id"]
    )


async def on_start(start_data: dict, manager: DialogManager) -> None:
    if isinstance(start_data, dict) and "teacher_override_id" in start_data:
        manager.dialog_data["teacher_override_id"] = start_data["teacher_override_id"]


async def get_hw_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    teacher_id = _teacher_id(dialog_manager)
    homeworks = await api_client.get_homeworks(teacher_id=teacher_id)
    homeworks_sorted = sorted(homeworks, key=lambda x: x["due_at"])
    items = [(str(h["id"]), f"{h['title']} — {h['due_at'][:10]}") for h in homeworks_sorted]
    return {"homeworks": items}


async def on_new_hw(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(TeacherHomeworkSG.hw_target)


async def on_hw_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["hw_id"] = int(item_id)
    await manager.switch_to(TeacherHomeworkSG.hw_detail)


async def on_target_group(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["hw_for_group"] = True
    await manager.switch_to(TeacherHomeworkSG.hw_pick_group)


async def on_target_student(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["hw_for_group"] = False
    await manager.switch_to(TeacherHomeworkSG.hw_pick_student)


async def get_groups(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    groups = await api_client.get_groups()
    items = [(str(g["id"]), g["name"]) for g in groups]
    return {"groups": items}


async def on_group_picked(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["hw_group_id"] = int(item_id)
    await manager.switch_to(TeacherHomeworkSG.hw_title)


async def get_students(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    students = await api_client.get_students(status="active")
    items = [(str(s["user_id"]), s["full_name"]) for s in students]
    return {"students": items}


async def on_student_picked(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["hw_student_id"] = int(item_id)
    await manager.switch_to(TeacherHomeworkSG.hw_title)


async def on_title_submitted(
    message: Message, widget: Any, manager: DialogManager, text: str
) -> None:
    manager.dialog_data["hw_title"] = text
    await manager.switch_to(TeacherHomeworkSG.hw_description)


async def on_description_submitted(
    message: Message, widget: Any, manager: DialogManager, text: str
) -> None:
    manager.dialog_data["hw_description"] = text
    await manager.switch_to(TeacherHomeworkSG.hw_due_date)


async def on_due_date_submitted(
    message: Message, widget: Any, manager: DialogManager, text: str
) -> None:
    try:
        kyiv_dt = datetime.strptime(text.strip(), "%d.%m.%Y %H:%M").replace(tzinfo=KYIV_TZ)
        utc_dt = kyiv_dt.astimezone(UTC_TZ)
    except ValueError:
        await message.answer("❌ Невірний формат. Введіть дату у форматі ДД.ММ.РРРР ГГ:ХХ")
        return

    api_client = manager.middleware_data["api_client"]
    teacher_id = _teacher_id(manager)
    data = {
        "teacher_id": teacher_id,
        "title": manager.dialog_data["hw_title"],
        "description": manager.dialog_data["hw_description"],
        "due_at": utc_dt.isoformat(),
    }
    if manager.dialog_data.get("hw_for_group"):
        data["group_id"] = manager.dialog_data["hw_group_id"]
    else:
        data["student_user_id"] = manager.dialog_data["hw_student_id"]

    hw = await api_client.create_homework(data)

    # Send notifications
    bot = manager.middleware_data["bot"]
    teacher_profile = await api_client.get_teacher_profile(teacher_id)
    teacher_name = teacher_profile.get("full_name", "Викладач")
    due_kyiv = utc_dt.astimezone(KYIV_TZ).strftime("%d.%m.%Y %H:%M")

    if data.get("group_id"):
        students = await api_client.get_group_students(data["group_id"])
    else:
        raw = await api_client.get_student(data["student_user_id"])
        students = [raw]

    for s in students:
        user = await api_client.get_user(s["user_id"])
        tg_id = user["telegram_id"]
        individual_line = "\n👤 Особисте завдання" if not data.get("group_id") else ""
        text_msg = (
            f"📝 Нове домашнє завдання!{individual_line}\n\n"
            f"📚 {hw['title']}\n"
            f"📋 {hw['description']}\n"
            f"⏰ Здати до: {due_kyiv}\n\n"
            f"Від: {teacher_name}"
        )
        try:
            await bot.send_message(tg_id, text_msg)
        except Exception:
            pass

    await manager.switch_to(TeacherHomeworkSG.hw_list)


async def get_hw_detail(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    hw_id = dialog_manager.dialog_data.get("hw_id", 0)
    hw = await api_client.get_homework(hw_id)
    grades = await api_client.get_homework_grades(hw_id)

    if hw.get("group_id"):
        students = await api_client.get_group_students(hw["group_id"])
    elif hw.get("student_user_id"):
        raw = await api_client.get_student(hw["student_user_id"])
        students = [raw]
    else:
        students = []

    student_lines = []
    for s in students:
        uid = s["user_id"]
        grade = next((g["grade_text"] for g in grades if g["student_user_id"] == uid), None)
        mark = f"✅ {grade}" if grade else "⏳ без оцінки"
        student_lines.append(f"{s['full_name']}: {mark}")

    due_kyiv = datetime.fromisoformat(hw["due_at"]).astimezone(KYIV_TZ).strftime("%d.%m.%Y %H:%M")
    detail_text = (
        f"📚 {hw['title']}\n"
        f"📋 {hw['description']}\n"
        f"⏰ До: {due_kyiv}\n\n"
        + "\n".join(student_lines)
    )
    return {"hw_detail_text": detail_text, "hw_id": hw_id}


async def on_grade_click(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(TeacherHomeworkSG.hw_grade)


async def get_ungraded_students(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    hw_id = dialog_manager.dialog_data.get("hw_id", 0)
    hw = await api_client.get_homework(hw_id)
    grades = await api_client.get_homework_grades(hw_id)
    graded_ids = {g["student_user_id"] for g in grades}

    if hw.get("group_id"):
        students = await api_client.get_group_students(hw["group_id"])
    elif hw.get("student_user_id"):
        raw = await api_client.get_student(hw["student_user_id"])
        students = [raw]
    else:
        students = []

    ungraded = [(str(s["user_id"]), s["full_name"]) for s in students if s["user_id"] not in graded_ids]
    return {"ungraded_students": ungraded}


async def on_grade_student_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["hw_grade_student_id"] = int(item_id)


async def on_grade_text_submitted(
    message: Message, widget: Any, manager: DialogManager, text: str
) -> None:
    api_client = manager.middleware_data["api_client"]
    teacher_id = _teacher_id(manager)
    hw_id = manager.dialog_data.get("hw_id", 0)
    student_id = manager.dialog_data.get("hw_grade_student_id", 0)

    await api_client.upsert_grade(hw_id, {
        "student_user_id": student_id,
        "graded_by": teacher_id,
        "grade_text": text,
    })

    # Notify student
    bot = manager.middleware_data["bot"]
    hw = await api_client.get_homework(hw_id)
    teacher_profile = await api_client.get_teacher_profile(teacher_id)
    teacher_name = teacher_profile.get("full_name", "Викладач")
    student = await api_client.get_student(student_id)
    user = await api_client.get_user(student["user_id"])
    tg_id = user["telegram_id"]
    try:
        await bot.send_message(
            tg_id,
            f"✅ Домашнє завдання оцінено!\n\n"
            f"📚 {hw['title']}\n"
            f"📝 Оцінка: {text}\n\n"
            f"Від: {teacher_name}",
        )
    except Exception:
        pass

    await manager.switch_to(TeacherHomeworkSG.hw_detail)


dialog = Dialog(
    Window(
        Const("📝 Домашні завдання:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="hw_list_select",
                item_id_getter=lambda x: x[0],
                items="homeworks",
                on_click=on_hw_selected,
            ),
            id="hw_list_scroll",
            width=1,
            height=7,
        ),
        Button(Const("➕ Нове ДЗ"), id="btn_new_hw", on_click=on_new_hw),
        state=TeacherHomeworkSG.hw_list,
        getter=get_hw_list,
    ),
    Window(
        Const("Для кого ДЗ?"),
        Button(Const("👥 Для групи"), id="btn_for_group", on_click=on_target_group),
        Button(Const("👤 Для учня"), id="btn_for_student", on_click=on_target_student),
        Button(Const("← Назад"), id="btn_back_hw_list", on_click=lambda c, b, m: m.switch_to(TeacherHomeworkSG.hw_list)),
        state=TeacherHomeworkSG.hw_target,
    ),
    Window(
        Const("Оберіть групу:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="hw_groups",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_picked,
            ),
            id="hw_groups_scroll",
            width=1,
            height=7,
        ),
        Button(Const("← Назад"), id="btn_back_target", on_click=lambda c, b, m: m.switch_to(TeacherHomeworkSG.hw_target)),
        state=TeacherHomeworkSG.hw_pick_group,
        getter=get_groups,
    ),
    Window(
        Const("Оберіть учня:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="hw_students",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=on_student_picked,
            ),
            id="hw_students_scroll",
            width=1,
            height=7,
        ),
        Button(Const("← Назад"), id="btn_back_target2", on_click=lambda c, b, m: m.switch_to(TeacherHomeworkSG.hw_target)),
        state=TeacherHomeworkSG.hw_pick_student,
        getter=get_students,
    ),
    Window(
        Const("📚 Введіть назву ДЗ (макс. 256 символів):"),
        TextInput(id="hw_title_input", on_success=on_title_submitted),
        state=TeacherHomeworkSG.hw_title,
    ),
    Window(
        Const("📋 Введіть опис ДЗ:"),
        TextInput(id="hw_desc_input", on_success=on_description_submitted),
        state=TeacherHomeworkSG.hw_description,
    ),
    Window(
        Const("⏰ Введіть дедлайн (формат: ДД.ММ.РРРР ГГ:ХХ, час — київський):"),
        TextInput(id="hw_due_input", on_success=on_due_date_submitted),
        state=TeacherHomeworkSG.hw_due_date,
    ),
    Window(
        Format("{hw_detail_text}"),
        Button(Const("📝 Виставити оцінку"), id="btn_grade", on_click=on_grade_click),
        Button(Const("← Назад"), id="btn_back_hw_list2", on_click=lambda c, b, m: m.switch_to(TeacherHomeworkSG.hw_list)),
        state=TeacherHomeworkSG.hw_detail,
        getter=get_hw_detail,
    ),
    Window(
        Const("Оберіть учня для оцінки:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="grade_students",
                item_id_getter=lambda x: x[0],
                items="ungraded_students",
                on_click=on_grade_student_selected,
            ),
            id="grade_students_scroll",
            width=1,
            height=7,
        ),
        Const("Введіть оцінку:"),
        TextInput(id="grade_text_input", on_success=on_grade_text_submitted),
        Button(Const("← Назад"), id="btn_back_hw_detail", on_click=lambda c, b, m: m.switch_to(TeacherHomeworkSG.hw_detail)),
        state=TeacherHomeworkSG.hw_grade,
        getter=get_ungraded_students,
    ),
    on_start=on_start,
)
