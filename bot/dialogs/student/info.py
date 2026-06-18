from typing import Any

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format


class StudentInfoSG(StatesGroup):
    main = State()
    rules = State()
    prices = State()
    info = State()
    teachers = State()
    teacher_card = State()


# ── getters ──────────────────────────────────────────────────────────────────

async def get_rules(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    content = await api_client.get_content("school_rules")
    return {"content_text": content.get("value", "—")}


async def get_prices(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    content = await api_client.get_content("price_list")
    return {"content_text": content.get("value", "—")}


async def get_info(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    content = await api_client.get_content("school_info")
    return {"content_text": content.get("value", "—")}


async def get_teachers(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    profiles = await api_client.get_teacher_profiles()
    items = [
        (str(p["user_id"]), p.get("full_name") or f"Викладач #{p['user_id']}")
        for p in profiles
    ]
    return {"teachers": items, "count": len(items)}


async def get_teacher_card(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    bot = dialog_manager.middleware_data["bot"]
    event_from_user = dialog_manager.middleware_data["event_from_user"]
    user_id = dialog_manager.dialog_data.get("selected_teacher_id", 0)
    profile = await api_client.get_teacher_profile(user_id)

    full_name = profile.get("full_name") or "—"
    specialization = profile.get("specialization") or "—"
    experience_years = profile.get("experience_years") or 0
    bio = profile.get("bio") or "—"
    photo_file_id = profile.get("photo_file_id")

    caption = (
        f"👩‍🏫 {full_name}\n"
        f"🎓 Спеціалізація: {specialization}\n"
        f"📅 Досвід: {experience_years} р.\n"
        f"📝 {bio}"
    )

    if photo_file_id:
        try:
            await bot.send_photo(
                event_from_user.id,
                photo_file_id,
                caption=caption,
            )
        except Exception:
            pass

    return {
        "teacher_name": full_name,
        "teacher_spec": specialization,
        "teacher_exp": str(experience_years),
        "teacher_bio": bio,
        "has_photo": bool(photo_file_id),
    }


# ── callbacks ─────────────────────────────────────────────────────────────────

async def on_back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.student.menu import StudentMenuSG
    await manager.start(StudentMenuSG.main, mode=StartMode.RESET_STACK)


async def on_teacher_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["selected_teacher_id"] = int(item_id)
    await manager.switch_to(StudentInfoSG.teacher_card)


# ── dialog ────────────────────────────────────────────────────────────────────

dialog = Dialog(
    # main menu
    Window(
        Const("📄 Інформація про школу\n\nОберіть розділ:"),
        Button(Const("📋 Правила школи"), id="si_rules",
               on_click=lambda c, b, m: m.switch_to(StudentInfoSG.rules)),
        Button(Const("💰 Ціни"), id="si_prices",
               on_click=lambda c, b, m: m.switch_to(StudentInfoSG.prices)),
        Button(Const("📍 Контакти"), id="si_info",
               on_click=lambda c, b, m: m.switch_to(StudentInfoSG.info)),
        Button(Const("👩‍🏫 Викладачі"), id="si_teachers",
               on_click=lambda c, b, m: m.switch_to(StudentInfoSG.teachers)),
        Button(Const("← Меню"), id="si_back_menu", on_click=on_back_to_menu),
        state=StudentInfoSG.main,
    ),
    # rules
    Window(
        Format("{content_text}"),
        Button(Const("← Назад"), id="si_back_main_r",
               on_click=lambda c, b, m: m.switch_to(StudentInfoSG.main)),
        state=StudentInfoSG.rules,
        getter=get_rules,
    ),
    # prices
    Window(
        Format("{content_text}"),
        Button(Const("← Назад"), id="si_back_main_p",
               on_click=lambda c, b, m: m.switch_to(StudentInfoSG.main)),
        state=StudentInfoSG.prices,
        getter=get_prices,
    ),
    # info / contacts
    Window(
        Format("{content_text}"),
        Button(Const("← Назад"), id="si_back_main_i",
               on_click=lambda c, b, m: m.switch_to(StudentInfoSG.main)),
        state=StudentInfoSG.info,
        getter=get_info,
    ),
    # teachers list
    Window(
        Format("👩‍🏫 Наші викладачі ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="si_teachers_sel",
                item_id_getter=lambda x: x[0],
                items="teachers",
                on_click=on_teacher_selected,
            ),
            id="si_teachers_scroll",
            width=1,
            height=8,
        ),
        Button(Const("← Назад"), id="si_back_main_t",
               on_click=lambda c, b, m: m.switch_to(StudentInfoSG.main)),
        state=StudentInfoSG.teachers,
        getter=get_teachers,
    ),
    # teacher card
    Window(
        Format(
            "👩‍🏫 {teacher_name}\n"
            "🎓 Спеціалізація: {teacher_spec}\n"
            "📅 Досвід: {teacher_exp} р.\n"
            "📝 {teacher_bio}"
        ),
        Button(Const("← Назад"), id="si_back_teachers",
               on_click=lambda c, b, m: m.switch_to(StudentInfoSG.teachers)),
        state=StudentInfoSG.teacher_card,
        getter=get_teacher_card,
    ),
)
