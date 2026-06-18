from typing import Any, Optional

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format


class AdminBroadcastSG(StatesGroup):
    target_select = State()
    group_select = State()
    student_select = State()
    compose = State()
    preview = State()
    history = State()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _resolve_recipients(
    api_client, target_type: str, target_id: Optional[int]
) -> list[int]:
    if target_type == "all_students":
        students = await api_client.get_students(status="active", limit=500)
        return [s["telegram_id"] for s in students if s.get("telegram_id")]
    elif target_type == "all_teachers":
        users = await api_client.get_users(role="teacher", status="active")
        return [u["telegram_id"] for u in users if u.get("telegram_id")]
    elif target_type == "all":
        students = await api_client.get_students(status="active", limit=500)
        teachers = await api_client.get_users(role="teacher", status="active")
        ids = [s["telegram_id"] for s in students if s.get("telegram_id")]
        ids += [u["telegram_id"] for u in teachers if u.get("telegram_id")]
        return ids
    elif target_type == "group" and target_id:
        students = await api_client.get_group_students(target_id)
        return [s["telegram_id"] for s in students if s.get("telegram_id")]
    elif target_type == "student" and target_id:
        student = await api_client.get_student(target_id)
        if student and student.get("telegram_id"):
            return [student["telegram_id"]]
    return []


# ---------------------------------------------------------------------------
# Target select handlers
# ---------------------------------------------------------------------------

async def on_target_direct(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    """Handler for direct target types (no sub-selection needed)."""
    target_map = {
        "t_all_students": "all_students",
        "t_all_teachers": "all_teachers",
        "t_all": "all",
    }
    manager.dialog_data["target_type"] = target_map[button.widget_id]
    manager.dialog_data.pop("target_id", None)
    await manager.switch_to(AdminBroadcastSG.compose)


async def on_target_group(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data["target_type"] = "group"
    manager.dialog_data.pop("target_id", None)
    await manager.switch_to(AdminBroadcastSG.group_select)


async def on_target_student(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data["target_type"] = "student"
    manager.dialog_data.pop("target_id", None)
    await manager.switch_to(AdminBroadcastSG.student_select)


# ---------------------------------------------------------------------------
# Group select
# ---------------------------------------------------------------------------

async def get_groups_for_broadcast(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    groups = await api_client.get_groups()
    items = [(str(g["id"]), g["name"]) for g in groups]
    return {"groups": items, "count": len(items)}


async def on_group_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["target_id"] = int(item_id)
    await manager.switch_to(AdminBroadcastSG.compose)


# ---------------------------------------------------------------------------
# Student select
# ---------------------------------------------------------------------------

async def get_students_for_broadcast(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    students = await api_client.get_students(status="active", limit=200)
    items = [
        (str(s["id"]), s.get("full_name") or f"Учень #{s['id']}")
        for s in students
    ]
    return {"students": items, "count": len(items)}


async def on_student_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["target_id"] = int(item_id)
    await manager.switch_to(AdminBroadcastSG.compose)


# ---------------------------------------------------------------------------
# Compose
# ---------------------------------------------------------------------------

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
        await message.answer("Підтримуються: текст, фото, документ, відео")
        return
    await manager.switch_to(AdminBroadcastSG.preview)


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

async def get_preview(dialog_manager: DialogManager, **kwargs) -> dict:
    dd = dialog_manager.dialog_data
    target_type = dd.get("target_type", "")
    target_labels = {
        "all_students": "Всі учні",
        "group": f"Група #{dd.get('target_id', '')}",
        "student": f"Учень #{dd.get('target_id', '')}",
        "all_teachers": "Всі викладачі",
        "all": "Всі",
    }
    return {
        "target_label": target_labels.get(target_type, target_type),
        "msg_type": dd.get("msg_type", ""),
        "msg_text": dd.get("msg_text") or "(медіа)",
    }


async def on_send(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    bot = manager.middleware_data["bot"]
    user = manager.middleware_data["event_from_user"]
    dd = manager.dialog_data

    target_type = dd["target_type"]
    target_id = dd.get("target_id")
    msg_type = dd["msg_type"]
    msg_text = dd.get("msg_text")
    msg_file_id = dd.get("msg_file_id")

    recipients = await _resolve_recipients(api_client, target_type, target_id)

    count = 0
    for tg_id in recipients:
        if tg_id and tg_id > 0:
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

    sender_user = await api_client.get_or_create_user(user.id, user.username)

    await api_client.save_broadcast(
        target_type=target_type,
        message_type=msg_type,
        recipient_count=count,
        sender_id=sender_user.get("id"),
        target_id=target_id,
        text=msg_text,
        file_id=msg_file_id,
    )

    await callback.message.answer(f"✅ Надіслано {count} користувачам")
    await manager.switch_to(AdminBroadcastSG.target_select)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

async def get_history(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    broadcasts = await api_client.get_broadcasts(limit=20)

    target_labels = {
        "all_students": "Всі учні",
        "group": "Група",
        "student": "Учень",
        "all_teachers": "Всі викладачі",
        "all": "Всі",
    }

    items = []
    for b in broadcasts:
        ttype = target_labels.get(b.get("target_type", ""), b.get("target_type", ""))
        mtype = b.get("message_type", "")
        count = b.get("recipient_count", 0)
        sent_at = b.get("sent_at", "")[:16] if b.get("sent_at") else "—"
        items.append(f"📢 {ttype} | {mtype} | {sent_at} | {count} отримали")

    indexed = [(str(i), label) for i, label in enumerate(items)]
    return {"history_items": indexed, "history_count": len(indexed)}


async def on_history_item_click(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    # Read-only list — no action on click
    pass


# ---------------------------------------------------------------------------
# Back to menu
# ---------------------------------------------------------------------------

async def on_back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

dialog = Dialog(
    # ---- target_select ----
    Window(
        Const("📢 Розсилка\n\nОберіть аудиторію:"),
        Button(Const("👥 Всі учні"), id="t_all_students", on_click=on_target_direct),
        Button(Const("🏫 Група"), id="t_group", on_click=on_target_group),
        Button(Const("👤 Учень"), id="t_student", on_click=on_target_student),
        Button(Const("👩‍🏫 Всі викладачі"), id="t_all_teachers", on_click=on_target_direct),
        Button(Const("📣 Всі"), id="t_all", on_click=on_target_direct),
        Button(
            Const("🕐 Історія"),
            id="t_history",
            on_click=lambda c, b, m: m.switch_to(AdminBroadcastSG.history),
        ),
        Button(Const("← Меню"), id="back_menu_br", on_click=on_back_to_menu),
        state=AdminBroadcastSG.target_select,
    ),
    # ---- group_select ----
    Window(
        Format("🏫 Оберіть групу ({count} груп):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="group_sel",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_selected,
            ),
            id="group_scroll",
            width=1,
            height=8,
        ),
        Button(
            Const("← Назад"),
            id="back_target_gr",
            on_click=lambda c, b, m: m.switch_to(AdminBroadcastSG.target_select),
        ),
        state=AdminBroadcastSG.group_select,
        getter=get_groups_for_broadcast,
    ),
    # ---- student_select ----
    Window(
        Format("👤 Оберіть учня ({count} учнів):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="student_sel",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=on_student_selected,
            ),
            id="student_scroll",
            width=1,
            height=8,
        ),
        Button(
            Const("← Назад"),
            id="back_target_st",
            on_click=lambda c, b, m: m.switch_to(AdminBroadcastSG.target_select),
        ),
        state=AdminBroadcastSG.student_select,
        getter=get_students_for_broadcast,
    ),
    # ---- compose ----
    Window(
        Const("✏️ Надішліть повідомлення (текст, фото, документ або відео):"),
        MessageInput(on_message_received, content_types=[ContentType.ANY]),
        Button(
            Const("← Назад"),
            id="back_compose",
            on_click=lambda c, b, m: m.switch_to(AdminBroadcastSG.target_select),
        ),
        state=AdminBroadcastSG.compose,
    ),
    # ---- preview ----
    Window(
        Format(
            "👀 Перегляд розсилки:\n\n"
            "Аудиторія: {target_label}\n"
            "Тип: {msg_type}\n"
            "Текст: {msg_text}"
        ),
        Row(
            Button(Const("✅ Надіслати"), id="btn_send", on_click=on_send),
            Button(
                Const("✏️ Змінити"),
                id="btn_edit",
                on_click=lambda c, b, m: m.switch_to(AdminBroadcastSG.compose),
            ),
        ),
        Button(
            Const("← Скасувати"),
            id="btn_cancel_br",
            on_click=lambda c, b, m: m.switch_to(AdminBroadcastSG.target_select),
        ),
        state=AdminBroadcastSG.preview,
        getter=get_preview,
    ),
    # ---- history ----
    Window(
        Format("📋 Історія розсилок ({history_count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="history_sel",
                item_id_getter=lambda x: x[0],
                items="history_items",
                on_click=on_history_item_click,
            ),
            id="history_scroll",
            width=1,
            height=8,
        ),
        Button(
            Const("← Назад"),
            id="back_hist",
            on_click=lambda c, b, m: m.switch_to(AdminBroadcastSG.target_select),
        ),
        state=AdminBroadcastSG.history,
        getter=get_history,
    ),
)
