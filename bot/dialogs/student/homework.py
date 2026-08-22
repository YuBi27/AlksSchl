from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput

KYIV_TZ = ZoneInfo("Europe/Kyiv")


class StudentHomeworkSG(StatesGroup):
    hw_list = State()
    hw_detail = State()
    hw_submit = State()


def _trunc(text: str, max_len: int = 50) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


async def get_hw_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_data = dialog_manager.middleware_data["user_data"]
    user_id = user_data["id"]

    try:
        student = await api_client.get_student(user_id)
        group_names = student.get("group_names", [])
    except Exception:
        group_names = []

    all_groups = await api_client.get_groups()
    name_to_id = {g["name"]: g["id"] for g in all_groups}
    group_ids = [name_to_id[n] for n in group_names if n in name_to_id]

    all_hw = []
    seen_ids: set[int] = set()
    for gid in group_ids:
        hws = await api_client.get_homeworks(group_id=gid)
        for hw in hws:
            if hw["id"] not in seen_ids:
                seen_ids.add(hw["id"])
                all_hw.append(hw)

    personal_hws = await api_client.get_homeworks(student_user_id=user_id)
    for hw in personal_hws:
        if hw["id"] not in seen_ids:
            seen_ids.add(hw["id"])
            all_hw.append(hw)

    all_hw.sort(key=lambda h: h["due_at"])

    grades: dict[int, str] = {}
    for hw in all_hw:
        g = await api_client.get_homework_grades(hw["id"])
        for gr in g:
            if gr["student_user_id"] == user_id:
                grades[hw["id"]] = gr["grade_text"]

    items = []
    for hw in all_hw:
        due = datetime.fromisoformat(hw["due_at"]).astimezone(KYIV_TZ)
        due_str = due.strftime("%d.%m %H:%M")
        graded = "✅" if hw["id"] in grades else "⏳"
        label = _trunc(f"{graded} {hw['title']} — до {due_str}")
        items.append((str(hw["id"]), label))

    dialog_manager.dialog_data["_hw_cache"] = {str(hw["id"]): hw for hw in all_hw}
    dialog_manager.dialog_data["_grades_cache"] = {str(k): v for k, v in grades.items()}

    return {"homeworks": items, "count": len(items)}


async def on_select_hw(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["selected_hw_id"] = item_id
    await manager.switch_to(StudentHomeworkSG.hw_detail)


async def get_hw_detail(dialog_manager: DialogManager, **kwargs) -> dict:
    hw_id = dialog_manager.dialog_data.get("selected_hw_id", "0")
    cache = dialog_manager.dialog_data.get("_hw_cache", {})
    grades_cache = dialog_manager.dialog_data.get("_grades_cache", {})
    hw = cache.get(hw_id)
    if not hw:
        return {"hw_text": "❌ Завдання не знайдено", "hw_id": "0"}
    due = datetime.fromisoformat(hw["due_at"]).astimezone(KYIV_TZ)
    due_str = due.strftime("%d.%m.%Y о %H:%M")
    grade = grades_cache.get(hw_id)
    grade_line = f"\n\n📝 Ваша оцінка: <b>{grade}</b>" if grade else "\n\n⏳ Ще не оцінено"
    target = "👥 Для групи" if hw.get("group_id") else "👤 Особисте"
    hw_text = (
        f"📚 <b>{hw['title']}</b>\n"
        f"📋 {hw.get('description') or '—'}\n"
        f"⏰ Здати до: {due_str}\n"
        f"🎯 {target}"
        f"{grade_line}"
    )
    return {"hw_text": hw_text, "hw_id": hw_id}


async def on_submit_click(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(StudentHomeworkSG.hw_submit)


async def on_homework_submission(
    message: Message, widget: MessageInput, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    bot = manager.middleware_data["bot"]
    user_data = manager.middleware_data["user_data"]
    user_id = user_data["id"]

    hw_id = manager.dialog_data.get("selected_hw_id", "0")
    cache = manager.dialog_data.get("_hw_cache", {})
    hw = cache.get(hw_id, {})

    # Get student name
    try:
        student = await api_client.get_student(user_id)
        student_name = student.get("full_name") or user_data.get("username") or f"ID {user_id}"
    except Exception:
        student_name = user_data.get("username") or f"ID {user_id}"

    hw_title = hw.get("title", "ДЗ")
    caption = (
        f"📤 <b>Відповідь на ДЗ</b>\n\n"
        f"📚 {hw_title}\n"
        f"👤 {student_name}"
    )

    # Find teacher to notify
    teacher_id = hw.get("teacher_id", 0)
    teacher_tg_id = None
    if teacher_id:
        try:
            teacher_user = await api_client.get_user(teacher_id)
            teacher_tg_id = teacher_user.get("telegram_id")
        except Exception:
            pass

    # Also notify admins if no teacher
    from bot.config import settings
    notify_tg_ids = []
    if teacher_tg_id:
        notify_tg_ids.append(teacher_tg_id)
    else:
        notify_tg_ids.extend(settings.admin_id_list)

    # Forward submission to teacher/admin
    for tg_id in notify_tg_ids:
        try:
            if message.text:
                await bot.send_message(
                    tg_id,
                    f"{caption}\n\n💬 {message.text}",
                    parse_mode="HTML",
                )
            elif message.photo:
                await bot.send_photo(
                    tg_id,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
            elif message.document:
                await bot.send_document(
                    tg_id,
                    document=message.document.file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
            elif message.voice:
                await bot.send_voice(
                    tg_id,
                    voice=message.voice.file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
            elif message.video:
                await bot.send_video(
                    tg_id,
                    video=message.video.file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
            elif message.audio:
                await bot.send_audio(
                    tg_id,
                    audio=message.audio.file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
        except Exception:
            pass

    await message.answer(
        f"✅ Вашу відповідь на «{hw_title}» надіслано викладачу!",
        parse_mode="HTML",
    )
    await manager.switch_to(StudentHomeworkSG.hw_detail)


async def _back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.student.menu import StudentMenuSG
    await manager.start(StudentMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("📝 Ваші домашні завдання ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="hw_sel",
                item_id_getter=lambda x: x[0],
                items="homeworks",
                on_click=on_select_hw,
            ),
            id="hw_scroll",
            width=1,
            height=8,
        ),
        Button(Const("← Меню"), id="back_menu_hw", on_click=_back_to_menu),
        state=StudentHomeworkSG.hw_list,
        getter=get_hw_list,
    ),
    Window(
        Format("{hw_text}"),
        Row(
            Button(Const("📤 Надіслати відповідь"), id="btn_submit_hw", on_click=on_submit_click),
            Button(Const("← Назад"), id="back_hw_list", on_click=lambda c, b, m: m.switch_to(StudentHomeworkSG.hw_list)),
        ),
        state=StudentHomeworkSG.hw_detail,
        getter=get_hw_detail,
    ),
    Window(
        Const(
            "📤 <b>Надіслати відповідь на ДЗ</b>\n\n"
            "Надішліть текст, фото, документ, голосове або відео.\n"
            "Викладач отримає вашу відповідь."
        ),
        MessageInput(
            on_homework_submission,
            content_types=[
                ContentType.TEXT,
                ContentType.PHOTO,
                ContentType.DOCUMENT,
                ContentType.VOICE,
                ContentType.VIDEO,
                ContentType.AUDIO,
            ],
        ),
        Button(
            Const("← Скасувати"),
            id="cancel_submit",
            on_click=lambda c, b, m: m.switch_to(StudentHomeworkSG.hw_detail),
        ),
        state=StudentHomeworkSG.hw_submit,
    ),
)
