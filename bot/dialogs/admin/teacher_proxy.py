from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format


class TeacherProxySG(StatesGroup):
    teacher_list = State()
    teacher_selected = State()


async def get_teachers(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    teachers = await api_client.get_users_by_role("teacher")
    items = [(str(t["id"]), t.get("username") or f"ID {t['id']}") for t in teachers]
    return {"teachers": items}


async def on_teacher_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["proxy_teacher_id"] = int(item_id)
    await manager.switch_to(TeacherProxySG.teacher_selected)


async def get_teacher_name(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    teacher_id = dialog_manager.dialog_data.get("proxy_teacher_id", 0)
    try:
        profile = await api_client.get_teacher_profile(teacher_id)
        name = profile.get("full_name", f"ID {teacher_id}")
    except Exception:
        name = f"ID {teacher_id}"
    return {"proxy_teacher_name": name}


async def on_open_panel(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.teacher.menu import TeacherMenuSG
    teacher_id = manager.dialog_data.get("proxy_teacher_id", 0)
    await manager.start(TeacherMenuSG.main, data={"teacher_override_id": teacher_id})


dialog = Dialog(
    Window(
        Const("👨‍🏫 Оберіть викладача:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="teacher_select",
                item_id_getter=lambda x: x[0],
                items="teachers",
                on_click=on_teacher_selected,
            ),
            id="teacher_scroll",
            width=1,
            height=7,
        ),
        state=TeacherProxySG.teacher_list,
        getter=get_teachers,
    ),
    Window(
        Format("Викладач: {proxy_teacher_name}"),
        Button(Const("👨‍🏫 Відкрити панель"), id="btn_open_panel", on_click=on_open_panel),
        Button(Const("← Назад"), id="btn_back_list", on_click=lambda c, b, m: m.switch_to(TeacherProxySG.teacher_list)),
        state=TeacherProxySG.teacher_selected,
        getter=get_teacher_name,
    ),
)
