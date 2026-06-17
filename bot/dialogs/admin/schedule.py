from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

KYIV_TZ = ZoneInfo("Europe/Kyiv")

DAYS_UK = [
    ("0", "Понеділок"),
    ("1", "Вівторок"),
    ("2", "Середа"),
    ("3", "Четвер"),
    ("4", "П'ятниця"),
    ("5", "Субота"),
    ("6", "Неділя"),
]

DAY_NAMES = {str(i): name for i, name in enumerate(
    ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
)}


class ScheduleMgmtSG(StatesGroup):
    list_groups = State()
    group_schedule = State()
    lesson_card = State()
    edit_lesson_datetime = State()
    edit_lesson_zoom = State()
    template_list = State()
    template_day = State()
    template_time = State()
    template_duration = State()


# --- Getters ---

async def get_groups_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    groups = await api_client.get_groups()
    items = [(str(g["id"]), g["name"]) for g in groups]
    return {"groups": items, "count": len(groups)}


async def get_group_schedule(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("group_id", 0)
    group = await api_client.get_group(group_id)

    from datetime import timedelta, timezone
    now = datetime.now(tz=timezone.utc)
    to_dt = now + timedelta(days=14)
    lessons = await api_client.get_lessons(
        group_id=group_id,
        from_dt=now.isoformat(),
        to_dt=to_dt.isoformat(),
    )

    items = []
    for l in lessons:
        scheduled = datetime.fromisoformat(l["scheduled_at"]).astimezone(KYIV_TZ)
        zoom_icon = "🔗" if l.get("zoom_link") else "—"
        status_icon = "❌" if l["status"] == "cancelled" else ""
        label = f"{scheduled.strftime('%d.%m %H:%M')} {zoom_icon} {status_icon}".strip()
        items.append((str(l["id"]), label))

    return {
        "group_name": group.get("name", "—"),
        "lessons": items,
        "count": len(lessons),
    }


async def get_lesson_card(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    lesson_id = dialog_manager.dialog_data.get("lesson_id", 0)
    lesson = await api_client.get_lesson(lesson_id)
    scheduled = datetime.fromisoformat(lesson["scheduled_at"]).astimezone(KYIV_TZ)
    return {
        "lesson_id": lesson_id,
        "scheduled_str": scheduled.strftime("%d.%m.%Y о %H:%M"),
        "duration": lesson["duration_min"],
        "zoom_link": lesson.get("zoom_link") or "не вказано",
        "status": lesson["status"],
    }


async def get_template_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("group_id", 0)
    schedules = await api_client.get_schedules(group_id)
    items = [
        (str(s["id"]), f"{DAY_NAMES.get(str(s['day_of_week']), '?')} {s['start_time'][:5]} ({s['duration_min']} хв)")
        for s in schedules
    ]
    return {"templates": items, "count": len(schedules)}


# --- Navigation handlers ---

async def on_select_group(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["group_id"] = int(item_id)
    await manager.switch_to(ScheduleMgmtSG.group_schedule)


async def on_select_lesson(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["lesson_id"] = int(item_id)
    await manager.switch_to(ScheduleMgmtSG.lesson_card)


async def on_back_to_groups(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(ScheduleMgmtSG.list_groups)


async def on_back_to_schedule(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(ScheduleMgmtSG.group_schedule)


async def on_back_to_lesson(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(ScheduleMgmtSG.lesson_card)


async def on_open_templates(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(ScheduleMgmtSG.template_list)


async def on_edit_lesson(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(ScheduleMgmtSG.edit_lesson_datetime)


# --- Lesson edit handlers ---

async def on_lesson_datetime_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    try:
        dt_kyiv = datetime.strptime(value.strip(), "%d.%m.%Y %H:%M")
        dt_utc = dt_kyiv.replace(tzinfo=KYIV_TZ).astimezone(ZoneInfo("UTC"))
        manager.dialog_data["new_scheduled_at"] = dt_utc.isoformat()
    except ValueError:
        await message.answer("❌ Формат: ДД.ММ.РРРР ГГ:ХХ (наприклад 18.06.2026 17:00)")
        return
    await manager.switch_to(ScheduleMgmtSG.edit_lesson_zoom)


async def on_lesson_zoom_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    manager.dialog_data["new_zoom_link"] = value.strip()
    await _save_lesson(manager)


async def on_skip_zoom(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("new_zoom_link", None)
    await _save_lesson(manager)


async def _save_lesson(manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    lesson_id = manager.dialog_data["lesson_id"]
    kwargs = {}
    if "new_scheduled_at" in manager.dialog_data:
        kwargs["scheduled_at"] = manager.dialog_data.pop("new_scheduled_at")
    if "new_zoom_link" in manager.dialog_data:
        kwargs["zoom_link"] = manager.dialog_data.pop("new_zoom_link")
    if kwargs:
        await api_client.update_lesson(lesson_id, **kwargs)
    await manager.switch_to(ScheduleMgmtSG.lesson_card)


async def on_cancel_lesson(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    lesson_id = manager.dialog_data["lesson_id"]
    await api_client.cancel_lesson(lesson_id)
    await callback.answer("✅ Заняття скасовано")
    await manager.switch_to(ScheduleMgmtSG.group_schedule)


# --- Template create handlers ---

async def on_new_template(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("new_day", None)
    manager.dialog_data.pop("new_time", None)
    manager.dialog_data.pop("new_duration", None)
    await manager.switch_to(ScheduleMgmtSG.template_day)


async def on_day_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["new_day"] = int(item_id)
    await manager.switch_to(ScheduleMgmtSG.template_time)


async def on_time_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    try:
        datetime.strptime(value.strip(), "%H:%M")
        manager.dialog_data["new_time"] = value.strip()
    except ValueError:
        await message.answer("❌ Формат: ГГ:ХХ (наприклад 17:00)")
        return
    await manager.switch_to(ScheduleMgmtSG.template_duration)


async def on_duration_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    try:
        dur = int(value.strip())
        assert 1 <= dur <= 480
        manager.dialog_data["new_duration"] = dur
    except (ValueError, AssertionError):
        await message.answer("❌ Введіть кількість хвилин (1–480)")
        return
    await _save_template(manager)


async def on_duration_default(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data["new_duration"] = 60
    await _save_template(manager)


async def _save_template(manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    group_id = manager.dialog_data["group_id"]
    day = manager.dialog_data["new_day"]
    start_time = manager.dialog_data["new_time"]
    duration = manager.dialog_data.get("new_duration", 60)
    await api_client.create_schedule(group_id, day, start_time, duration)
    await manager.switch_to(ScheduleMgmtSG.template_list)


# --- Dialog windows ---

async def _back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("📅 Розклад — оберіть групу ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="sched_groups_sel",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_select_group,
            ),
            id="sched_groups_scroll",
            width=1,
            height=8,
        ),
        Button(Const("← Меню"), id="back_menu_sched", on_click=_back_to_menu),
        state=ScheduleMgmtSG.list_groups,
        getter=get_groups_list,
    ),
    Window(
        Format("📅 {group_name} — наступні 14 днів ({count} занять):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="lessons_sel",
                item_id_getter=lambda x: x[0],
                items="lessons",
                on_click=on_select_lesson,
            ),
            id="lessons_scroll",
            width=1,
            height=8,
        ),
        Row(
            Button(Const("⚙️ Шаблони"), id="open_templates", on_click=on_open_templates),
            Button(Const("← Назад"), id="back_groups", on_click=on_back_to_groups),
        ),
        state=ScheduleMgmtSG.group_schedule,
        getter=get_group_schedule,
    ),
    Window(
        Format(
            "📌 Заняття\n"
            "📅 {scheduled_str}\n"
            "⏱ {duration} хв\n"
            "🔗 {zoom_link}\n"
            "🔘 Статус: {status}"
        ),
        Row(
            Button(Const("✏️ Редагувати"), id="edit_lesson", on_click=on_edit_lesson),
            Button(Const("❌ Скасувати"), id="cancel_lesson_btn", on_click=on_cancel_lesson),
        ),
        Button(Const("← Назад"), id="back_to_sched", on_click=on_back_to_schedule),
        state=ScheduleMgmtSG.lesson_card,
        getter=get_lesson_card,
    ),
    Window(
        Const("✏️ Введіть нову дату та час заняття (ДД.ММ.РРРР ГГ:ХХ):"),
        TextInput(id="lesson_dt_input", on_success=on_lesson_datetime_entered),
        Button(Const("← Назад"), id="back_lesson_dt", on_click=on_back_to_lesson),
        state=ScheduleMgmtSG.edit_lesson_datetime,
    ),
    Window(
        Const("🔗 Введіть Zoom-посилання для цього заняття:"),
        TextInput(id="lesson_zoom_input", on_success=on_lesson_zoom_entered),
        Row(
            Button(Const("⏭ Пропустити"), id="skip_zoom", on_click=on_skip_zoom),
            Button(Const("← Назад"), id="back_lesson_zoom", on_click=on_back_to_lesson),
        ),
        state=ScheduleMgmtSG.edit_lesson_zoom,
    ),
    Window(
        Format("⚙️ Шаблони групи ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="templates_sel",
                item_id_getter=lambda x: x[0],
                items="templates",
                on_click=lambda c, w, m, i: None,
            ),
            id="templates_scroll",
            width=1,
            height=6,
        ),
        Row(
            Button(Const("➕ Новий шаблон"), id="new_template", on_click=on_new_template),
            Button(Const("← Назад"), id="back_sched_tmpl", on_click=on_back_to_schedule),
        ),
        state=ScheduleMgmtSG.template_list,
        getter=get_template_list,
    ),
    Window(
        Const("📅 Оберіть день тижня:"),
        Select(
            Format("{item[1]}"),
            id="day_sel",
            item_id_getter=lambda x: x[0],
            items="days",
            on_click=on_day_selected,
        ),
        Button(Const("← Назад"), id="back_tmpl_day", on_click=lambda c, b, m: m.switch_to(ScheduleMgmtSG.template_list)),
        state=ScheduleMgmtSG.template_day,
        getter=lambda **_: {"days": DAYS_UK},
    ),
    Window(
        Const("🕐 Введіть час початку (ГГ:ХХ, наприклад 17:00):"),
        TextInput(id="time_input", on_success=on_time_entered),
        Button(Const("← Назад"), id="back_tmpl_time", on_click=lambda c, b, m: m.switch_to(ScheduleMgmtSG.template_day)),
        state=ScheduleMgmtSG.template_time,
    ),
    Window(
        Const("⏱ Введіть тривалість у хвилинах:"),
        TextInput(id="duration_input", on_success=on_duration_entered),
        Button(Const("60 хв (дефолт)"), id="dur_default", on_click=on_duration_default),
        state=ScheduleMgmtSG.template_duration,
    ),
)
