from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput


class AdminContentSG(StatesGroup):
    list_view = State()
    view_content = State()
    edit_content = State()


async def on_select_rules(callback, button, manager):
    manager.dialog_data["content_key"] = "school_rules"
    manager.dialog_data["content_label"] = "Правила школи"
    await manager.switch_to(AdminContentSG.view_content)


async def on_select_prices(callback, button, manager):
    manager.dialog_data["content_key"] = "price_list"
    manager.dialog_data["content_label"] = "Цінова політика"
    await manager.switch_to(AdminContentSG.view_content)


async def on_select_info(callback, button, manager):
    manager.dialog_data["content_key"] = "school_info"
    manager.dialog_data["content_label"] = "Контакти та адреса"
    await manager.switch_to(AdminContentSG.view_content)


async def get_content(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    key = dialog_manager.dialog_data.get("content_key", "")
    label = dialog_manager.dialog_data.get("content_label", "")
    content = await api_client.get_content(key)
    return {
        "content_label": label,
        "content_value": content.get("value", "—"),
    }


async def on_value_entered(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    api_client = manager.middleware_data["api_client"]
    key = manager.dialog_data.get("content_key", "")
    user_data = manager.middleware_data.get("user_data", {})
    updated_by = user_data.get("id")
    await api_client.set_content(key, value.strip(), updated_by=updated_by)
    await message.answer("✅ Збережено")
    await manager.switch_to(AdminContentSG.view_content)


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const("📄 Управління контентом\n\nОберіть розділ:"),
        Button(Const("📋 Правила школи"), id="cnt_rules", on_click=on_select_rules),
        Button(Const("💰 Цінова політика"), id="cnt_prices", on_click=on_select_prices),
        Button(Const("📍 Контакти та адреса"), id="cnt_info", on_click=on_select_info),
        Button(Const("← Меню"), id="cnt_back_menu", on_click=on_back_to_menu),
        state=AdminContentSG.list_view,
    ),
    Window(
        Format("📄 {content_label}\n\n{content_value}"),
        Button(Const("✏️ Редагувати"), id="cnt_edit", on_click=lambda c, b, m: m.switch_to(AdminContentSG.edit_content)),
        Button(Const("← Назад"), id="cnt_back_list", on_click=lambda c, b, m: m.switch_to(AdminContentSG.list_view)),
        state=AdminContentSG.view_content,
        getter=get_content,
    ),
    Window(
        Format("✏️ Редагувати: {content_label}\n\nВведіть новий текст:"),
        TextInput(id="content_input", on_success=on_value_entered),
        Button(Const("← Назад"), id="cnt_back_view", on_click=lambda c, b, m: m.switch_to(AdminContentSG.view_content)),
        state=AdminContentSG.edit_content,
        getter=get_content,
    ),
)
