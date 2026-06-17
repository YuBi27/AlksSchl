from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput


class GroupMgmtSG(StatesGroup):
    list_view = State()
    group_card = State()
    edit_name = State()
    edit_level = State()
    edit_desc = State()
    group_students = State()


LEVELS = [
    ("novice", "Новачок"),
    ("A1", "A1"),
    ("A2", "A2"),
    ("B1", "B1"),
    ("B2", "B2"),
    ("C1", "C1"),
    ("C2", "C2"),
]


async def get_groups_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    groups = await api_client.get_groups()
    items = [
        (str(g["id"]), f"{g['name']} | {g.get('level') or '—'} | {g['student_count']} учнів")
        for g in groups
    ]
    return {"groups": items, "count": len(groups)}


async def on_select_group(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["selected_group_id"] = int(item_id)
    await manager.switch_to(GroupMgmtSG.group_card)


async def on_new_group(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("selected_group_id", None)
    manager.dialog_data.pop("edit_name", None)
    manager.dialog_data.pop("edit_level", None)
    manager.dialog_data.pop("edit_desc", None)
    await manager.switch_to(GroupMgmtSG.edit_name)


async def get_group_card(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("selected_group_id", 0)
    group = await api_client.get_group(group_id)
    return {
        "group_name": group.get("name", "—"),
        "level": group.get("level") or "Не вказано",
        "description": group.get("description") or "—",
        "student_count": group.get("student_count", 0),
        "group_id": group_id,
    }


async def on_edit_group(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    group_id = manager.dialog_data["selected_group_id"]
    group = await api_client.get_group(group_id)
    manager.dialog_data["edit_name"] = group["name"]
    manager.dialog_data["edit_level"] = group.get("level")
    manager.dialog_data["edit_desc"] = group.get("description")
    await manager.switch_to(GroupMgmtSG.edit_name)


async def on_view_students(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(GroupMgmtSG.group_students)


async def on_delete_group(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    group_id = manager.dialog_data["selected_group_id"]
    await api_client.delete_group(group_id)
    await callback.answer("✅ Групу видалено")
    await manager.switch_to(GroupMgmtSG.list_view)


async def on_back_to_list(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(GroupMgmtSG.list_view)


async def on_back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


async def on_name_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    manager.dialog_data["edit_name"] = value.strip()
    await manager.switch_to(GroupMgmtSG.edit_level)


async def on_level_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["edit_level"] = item_id
    await manager.switch_to(GroupMgmtSG.edit_desc)


async def on_desc_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    manager.dialog_data["edit_desc"] = value.strip()
    await _save_group(manager)


async def on_skip_desc(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data["edit_desc"] = None
    await _save_group(manager)


async def _save_group(manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    name = manager.dialog_data["edit_name"]
    level = manager.dialog_data.get("edit_level")
    desc = manager.dialog_data.get("edit_desc")
    group_id = manager.dialog_data.get("selected_group_id")

    if group_id:
        await api_client.update_group(group_id, name=name, level=level, description=desc)
    else:
        group = await api_client.create_group(name, level, desc)
        manager.dialog_data["selected_group_id"] = group["id"]

    await manager.switch_to(GroupMgmtSG.group_card)


async def get_group_students(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("selected_group_id", 0)
    students = await api_client.get_group_students(group_id, limit=50)
    items = [
        (str(s["id"]), f"{s.get('full_name') or '—'} | {s.get('english_level') or '—'}")
        for s in students
    ]
    return {"students": items, "count": len(students)}


dialog = Dialog(
    Window(
        Format("🏫 Групи ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="groups_sel",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_select_group,
            ),
            id="groups_scroll",
            width=1,
            height=8,
        ),
        Button(Const("➕ Нова група"), id="new_group", on_click=on_new_group),
        Button(Const("← Меню"), id="back_menu_g", on_click=on_back_to_menu),
        state=GroupMgmtSG.list_view,
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
            Button(Const("✏️ Редагувати"), id="edit_grp", on_click=on_edit_group),
            Button(Const("👥 Учні"), id="view_students", on_click=on_view_students),
        ),
        Row(
            Button(Const("🗑 Видалити"), id="del_grp", on_click=on_delete_group),
            Button(Const("← Назад"), id="back_list_g", on_click=on_back_to_list),
        ),
        state=GroupMgmtSG.group_card,
        getter=get_group_card,
    ),
    Window(
        Const("✏️ Введіть назву групи:"),
        TextInput(id="name_input", on_success=on_name_entered),
        Button(Const("← Назад"), id="back_list_n", on_click=on_back_to_list),
        state=GroupMgmtSG.edit_name,
    ),
    Window(
        Const("🎓 Оберіть рівень групи:"),
        Select(
            Format("{item[1]}"),
            id="level_sel",
            item_id_getter=lambda x: x[0],
            items="levels",
            on_click=on_level_selected,
        ),
        Button(Const("← Назад"), id="back_name", on_click=lambda c, b, m: m.switch_to(GroupMgmtSG.edit_name)),
        state=GroupMgmtSG.edit_level,
        getter=lambda **_: {"levels": LEVELS},
    ),
    Window(
        Const("📝 Введіть опис групи (необов'язково):"),
        TextInput(id="desc_input", on_success=on_desc_entered),
        Button(Const("⏭ Пропустити"), id="skip_desc", on_click=on_skip_desc),
        state=GroupMgmtSG.edit_desc,
    ),
    Window(
        Format("👥 Учні групи ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="grp_students_sel",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=lambda c, w, m, i: None,
            ),
            id="grp_students_scroll",
            width=1,
            height=10,
        ),
        Button(Const("← Назад до групи"), id="back_card_gs", on_click=lambda c, b, m: m.switch_to(GroupMgmtSG.group_card)),
        state=GroupMgmtSG.group_students,
        getter=get_group_students,
    ),
)
