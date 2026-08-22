from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput

class AdminContentSG(StatesGroup):
    list_view = State()
    view_content = State()
    edit_text = State()
    upload_media = State()


_CONTENT_KEYS = {
    "school_rules": "📋 Правила школи",
    "price_list": "💰 Цінова політика",
    "school_info": "📍 Контакти та адреса",
    "payment_details": "💳 Реквізити для оплати",
    "offer_agreement": "📜 Договір-оферта",
}

_FILE_TYPE_ICON = {"photo": "🖼", "video": "🎬", "document": "📎"}


async def _select(callback: CallbackQuery, button: Button, manager: DialogManager, key: str) -> None:
    manager.dialog_data["content_key"] = key
    manager.dialog_data["content_label"] = _CONTENT_KEYS[key]
    await manager.switch_to(AdminContentSG.view_content)


async def on_select_rules(c, b, m):   await _select(c, b, m, "school_rules")
async def on_select_prices(c, b, m):  await _select(c, b, m, "price_list")
async def on_select_info(c, b, m):    await _select(c, b, m, "school_info")
async def on_select_payment(c, b, m): await _select(c, b, m, "payment_details")
async def on_select_offer(c, b, m):   await _select(c, b, m, "offer_agreement")


async def get_content(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    key = dialog_manager.dialog_data.get("content_key", "")
    label = dialog_manager.dialog_data.get("content_label", "")
    content = await api_client.get_content(key)
    file_id = content.get("file_id")
    file_type = content.get("file_type")
    media_info = (
        f"{_FILE_TYPE_ICON.get(file_type, '📎')} Медіафайл прикріплено ({file_type})"
        if file_id else "Медіафайл відсутній"
    )
    return {
        "content_label": label,
        "content_value": content.get("value", "—"),
        "media_info": media_info,
        "has_media": bool(file_id),
    }


async def on_edit_text(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    await m.switch_to(AdminContentSG.edit_text)


async def on_upload_media(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    await m.switch_to(AdminContentSG.upload_media)


async def on_remove_media(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    key = manager.dialog_data.get("content_key", "")
    content = await api_client.get_content(key)
    user_id = manager.middleware_data["user_data"]["id"]
    await api_client.set_content(
        key, content.get("value", ""),
        updated_by=user_id,
        file_id=None, file_type=None,
    )
    await callback.answer("✅ Медіафайл видалено")
    await manager.switch_to(AdminContentSG.view_content)


async def on_text_entered(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    api_client = manager.middleware_data["api_client"]
    key = manager.dialog_data.get("content_key", "")
    user_id = manager.middleware_data["user_data"]["id"]
    # Preserve existing media when updating text
    content = await api_client.get_content(key)
    await api_client.set_content(
        key, value.strip(),
        updated_by=user_id,
        file_id=content.get("file_id"),
        file_type=content.get("file_type"),
    )
    await message.answer("✅ Текст збережено")
    await manager.switch_to(AdminContentSG.view_content)


async def on_media_received(message: Message, widget: MessageInput, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    key = manager.dialog_data.get("content_key", "")
    user_id = manager.middleware_data["user_data"]["id"]

    file_id: str | None = None
    file_type: str | None = None

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    else:
        await message.answer("⚠️ Надішліть фото, відео або документ")
        return

    content = await api_client.get_content(key)
    await api_client.set_content(
        key, content.get("value", ""),
        updated_by=user_id,
        file_id=file_id,
        file_type=file_type,
    )
    await message.answer("✅ Медіафайл збережено")
    await manager.switch_to(AdminContentSG.view_content)


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const("📄 Управління контентом\n\nОберіть розділ:"),
        Button(Const("📋 Правила школи"),        id="cnt_rules",   on_click=on_select_rules),
        Button(Const("💰 Цінова політика"),      id="cnt_prices",  on_click=on_select_prices),
        Button(Const("📍 Контакти та адреса"),   id="cnt_info",    on_click=on_select_info),
        Button(Const("💳 Реквізити для оплати"), id="cnt_pay",     on_click=on_select_payment),
        Button(Const("📜 Договір-оферта"),       id="cnt_offer",   on_click=on_select_offer),
        Button(Const("← Меню"), id="cnt_back_menu", on_click=on_back_to_menu),
        state=AdminContentSG.list_view,
    ),
    Window(
        Format(
            "📄 {content_label}\n\n"
            "{content_value}\n\n"
            "{media_info}"
        ),
        Row(
            Button(Const("✏️ Текст"),         id="cnt_edit_text",   on_click=on_edit_text),
            Button(Const("📎 Медіафайл"),     id="cnt_upload_media", on_click=on_upload_media),
        ),
        Button(
            Const("🗑 Видалити медіа"),
            id="cnt_remove_media",
            on_click=on_remove_media,
            when="has_media",
        ),
        Button(Const("← Назад"), id="cnt_back_list", on_click=lambda c, b, m: m.switch_to(AdminContentSG.list_view)),
        state=AdminContentSG.view_content,
        getter=get_content,
    ),
    Window(
        Format("✏️ {content_label}\n\nВведіть новий текст:"),
        TextInput(id="content_text_input", on_success=on_text_entered),
        Button(Const("← Назад"), id="cnt_back_view_t", on_click=lambda c, b, m: m.switch_to(AdminContentSG.view_content)),
        state=AdminContentSG.edit_text,
        getter=get_content,
    ),
    Window(
        Format("📎 {content_label}\n\nНадішліть фото, відео або документ:"),
        MessageInput(on_media_received),
        Button(Const("← Назад"), id="cnt_back_view_m", on_click=lambda c, b, m: m.switch_to(AdminContentSG.view_content)),
        state=AdminContentSG.upload_media,
        getter=get_content,
    ),
)
