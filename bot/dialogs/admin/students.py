from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select, Multiselect
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput


class StudentMgmtSG(StatesGroup):
    list_view = State()
    student_card = State()
    edit_level = State()
    assign_groups = State()
    confirm_delete = State()


LEVELS = [
    ("novice", "Новачок"),
    ("A1", "A1"),
    ("A2", "A2"),
    ("B1", "B1"),
    ("B2", "B2"),
    ("C1", "C1"),
    ("C2", "C2"),
]


async def get_students_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    search = dialog_manager.dialog_data.get("search")
    status_filter = dialog_manager.dialog_data.get("status_filter")
    group_filter = dialog_manager.dialog_data.get("group_filter")

    students = await api_client.get_students(
        search=search, status=status_filter, group_id=group_filter, limit=50
    )
    items = [
        (str(s["id"]), f"{s.get('full_name') or '—'} | {s.get('english_level') or '—'}")
        for s in students
    ]
    return {"students": items, "count": len(students), "search": search or ""}


async def on_search(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    manager.dialog_data["search"] = value.strip()


async def on_clear_search(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("search", None)


async def on_filter_all(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("status_filter", None)


async def on_filter_active(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data["status_filter"] = "active"


async def on_filter_pending(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data["status_filter"] = "pending"


async def on_select_student(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["selected_student_id"] = int(item_id)
    await manager.switch_to(StudentMgmtSG.student_card)


async def get_student_card(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_id = dialog_manager.dialog_data.get("selected_student_id", 0)
    student = await api_client.get_student(user_id)
    return {
        "full_name": student.get("full_name") or "—",
        "phone": student.get("phone") or "—",
        "english_level": student.get("english_level") or "Не вказано",
        "groups": ", ".join(student.get("group_names") or []) or "Не призначений",
        "status": student.get("status") or "—",
        "username": student.get("username") or "—",
        "user_id": user_id,
    }


async def on_edit_level(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(StudentMgmtSG.edit_level)


async def on_assign_groups(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(StudentMgmtSG.assign_groups)


async def on_change_status(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    user_id = manager.dialog_data["selected_student_id"]
    student = await api_client.get_student(user_id)
    new_status = "inactive" if student["status"] == "active" else "active"
    await api_client.update_status(user_id, new_status)
    await callback.answer(f"Статус змінено на: {new_status}")


async def on_confirm_delete_prompt(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(StudentMgmtSG.confirm_delete)


async def on_back_to_list(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(StudentMgmtSG.list_view)


async def on_level_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    api_client = manager.middleware_data["api_client"]
    user_id = manager.dialog_data["selected_student_id"]
    await api_client.set_student_level(user_id, item_id)
    await callback.answer(f"✅ Рівень встановлено: {item_id}")
    await manager.switch_to(StudentMgmtSG.student_card)


async def get_groups_for_select(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    groups = await api_client.get_groups()
    items = [(str(g["id"]), g["name"]) for g in groups]
    return {"groups": items}


async def on_save_groups(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    user_id = manager.dialog_data["selected_student_id"]
    checked = manager.find("groups_ms").get_checked()
    group_ids = [int(gid) for gid in checked]
    await api_client.set_student_groups(user_id, group_ids)
    await callback.answer("✅ Групи збережено")
    await manager.switch_to(StudentMgmtSG.student_card)


async def get_confirm_delete(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_id = dialog_manager.dialog_data.get("selected_student_id", 0)
    student = await api_client.get_student(user_id)
    return {"full_name": student.get("full_name") or "—"}


async def on_confirm_delete(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    user_id = manager.dialog_data["selected_student_id"]
    await api_client.delete_student(user_id)
    await callback.answer("✅ Учня деактивовано")
    await manager.switch_to(StudentMgmtSG.list_view)


dialog = Dialog(
    Window(
        Format("👥 Учні ({count})\nПошук: {search}"),
        TextInput(id="search_input", on_success=on_search),
        Row(
            Button(Const("Всі"), id="filter_all", on_click=on_filter_all),
            Button(Const("Активні"), id="filter_active", on_click=on_filter_active),
            Button(Const("Pending"), id="filter_pending", on_click=on_filter_pending),
        ),
        Button(Const("✖ Скинути пошук"), id="clear_search", on_click=on_clear_search),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="students_select",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=on_select_student,
            ),
            id="students_scroll",
            width=1,
            height=10,
        ),
        state=StudentMgmtSG.list_view,
        getter=get_students_list,
    ),
    Window(
        Format(
            "👤 {full_name}\n"
            "📱 {phone}\n"
            "🎓 Рівень: {english_level}\n"
            "👥 Групи: {groups}\n"
            "🔘 Статус: {status}\n"
            "@{username}"
        ),
        Row(
            Button(Const("✏️ Рівень"), id="btn_level", on_click=on_edit_level),
            Button(Const("👥 Групи"), id="btn_groups", on_click=on_assign_groups),
        ),
        Row(
            Button(Const("🔄 Статус"), id="btn_status", on_click=on_change_status),
            Button(Const("🗑 Видалити"), id="btn_delete", on_click=on_confirm_delete_prompt),
        ),
        Button(Const("← Назад"), id="back_list", on_click=on_back_to_list),
        state=StudentMgmtSG.student_card,
        getter=get_student_card,
    ),
    Window(
        Const("✏️ Оберіть рівень англійської:"),
        Select(
            Format("{item[1]}"),
            id="level_select",
            item_id_getter=lambda x: x[0],
            items="levels",
            on_click=on_level_selected,
        ),
        Button(Const("← Назад"), id="back_card_lv", on_click=lambda c, b, m: m.switch_to(StudentMgmtSG.student_card)),
        state=StudentMgmtSG.edit_level,
        getter=lambda **_: {"levels": LEVELS},
    ),
    Window(
        Const("👥 Оберіть групи (можна кілька):"),
        Multiselect(
            Format("✅ {item[1]}"),
            Format("☑️ {item[1]}"),
            id="groups_ms",
            item_id_getter=lambda x: x[0],
            items="groups",
        ),
        Row(
            Button(Const("✅ Зберегти"), id="save_groups", on_click=on_save_groups),
            Button(Const("← Назад"), id="back_card_gr", on_click=lambda c, b, m: m.switch_to(StudentMgmtSG.student_card)),
        ),
        state=StudentMgmtSG.assign_groups,
        getter=get_groups_for_select,
    ),
    Window(
        Format("⚠️ Видалити учня {full_name}?\nЦе деактивує акаунт."),
        Row(
            Button(Const("✅ Підтвердити"), id="confirm_del", on_click=on_confirm_delete),
            Button(Const("❌ Скасувати"), id="cancel_del", on_click=lambda c, b, m: m.switch_to(StudentMgmtSG.student_card)),
        ),
        state=StudentMgmtSG.confirm_delete,
        getter=get_confirm_delete,
    ),
)
