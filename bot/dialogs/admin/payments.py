from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput


class AdminPaymentSG(StatesGroup):
    details_view = State()
    details_edit = State()


async def get_details(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    content = await api_client.get_content("payment_details")
    return {"details_value": content.get("value", "—")}


async def on_details_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    api_client = manager.middleware_data["api_client"]
    user_data = manager.middleware_data.get("user_data", {})
    # Preserve media attached via the Content section
    current = await api_client.get_content("payment_details")
    await api_client.set_content(
        "payment_details", value.strip(),
        updated_by=user_data.get("id"),
        file_id=current.get("file_id"),
        file_type=current.get("file_type"),
    )
    await message.answer("✅ Реквізити збережено")
    await manager.switch_to(AdminPaymentSG.details_view)


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("🏦 Реквізити для оплати:\n\n{details_value}"),
        Button(Const("✏️ Редагувати"), id="pay_det_edit",
               on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.details_edit)),
        Button(Const("← Меню"), id="pay_back_menu", on_click=on_back_to_menu),
        state=AdminPaymentSG.details_view,
        getter=get_details,
    ),
    Window(
        Const("✏️ Введіть реквізити для оплати\n(картка, IBAN, отримувач тощо):"),
        TextInput(id="pay_det_input", on_success=on_details_entered),
        Button(Const("← Назад"), id="pay_det_edit_back",
               on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.details_view)),
        state=AdminPaymentSG.details_edit,
    ),
)
