from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const


class StudentMenuSG(StatesGroup):
    main = State()


async def on_my_schedule(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.student.schedule import StudentScheduleSG
    await manager.start(StudentScheduleSG.schedule_view, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const("🏠 Головне меню"),
        Button(Const("📅 Мій розклад"), id="btn_my_schedule", on_click=on_my_schedule),
        state=StudentMenuSG.main,
    )
)
