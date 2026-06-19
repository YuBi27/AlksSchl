from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput


class TeacherGroupSG(StatesGroup):
    list_view = State()
    group_card = State()
    edit_name = State()
    edit_level = State()
    edit_desc = State()
    group_students = State()
    add_student = State()


LEVELS = [
    ("novice", "Новачок"),
    ("A1", "A1"),
    ("A2", "A2"),
    ("B1", "B1"),
    ("B2", "B2"),
    ("C1", "C1"),
    ("C2", "C2"),
]


def _trunc(text: str, max_len: int = 58) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def _teacher_id(manager: DialogManager) -> int | None:
    override = manager.dialog_data.get("teacher_override_id")
    if override:
        return override
    # Admin in their own teacher panel sees all groups (no filter)
    if manager.middleware_data["user_data"]["role"] == "admin":
        return None
    return manager.middleware_data["user_data"]["id"]


async def on_start(start_data: dict, manager: DialogManager) -> None:
    if isinstance(start_data, dict) and "teacher_override_id" in start_data:
        manager.dialog_data["teacher_override_id"] = start_data["teacher_override_id"]


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.teacher.menu import TeacherMenuSG
    override_id = manager.dialog_data.get("teacher_override_id")
    data = {"teacher_override_id": override_id} if override_id else {}
    await manager.start(TeacherMenuSG.main, mode=StartMode.RESET_STACK, data=data)


async def get_groups_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    teacher_id = _teacher_id(dialog_manager)
    groups = await api_client.get_groups(teacher_id=teacher_id)
    items = [
        (str(g["id"]), _trunc(f"{g['name']} ({g.get('level') or '—'}, {g['student_count']} учнів)"))
        for g in groups
    ]
    return {"groups": items, "count": len(groups)}


async def on_select_group(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["selected_group_id"] = int(item_id)
    await manager.switch_to(TeacherGroupSG.group_card)


async def on_new_group(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data.pop("selected_group_id", None)
    manager.dialog_data.pop("edit_name", None)
    manager.dialog_data.pop("edit_level", None)
    manager.dialog_data.pop("edit_desc", None)
    await manager.switch_to(TeacherGroupSG.edit_name)


async def get_group_card(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("selected_group_id", 0)
    group = await api_client.get_group(group_id)
    return {
        "group_name": group.get("name", "—"),
        "level": group.get("level") or "Не вказано",
        "description": group.get("description") or "—",
        "student_count": group.get("student_count", 0),
    }


async def on_edit_group(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    group_id = manager.dialog_data["selected_group_id"]
    group = await api_client.get_group(group_id)
    manager.dialog_data["edit_name"] = group["name"]
    manager.dialog_data["edit_level"] = group.get("level")
    manager.dialog_data["edit_desc"] = group.get("description")
    await manager.switch_to(TeacherGroupSG.edit_name)


async def on_view_students(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(TeacherGroupSG.group_students)


async def get_levels(**kwargs) -> dict:
    return {"levels": LEVELS}


async def on_delete_group(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    group_id = manager.dialog_data["selected_group_id"]
    await api_client.delete_group(group_id)
    await callback.answer("✅ Групу видалено")
    await callback.message.answer("✅ Групу видалено")
    await manager.switch_to(TeacherGroupSG.list_view)


async def on_name_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    manager.dialog_data["edit_name"] = value.strip()
    await manager.switch_to(TeacherGroupSG.edit_level)


async def on_level_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["edit_level"] = item_id
    await manager.switch_to(TeacherGroupSG.edit_desc)


async def on_desc_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    manager.dialog_data["edit_desc"] = value.strip()
    await _save_group(manager, message.answer)


async def on_skip_desc(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["edit_desc"] = None
    await _save_group(manager, callback.message.answer)


async def _save_group(manager: DialogManager, answer=None) -> None:
    api_client = manager.middleware_data["api_client"]
    teacher_id = _teacher_id(manager)
    name = manager.dialog_data["edit_name"]
    level = manager.dialog_data.get("edit_level")
    desc = manager.dialog_data.get("edit_desc")
    group_id = manager.dialog_data.get("selected_group_id")

    if group_id:
        await api_client.update_group(group_id, name=name, level=level, description=desc)
        msg = f"✅ Групу <b>{name}</b> оновлено"
    else:
        group = await api_client.create_group(name, level, desc, teacher_id=teacher_id)
        manager.dialog_data["selected_group_id"] = group["id"]
        msg = f"✅ Групу <b>{name}</b> створено"

    if answer:
        try:
            await answer(msg, parse_mode="HTML")
        except Exception:
            pass

    await manager.switch_to(TeacherGroupSG.group_card)


async def get_group_students(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("selected_group_id", 0)
    students = await api_client.get_group_students(group_id, limit=50)
    items = []
    for s in students:
        name = s.get("full_name") or f"Учень #{s['id']}"
        items.append((str(s["id"]), _trunc(f"🗑 {name}")))

    return {"students": items, "count": len(students)}


async def get_all_students_for_add(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("selected_group_id", 0)
    all_students = await api_client.get_students(status="active")
    group_students = await api_client.get_group_students(group_id, limit=100)
    group_ids = {s["id"] for s in group_students}
    items = [
        (str(s["id"]), _trunc(s.get("full_name") or f"Учень #{s['id']}"))
        for s in all_students
        if s["id"] not in group_ids
    ]
    return {"add_students": items}


async def on_add_student_click(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(TeacherGroupSG.add_student)


async def on_student_add_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    api_client = manager.middleware_data["api_client"]
    group_id = manager.dialog_data.get("selected_group_id", 0)
    student_id = int(item_id)
    student = await api_client.get_student(student_id)
    all_groups = await api_client.get_groups()
    name_to_id = {g["name"]: g["id"] for g in all_groups}
    current_ids = [name_to_id[n] for n in student.get("group_names", []) if n in name_to_id]
    new_ids = list(set(current_ids + [group_id]))
    await api_client.set_student_groups(student_id, new_ids)
    await callback.answer("✅ Учня додано до групи")
    await callback.message.answer("✅ Учня додано до групи")
    await manager.switch_to(TeacherGroupSG.group_students)


async def on_remove_student_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    api_client = manager.middleware_data["api_client"]
    group_id = manager.dialog_data.get("selected_group_id", 0)
    await api_client.remove_student_from_group(int(item_id), group_id)
    await callback.answer("✅ Учня видалено з групи")
    await callback.message.answer("✅ Учня видалено з групи")
    await manager.switch_to(TeacherGroupSG.group_students)


dialog = Dialog(
    Window(
        Format("🏫 Мої групи ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="tgrp_sel",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_select_group,
            ),
            id="tgrp_scroll",
            width=1,
            height=8,
        ),
        Button(Const("➕ Нова група"), id="tgrp_new", on_click=on_new_group),
        Button(Const("← Меню"), id="tgrp_back_menu", on_click=on_back_to_menu),
        state=TeacherGroupSG.list_view,
        getter=get_groups_list,
    ),
    Window(
        Format(
            "🏫 {group_name}\n"
            "🎓 Рівень: {level}\n"
            "📝 Опис: {description}\n"
            "👥 Учнів: {student_count}"
        ),
        Row(
            Button(Const("✏️ Редагувати"), id="tgrp_edit", on_click=on_edit_group),
            Button(Const("👥 Учні"), id="tgrp_students", on_click=on_view_students),
        ),
        Row(
            Button(Const("🗑 Видалити"), id="tgrp_del", on_click=on_delete_group),
            Button(Const("← Назад"), id="tgrp_back_list", on_click=lambda c, b, m: m.switch_to(TeacherGroupSG.list_view)),
        ),
        state=TeacherGroupSG.group_card,
        getter=get_group_card,
    ),
    Window(
        Const("✏️ Введіть назву групи:"),
        TextInput(id="tgrp_name_input", on_success=on_name_entered),
        Button(Const("← Назад"), id="tgrp_back_list_n", on_click=lambda c, b, m: m.switch_to(TeacherGroupSG.list_view)),
        state=TeacherGroupSG.edit_name,
    ),
    Window(
        Const("🎓 Оберіть рівень групи:"),
        Select(
            Format("{item[1]}"),
            id="tgrp_level_sel",
            item_id_getter=lambda x: x[0],
            items="levels",
            on_click=on_level_selected,
        ),
        Button(Const("← Назад"), id="tgrp_back_name", on_click=lambda c, b, m: m.switch_to(TeacherGroupSG.edit_name)),
        state=TeacherGroupSG.edit_level,
        getter=get_levels,
    ),
    Window(
        Const("📝 Введіть опис групи (необов'язково):"),
        TextInput(id="tgrp_desc_input", on_success=on_desc_entered),
        Button(Const("⏭ Пропустити"), id="tgrp_skip_desc", on_click=on_skip_desc),
        state=TeacherGroupSG.edit_desc,
    ),
    Window(
        Format("👥 Учні групи ({count}):\n(натисніть 🗑 щоб видалити з групи)"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="tgrp_stud_sel",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=on_remove_student_selected,
            ),
            id="tgrp_stud_scroll",
            width=1,
            height=8,
        ),
        Button(Const("➕ Додати учня"), id="tgrp_add_stud", on_click=on_add_student_click),
        Button(Const("← Назад до групи"), id="tgrp_back_card", on_click=lambda c, b, m: m.switch_to(TeacherGroupSG.group_card)),
        state=TeacherGroupSG.group_students,
        getter=get_group_students,
    ),
    Window(
        Const("👤 Оберіть учня для додавання:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="tgrp_add_sel",
                item_id_getter=lambda x: x[0],
                items="add_students",
                on_click=on_student_add_selected,
            ),
            id="tgrp_add_scroll",
            width=1,
            height=8,
        ),
        Button(Const("← Назад"), id="tgrp_back_students", on_click=lambda c, b, m: m.switch_to(TeacherGroupSG.group_students)),
        state=TeacherGroupSG.add_student,
        getter=get_all_students_for_add,
    ),
    on_start=on_start,
)
