from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format


class StudentPaymentSG(StatesGroup):
    main = State()


async def get_payment_details(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    content = await api_client.get_content("payment_details")
    return {"payment_details": content.get("value", "—")}


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.student.menu import StudentMenuSG
    await manager.start(StudentMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("💳 Реквізити для оплати\n\n{payment_details}"),
        Button(Const("← Меню"), id="sp_back_menu", on_click=on_back_to_menu),
        state=StudentPaymentSG.main,
        getter=get_payment_details,
    ),
)
