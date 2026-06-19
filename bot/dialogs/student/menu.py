from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select
from aiogram_dialog.widgets.text import Format


class StudentMenuSG(StatesGroup):
    main = State()


_MENU_ITEMS = [
    ("schedule", "📅 Мій розклад"),
    ("homework", "📝 Домашні завдання"),
    ("quizzes", "📋 Тести"),
    ("payments", "💳 Оплата"),
    ("profile", "👤 Мій профіль"),
    ("info", "📄 Інфо про школу"),
]


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
    return {"name": name, "groups": groups, "items": _MENU_ITEMS}


async def on_menu_select(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    if item_id == "schedule":
        from bot.dialogs.student.schedule import StudentScheduleSG
        await manager.start(StudentScheduleSG.schedule_view, mode=StartMode.RESET_STACK)
    elif item_id == "homework":
        from bot.dialogs.student.homework import StudentHomeworkSG
        await manager.start(StudentHomeworkSG.hw_list, mode=StartMode.RESET_STACK)
    elif item_id == "profile":
        from bot.dialogs.student.profile import StudentProfileSG
        await manager.start(StudentProfileSG.main, mode=StartMode.RESET_STACK)
    elif item_id == "info":
        from bot.dialogs.student.info import StudentInfoSG
        await manager.start(StudentInfoSG.main, mode=StartMode.RESET_STACK)
    elif item_id == "payments":
        from bot.dialogs.student.payments import StudentPaymentSG
        await manager.start(StudentPaymentSG.main, mode=StartMode.RESET_STACK)
    elif item_id == "quizzes":
        from bot.dialogs.student.quizzes import StudentQuizSG
        await manager.start(StudentQuizSG.quiz_list, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("🏠 Привіт, <b>{name}</b>!\n👥 Групи: {groups}\n\nОберіть розділ:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="student_menu_sel",
                item_id_getter=lambda x: x[0],
                items="items",
                on_click=on_menu_select,
            ),
            id="student_menu_sg",
            width=1,
            height=6,
        ),
        state=StudentMenuSG.main,
        getter=get_menu_data,
    )
)
