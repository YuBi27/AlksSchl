from typing import Any

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format


class TeacherBroadcastSG(StatesGroup):
    group_select = State()
    compose = State()
    preview = State()


def _teacher_id(manager: DialogManager) -> int:
    return (
        manager.dialog_data.get("teacher_override_id")
        or manager.middleware_data["user_data"]["id"]
    )


async def on_start(start_data: dict, manager: DialogManager) -> None:
    if isinstance(start_data, dict) and "teacher_override_id" in start_data:
        manager.dialog_data["teacher_override_id"] = start_data["teacher_override_id"]


async def get_teacher_groups(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    teacher_id = _teacher_id(dialog_manager)
    groups = await api_client.get_groups(teacher_id=teacher_id)
    items = [(str(g["id"]), g["name"]) for g in groups]
    return {"groups": items, "count": len(groups)}


async def on_group_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["target_id"] = int(item_id)
    await manager.switch_to(TeacherBroadcastSG.compose)


async def on_message_received(
    message: Message, widget: MessageInput, manager: DialogManager
) -> None:
    if message.content_type == ContentType.TEXT:
        manager.dialog_data["msg_type"] = "text"
        manager.dialog_data["msg_text"] = message.text
        manager.dialog_data["msg_file_id"] = None
    elif message.content_type == ContentType.PHOTO:
        manager.dialog_data["msg_type"] = "photo"
        manager.dialog_data["msg_file_id"] = message.photo[-1].file_id
        manager.dialog_data["msg_text"] = message.caption
    elif message.content_type == ContentType.DOCUMENT:
        manager.dialog_data["msg_type"] = "document"
        manager.dialog_data["msg_file_id"] = message.document.file_id
        manager.dialog_data["msg_text"] = message.caption
    elif message.content_type == ContentType.VIDEO:
        manager.dialog_data["msg_type"] = "video"
        manager.dialog_data["msg_file_id"] = message.video.file_id
        manager.dialog_data["msg_text"] = message.caption
    else:
        await message.answer("Підтримуються: текст, фото, документ або відео")
        return
    await manager.switch_to(TeacherBroadcastSG.preview)


async def get_preview(dialog_manager: DialogManager, **kwargs) -> dict:
    dd = dialog_manager.dialog_data
    return {
        "target_id": dd.get("target_id", ""),
        "msg_type": dd.get("msg_type", ""),
        "msg_text": dd.get("msg_text") or "(медіа)",
    }


async def on_send(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    bot = manager.middleware_data["bot"]
    user = manager.middleware_data["event_from_user"]
    dd = manager.dialog_data

    target_id = dd["target_id"]
    msg_type = dd["msg_type"]
    msg_text = dd.get("msg_text")
    msg_file_id = dd.get("msg_file_id")

    # Get students in group
    students = await api_client.get_group_students(target_id)
    recipients = [s["telegram_id"] for s in students if s.get("telegram_id") and s["telegram_id"] > 0]

    count = 0
    for tg_id in recipients:
        try:
            if msg_type == "text":
                await bot.send_message(tg_id, msg_text)
            elif msg_type == "photo":
                await bot.send_photo(tg_id, msg_file_id, caption=msg_text)
            elif msg_type == "document":
                await bot.send_document(tg_id, msg_file_id, caption=msg_text)
            elif msg_type == "video":
                await bot.send_video(tg_id, msg_file_id, caption=msg_text)
            count += 1
        except Exception:
            pass

    # Get sender internal id
    sender_user = await api_client.get_or_create_user(user.id, user.username)

    # Record broadcast
    await api_client.save_broadcast(
        target_type="group",
        message_type=msg_type,
        recipient_count=count,
        sender_id=sender_user.get("id"),
        target_id=target_id,
        text=msg_text,
        file_id=msg_file_id,
    )

    await callback.message.answer(f"✅ Надіслано {count} учням групи")
    await manager.switch_to(TeacherBroadcastSG.group_select)


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.teacher.menu import TeacherMenuSG
    await manager.start(TeacherMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("📢 Розсилка групі\n\nОберіть групу ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="tg_group_sel",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_selected,
            ),
            id="tg_group_scroll",
            width=1,
            height=8,
        ),
        Button(Const("← Меню"), id="tg_back_menu", on_click=on_back_to_menu),
        state=TeacherBroadcastSG.group_select,
        getter=get_teacher_groups,
    ),
    Window(
        Const("✏️ Надішліть повідомлення групі (текст, фото, документ або відео):"),
        MessageInput(on_message_received, content_types=[ContentType.ANY]),
        Button(Const("← Назад"), id="tg_back_compose", on_click=lambda c, b, m: m.switch_to(TeacherBroadcastSG.group_select)),
        state=TeacherBroadcastSG.compose,
    ),
    Window(
        Format("👀 Перегляд:\n\nГрупа: #{target_id}\nТип: {msg_type}\nТекст: {msg_text}"),
        Row(
            Button(Const("✅ Надіслати"), id="tg_btn_send", on_click=on_send),
            Button(Const("✏️ Змінити"), id="tg_btn_edit", on_click=lambda c, b, m: m.switch_to(TeacherBroadcastSG.compose)),
        ),
        Button(Const("← Скасувати"), id="tg_btn_cancel", on_click=lambda c, b, m: m.switch_to(TeacherBroadcastSG.group_select)),
        state=TeacherBroadcastSG.preview,
        getter=get_preview,
    ),
    on_start=on_start,
)
