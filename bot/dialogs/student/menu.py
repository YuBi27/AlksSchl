from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row
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


async def on_schedule(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.student.schedule import StudentScheduleSG
    await m.start(StudentScheduleSG.schedule_view, mode=StartMode.RESET_STACK)

async def on_homework(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.student.homework import StudentHomeworkSG
    await m.start(StudentHomeworkSG.hw_list, mode=StartMode.RESET_STACK)

async def on_quizzes(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.student.quizzes import StudentQuizSG
    await m.start(StudentQuizSG.quiz_list, mode=StartMode.RESET_STACK)

async def on_payments(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.student.payments import StudentPaymentSG
    await m.start(StudentPaymentSG.main, mode=StartMode.RESET_STACK)

async def on_profile(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.student.profile import StudentProfileSG
    await m.start(StudentProfileSG.main, mode=StartMode.RESET_STACK)

async def on_info(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.student.info import StudentInfoSG
    await m.start(StudentInfoSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("🏠 Привіт, <b>{name}</b>!\n👥 Групи: {groups}\n\nОберіть розділ:"),
        Row(
            Button(Const("📅 Розклад"),     id="sm_schedule",  on_click=on_schedule),
            Button(Const("📝 ДЗ"),          id="sm_hw",        on_click=on_homework),
        ),
        Row(
            Button(Const("📋 Тести"),       id="sm_quizzes",   on_click=on_quizzes),
            Button(Const("💳 Оплата"),      id="sm_payments",  on_click=on_payments),
        ),
        Row(
            Button(Const("👤 Профіль"),     id="sm_profile",   on_click=on_profile),
            Button(Const("📄 Про школу"),   id="sm_info",      on_click=on_info),
        ),
        state=StudentMenuSG.main,
        getter=get_menu_data,
    )
)
