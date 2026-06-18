from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format


class StudentMenuSG(StatesGroup):
    main = State()


async def get_menu_data(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_data = dialog_manager.middleware_data["user_data"]
    try:
        student = await api_client.get_student(user_data["id"])
        name = student.get("full_name") or "Учень"
        groups = ", ".join(student.get("group_names") or []) or "не призначений"
    except Exception:
        name = user_data.get("username") or "Учень"
        groups = "—"
    return {"name": name, "groups": groups}


async def on_my_schedule(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.student.schedule import StudentScheduleSG
    await manager.start(StudentScheduleSG.schedule_view, mode=StartMode.RESET_STACK)


async def on_my_homework(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.student.homework import StudentHomeworkSG
    await manager.start(StudentHomeworkSG.hw_list, mode=StartMode.RESET_STACK)


async def on_my_profile(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.student.profile import StudentProfileSG
    await manager.start(StudentProfileSG.main, mode=StartMode.RESET_STACK)


async def on_school_info(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.student.info import StudentInfoSG
    await manager.start(StudentInfoSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("🏠 Привіт, <b>{name}</b>!\n👥 Групи: {groups}\n\nОберіть розділ:"),
        Button(Const("📅 Мій розклад"), id="btn_my_schedule", on_click=on_my_schedule),
        Button(Const("📝 Домашні завдання"), id="btn_my_hw", on_click=on_my_homework),
        Button(Const("👤 Мій профіль"), id="btn_my_profile", on_click=on_my_profile),
        Button(Const("📄 Інфо про школу"), id="btn_school_info", on_click=on_school_info),
        state=StudentMenuSG.main,
        getter=get_menu_data,
    )
)
