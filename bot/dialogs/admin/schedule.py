from typing import Any
from datetime import datetime, timedelta, timezone
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
    template_card = State()
    template_day = State()
    template_time = State()
    template_duration = State()
    individual_students = State()
    individual_schedule = State()
    new_ind_dt = State()
    new_ind_dur = State()


# --- Helpers ---

def _trunc(text: str, max_len: int = 58) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


async def _get_days(**kwargs) -> dict:
    return {"days": DAYS_UK}


def _teacher_id(manager: DialogManager) -> int | None:
    return manager.dialog_data.get("teacher_override_id") or (
        manager.middleware_data["user_data"]["id"]
        if manager.dialog_data.get("origin") == "teacher"
        else None
    )


def _week_bounds(week_offset: int) -> tuple[datetime, datetime, str]:
    """UTC bounds and Kyiv label for the week at `week_offset` from current."""
    now_kyiv = datetime.now(tz=KYIV_TZ)
    monday = (now_kyiv - timedelta(days=now_kyiv.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=6)
    label = f"{monday.strftime('%d.%m')}–{sunday.strftime('%d.%m')}"
    if week_offset == 0:
        label += " (поточний)"
    from_utc = monday.astimezone(timezone.utc)
    to_utc = (monday + timedelta(days=7)).astimezone(timezone.utc)
    return from_utc, to_utc, label


DAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]


def _lesson_label(l: dict) -> str:
    scheduled = datetime.fromisoformat(l["scheduled_at"]).astimezone(KYIV_TZ)
    day = DAYS_SHORT[scheduled.weekday()]
    label = f"{day} {scheduled.strftime('%d.%m %H:%M')}"
    if l.get("zoom_link"):
        label += " 🔗"
    if l["status"] == "cancelled":
        label += " ❌ скасовано"
    return label


# --- Getters ---

async def get_groups_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    teacher_id = _teacher_id(dialog_manager)
    if teacher_id is not None:
        own = await api_client.get_groups(teacher_id=teacher_id)
        all_g = await api_client.get_groups()
        seen = {g["id"] for g in own}
        groups = own + [g for g in all_g if g["id"] not in seen and g.get("teacher_id") is None]
    else:
        groups = await api_client.get_groups()
    items = [(str(g["id"]), _trunc(g["name"])) for g in groups]
    return {"groups": items, "count": len(groups)}


async def get_group_schedule(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("group_id", 0)
    group = await api_client.get_group(group_id)

    week_offset = dialog_manager.dialog_data.get("week_offset", 0)
    from_dt, to_dt, week_label = _week_bounds(week_offset)
    lessons = await api_client.get_lessons(
        group_id=group_id,
        from_dt=from_dt.isoformat(),
        to_dt=to_dt.isoformat(),
    )
    lessons.sort(key=lambda l: l["scheduled_at"])
    items = [(str(l["id"]), _lesson_label(l)) for l in lessons]

    return {
        "group_name": group.get("name", "—"),
        "week_label": week_label,
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


async def get_template_card(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    group_id = dialog_manager.dialog_data.get("group_id", 0)
    template_id = dialog_manager.dialog_data.get("template_id", 0)
    schedules = await api_client.get_schedules(group_id)
    tmpl = next((s for s in schedules if s["id"] == template_id), {})
    day_name = DAY_NAMES.get(str(tmpl.get("day_of_week", "")), "?")
    return {
        "tmpl_day": day_name,
        "tmpl_time": (tmpl.get("start_time") or "")[:5],
        "tmpl_duration": tmpl.get("duration_min", "?"),
        "template_id": template_id,
    }


async def get_individual_students(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    students = await api_client.get_students(status="active", limit=100)
    items = [
        (str(s["id"]), _trunc(s.get("full_name") or f"Учень #{s['id']}"))
        for s in students
    ]
    return {"students": items, "count": len(students)}


async def get_individual_schedule(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    student_id = dialog_manager.dialog_data.get("individual_student_id", 0)
    student_name = dialog_manager.dialog_data.get("individual_student_name", "—")

    week_offset = dialog_manager.dialog_data.get("ind_week_offset", 0)
    from_dt, to_dt, week_label = _week_bounds(week_offset)
    lessons = await api_client.get_lessons(
        student_user_id=student_id,
        from_dt=from_dt.isoformat(),
        to_dt=to_dt.isoformat(),
    )
    lessons.sort(key=lambda l: l["scheduled_at"])
    items = [(str(l["id"]), _lesson_label(l)) for l in lessons]

    return {
        "student_name": student_name,
        "week_label": week_label,
        "lessons": items,
        "count": len(lessons),
    }


# --- Navigation handlers ---

async def on_select_group(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["group_id"] = int(item_id)
    manager.dialog_data["week_offset"] = 0
    await manager.switch_to(ScheduleMgmtSG.group_schedule)


async def on_prev_week(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["week_offset"] = manager.dialog_data.get("week_offset", 0) - 1
    await manager.switch_to(ScheduleMgmtSG.group_schedule)


async def on_next_week(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["week_offset"] = manager.dialog_data.get("week_offset", 0) + 1
    await manager.switch_to(ScheduleMgmtSG.group_schedule)


async def on_this_week(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["week_offset"] = 0
    await manager.switch_to(ScheduleMgmtSG.group_schedule)


async def on_ind_prev_week(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["ind_week_offset"] = manager.dialog_data.get("ind_week_offset", 0) - 1
    await manager.switch_to(ScheduleMgmtSG.individual_schedule)


async def on_ind_next_week(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["ind_week_offset"] = manager.dialog_data.get("ind_week_offset", 0) + 1
    await manager.switch_to(ScheduleMgmtSG.individual_schedule)


async def on_ind_this_week(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["ind_week_offset"] = 0
    await manager.switch_to(ScheduleMgmtSG.individual_schedule)


async def on_select_lesson(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["lesson_id"] = int(item_id)
    manager.dialog_data["lesson_context"] = "group"
    await manager.switch_to(ScheduleMgmtSG.lesson_card)


async def on_select_ind_lesson(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["lesson_id"] = int(item_id)
    manager.dialog_data["lesson_context"] = "individual"
    await manager.switch_to(ScheduleMgmtSG.lesson_card)


async def on_back_to_groups(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(ScheduleMgmtSG.list_groups)


async def on_back_to_schedule(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    if manager.dialog_data.get("lesson_context") == "individual":
        await manager.switch_to(ScheduleMgmtSG.individual_schedule)
    else:
        await manager.switch_to(ScheduleMgmtSG.group_schedule)


async def on_back_to_lesson(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(ScheduleMgmtSG.lesson_card)


async def on_open_templates(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(ScheduleMgmtSG.template_list)


async def on_edit_datetime(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("new_scheduled_at", None)
    await manager.switch_to(ScheduleMgmtSG.edit_lesson_datetime)


async def on_edit_zoom_start(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("new_zoom_link", None)
    await manager.switch_to(ScheduleMgmtSG.edit_lesson_zoom)


async def on_select_template(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["template_id"] = int(item_id)
    await manager.switch_to(ScheduleMgmtSG.template_card)


async def on_open_individual(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.switch_to(ScheduleMgmtSG.individual_students)


async def on_select_individual_student(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    api_client = manager.middleware_data["api_client"]
    student = await api_client.get_student(int(item_id))
    manager.dialog_data["individual_student_id"] = int(item_id)
    manager.dialog_data["individual_student_name"] = (
        student.get("full_name") or f"Учень #{item_id}"
    )
    manager.dialog_data["ind_week_offset"] = 0
    await manager.switch_to(ScheduleMgmtSG.individual_schedule)


async def on_new_ind_lesson(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("new_ind_scheduled_at", None)
    manager.dialog_data.pop("new_ind_duration", None)
    await manager.switch_to(ScheduleMgmtSG.new_ind_dt)


# --- Lesson edit handlers ---

async def on_lesson_datetime_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    try:
        dt_kyiv = datetime.strptime(value.strip(), "%d.%m.%Y %H:%M")
        dt_utc = dt_kyiv.replace(tzinfo=KYIV_TZ).astimezone(timezone.utc)
    except ValueError:
        await message.answer("❌ Формат: ДД.ММ.РРРР ГГ:ХХ (наприклад 18.06.2026 17:00)")
        await manager.update({})
        return
    api_client = manager.middleware_data["api_client"]
    lesson_id = manager.dialog_data.get("lesson_id", 0)
    lesson = await api_client.get_lesson(lesson_id)
    await api_client.update_lesson(lesson_id, scheduled_at=dt_utc.isoformat())
    await message.answer("✅ Час заняття оновлено")
    bot = manager.middleware_data.get("bot")
    if bot:
        new_dt_str = dt_kyiv.strftime("%d.%m.%Y о %H:%M")
        if lesson.get("group_id"):
            from bot.utils.notifications import notify_group_students
            group = await api_client.get_group(lesson["group_id"])
            await notify_group_students(
                bot, api_client, lesson["group_id"],
                f"📅 <b>Зміна часу заняття</b>\n\n"
                f"👥 Група: {group.get('name', '—')}\n"
                f"🕐 Новий час: {new_dt_str} (за Києвом)"
            )
        elif lesson.get("student_user_id"):
            from bot.utils.notifications import notify_user
            student_user = await api_client.get_user(lesson["student_user_id"])
            await notify_user(
                bot, student_user.get("telegram_id", 0),
                f"📅 <b>Зміна часу індивідуального заняття</b>\n\n"
                f"🕐 Новий час: {new_dt_str} (за Києвом)"
            )
    await manager.switch_to(ScheduleMgmtSG.lesson_card)


async def on_lesson_zoom_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    api_client = manager.middleware_data["api_client"]
    lesson_id = manager.dialog_data.get("lesson_id", 0)
    lesson = await api_client.get_lesson(lesson_id)
    await api_client.update_lesson(lesson_id, zoom_link=value.strip())
    await message.answer("✅ Zoom-посилання оновлено")
    bot = manager.middleware_data.get("bot")
    if bot:
        if lesson.get("group_id"):
            from bot.utils.notifications import notify_group_students
            group = await api_client.get_group(lesson["group_id"])
            await notify_group_students(
                bot, api_client, lesson["group_id"],
                f"🔗 <b>Оновлено Zoom-посилання</b>\n\n"
                f"👥 Група: {group.get('name', '—')}\n"
                f"🔗 {value.strip()}"
            )
        elif lesson.get("student_user_id"):
            from bot.utils.notifications import notify_user
            student_user = await api_client.get_user(lesson["student_user_id"])
            await notify_user(
                bot, student_user.get("telegram_id", 0),
                f"🔗 <b>Оновлено Zoom-посилання для індивідуального заняття</b>\n\n"
                f"🔗 {value.strip()}"
            )
    await manager.switch_to(ScheduleMgmtSG.lesson_card)


async def on_clear_zoom(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    lesson_id = manager.dialog_data.get("lesson_id", 0)
    await api_client.update_lesson(lesson_id, zoom_link=None)
    await callback.answer("🗑 Zoom-посилання видалено")
    await manager.switch_to(ScheduleMgmtSG.lesson_card)


async def on_cancel_lesson(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    lesson_id = manager.dialog_data["lesson_id"]
    lesson = await api_client.get_lesson(lesson_id)
    await api_client.cancel_lesson(lesson_id)
    await callback.answer("✅ Заняття скасовано")
    await callback.message.answer("✅ Заняття скасовано")
    bot = manager.middleware_data.get("bot")
    if bot:
        scheduled = datetime.fromisoformat(lesson["scheduled_at"]).astimezone(KYIV_TZ)
        dt_str = scheduled.strftime("%d.%m.%Y о %H:%M")
        if lesson.get("group_id"):
            from bot.utils.notifications import notify_group_students
            group = await api_client.get_group(lesson["group_id"])
            await notify_group_students(
                bot, api_client, lesson["group_id"],
                f"❌ <b>Заняття скасовано</b>\n\n"
                f"👥 Група: {group.get('name', '—')}\n"
                f"📅 {dt_str} (за Києвом)"
            )
        elif lesson.get("student_user_id"):
            from bot.utils.notifications import notify_user
            student_user = await api_client.get_user(lesson["student_user_id"])
            await notify_user(
                bot, student_user.get("telegram_id", 0),
                f"❌ <b>Індивідуальне заняття скасовано</b>\n\n"
                f"📅 {dt_str} (за Києвом)"
            )
    ctx = manager.dialog_data.get("lesson_context", "group")
    if ctx == "individual":
        await manager.switch_to(ScheduleMgmtSG.individual_schedule)
    else:
        await manager.switch_to(ScheduleMgmtSG.group_schedule)


async def on_delete_template(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    api_client = manager.middleware_data["api_client"]
    template_id = manager.dialog_data.get("template_id", 0)
    await api_client.delete_schedule(template_id)
    await callback.answer("🗑 Шаблон видалено")
    await callback.message.answer("✅ Шаблон розкладу видалено")
    await manager.switch_to(ScheduleMgmtSG.template_list)


# --- Individual lesson create ---

async def on_ind_dt_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    try:
        dt_kyiv = datetime.strptime(value.strip(), "%d.%m.%Y %H:%M")
        dt_utc = dt_kyiv.replace(tzinfo=KYIV_TZ).astimezone(timezone.utc)
        manager.dialog_data["new_ind_scheduled_at"] = dt_utc.isoformat()
    except ValueError:
        await message.answer("❌ Формат: ДД.ММ.РРРР ГГ:ХХ (наприклад 18.06.2026 17:00)")
        return
    await manager.switch_to(ScheduleMgmtSG.new_ind_dur)


async def on_ind_dur_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    try:
        dur = int(value.strip())
        assert 1 <= dur <= 480
    except (ValueError, AssertionError):
        await message.answer("❌ Введіть кількість хвилин (1–480)")
        return
    await _create_ind_lesson(manager, message.answer, duration=dur)


async def on_ind_dur_default(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await _create_ind_lesson(manager, callback.message.answer, duration=60)


async def _create_ind_lesson(manager: DialogManager, answer, duration: int) -> None:
    api_client = manager.middleware_data["api_client"]
    student_id = manager.dialog_data.get("individual_student_id")
    scheduled_at = manager.dialog_data.get("new_ind_scheduled_at")

    await api_client.create_lesson(
        scheduled_at=scheduled_at,
        duration_min=duration,
        student_user_id=student_id,
    )

    bot = manager.middleware_data.get("bot")
    if bot and student_id:
        try:
            from bot.utils.notifications import notify_user
            student_user = await api_client.get_user(student_id)
            tg_id = student_user.get("telegram_id", 0)
            dt_kyiv = datetime.fromisoformat(scheduled_at).astimezone(KYIV_TZ)
            dt_str = dt_kyiv.strftime("%d.%m.%Y о %H:%M")
            await notify_user(
                bot, tg_id,
                f"📅 <b>Нове індивідуальне заняття</b>\n\n"
                f"⏰ {dt_str} (за Києвом)\n"
                f"⏱ {duration} хв"
            )
        except Exception:
            pass

    if answer:
        try:
            await answer("✅ Індивідуальне заняття заплановано!")
        except Exception:
            pass
    await manager.switch_to(ScheduleMgmtSG.individual_schedule)


# --- Template create handlers ---

async def on_new_template(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("new_day", None)
    manager.dialog_data.pop("new_time", None)
    manager.dialog_data.pop("new_duration", None)
    manager.dialog_data.pop("edit_template_id", None)
    await manager.switch_to(ScheduleMgmtSG.template_day)


async def on_edit_template(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data.pop("new_day", None)
    manager.dialog_data.pop("new_time", None)
    manager.dialog_data.pop("new_duration", None)
    manager.dialog_data["edit_template_id"] = manager.dialog_data.get("template_id", 0)
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
    await _save_template(manager, message.answer)


async def on_duration_default(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data["new_duration"] = 60
    await _save_template(manager, callback.message.answer)


async def _save_template(manager: DialogManager, answer=None) -> None:
    api_client = manager.middleware_data["api_client"]
    group_id = manager.dialog_data["group_id"]
    day = manager.dialog_data["new_day"]
    start_time = manager.dialog_data["new_time"]
    duration = manager.dialog_data.get("new_duration", 60)
    edit_id = manager.dialog_data.pop("edit_template_id", None)
    if edit_id:
        await api_client.update_schedule(
            edit_id, day_of_week=day, start_time=start_time, duration_min=duration
        )
        msg = f"✅ Шаблон розкладу оновлено ({start_time}, {duration} хв)"
    else:
        await api_client.create_schedule(group_id, day, start_time, duration)
        msg = f"✅ Шаблон розкладу створено ({start_time}, {duration} хв)"
    if answer:
        try:
            await answer(msg)
        except Exception:
            pass
    await manager.switch_to(ScheduleMgmtSG.template_list)


# --- Dialog on_start + back to menu ---

async def on_start(start_data: dict, manager: DialogManager) -> None:
    if isinstance(start_data, dict):
        if start_data.get("origin") == "teacher":
            manager.dialog_data["origin"] = "teacher"
        if start_data.get("teacher_override_id"):
            manager.dialog_data["teacher_override_id"] = start_data["teacher_override_id"]


async def _back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    if manager.dialog_data.get("origin") == "teacher":
        from bot.dialogs.teacher.menu import TeacherMenuSG
        await manager.start(TeacherMenuSG.main, mode=StartMode.RESET_STACK)
    else:
        from bot.dialogs.admin.menu import AdminMenuSG
        await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


# --- Dialog windows ---

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
            height=7,
        ),
        Button(Const("👤 Індивідуальні заняття"), id="btn_individual", on_click=on_open_individual),
        Button(Const("← Меню"), id="back_menu_sched", on_click=_back_to_menu),
        state=ScheduleMgmtSG.list_groups,
        getter=get_groups_list,
    ),
    Window(
        Format("📅 {group_name} — тиждень {week_label}\nЗанять: {count}"),
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
            Button(Const("◀️"), id="week_prev", on_click=on_prev_week),
            Button(Const("Сьогодні"), id="week_now", on_click=on_this_week),
            Button(Const("▶️"), id="week_next", on_click=on_next_week),
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
            Button(Const("📅 Змінити час"), id="edit_dt", on_click=on_edit_datetime),
            Button(Const("🔗 Змінити Zoom"), id="edit_zoom", on_click=on_edit_zoom_start),
        ),
        Button(Const("❌ Скасувати заняття"), id="cancel_lesson_btn", on_click=on_cancel_lesson),
        Button(Const("← Назад"), id="back_to_sched", on_click=on_back_to_schedule),
        state=ScheduleMgmtSG.lesson_card,
        getter=get_lesson_card,
    ),
    Window(
        Const("📅 Введіть нову дату та час (ДД.ММ.РРРР ГГ:ХХ, наприклад 25.09.2026 17:00):"),
        TextInput(id="lesson_dt_input", on_success=on_lesson_datetime_entered),
        Button(Const("← Назад"), id="back_lesson_dt", on_click=on_back_to_lesson),
        state=ScheduleMgmtSG.edit_lesson_datetime,
    ),
    Window(
        Const("🔗 Введіть нове Zoom-посилання:"),
        TextInput(id="lesson_zoom_input", on_success=on_lesson_zoom_entered),
        Row(
            Button(Const("🗑 Видалити Zoom"), id="clear_zoom", on_click=on_clear_zoom),
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
                on_click=on_select_template,
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
        Format(
            "⚙️ Шаблон\n"
            "📅 День: {tmpl_day}\n"
            "🕐 Час: {tmpl_time}\n"
            "⏱ Тривалість: {tmpl_duration} хв"
        ),
        Row(
            Button(Const("✏️ Редагувати"), id="edit_tmpl", on_click=on_edit_template),
            Button(Const("🗑 Видалити"), id="delete_tmpl", on_click=on_delete_template),
        ),
        Button(Const("← Назад"), id="back_to_tmpl_list", on_click=lambda c, b, m: m.switch_to(ScheduleMgmtSG.template_list)),
        state=ScheduleMgmtSG.template_card,
        getter=get_template_card,
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
        getter=_get_days,
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
    # --- Individual lesson windows ---
    Window(
        Format("👤 Індивідуальні заняття — оберіть учня ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="ind_students_sel",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=on_select_individual_student,
            ),
            id="ind_students_scroll",
            width=1,
            height=8,
        ),
        Button(Const("← Назад"), id="back_ind_to_groups", on_click=on_back_to_groups),
        state=ScheduleMgmtSG.individual_students,
        getter=get_individual_students,
    ),
    Window(
        Format("👤 {student_name} — тиждень {week_label}\nЗанять: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="ind_lessons_sel",
                item_id_getter=lambda x: x[0],
                items="lessons",
                on_click=on_select_ind_lesson,
            ),
            id="ind_lessons_scroll",
            width=1,
            height=7,
        ),
        Row(
            Button(Const("◀️"), id="ind_week_prev", on_click=on_ind_prev_week),
            Button(Const("Сьогодні"), id="ind_week_now", on_click=on_ind_this_week),
            Button(Const("▶️"), id="ind_week_next", on_click=on_ind_next_week),
        ),
        Row(
            Button(Const("➕ Нове заняття"), id="new_ind_lesson", on_click=on_new_ind_lesson),
            Button(Const("← Назад"), id="back_ind_to_students", on_click=lambda c, b, m: m.switch_to(ScheduleMgmtSG.individual_students)),
        ),
        state=ScheduleMgmtSG.individual_schedule,
        getter=get_individual_schedule,
    ),
    Window(
        Const("📅 Введіть дату та час заняття (ДД.ММ.РРРР ГГ:ХХ, наприклад 25.09.2026 17:00):"),
        TextInput(id="ind_dt_input", on_success=on_ind_dt_entered),
        Button(Const("← Назад"), id="back_ind_dt", on_click=lambda c, b, m: m.switch_to(ScheduleMgmtSG.individual_schedule)),
        state=ScheduleMgmtSG.new_ind_dt,
    ),
    Window(
        Const("⏱ Введіть тривалість у хвилинах:"),
        TextInput(id="ind_dur_input", on_success=on_ind_dur_entered),
        Button(Const("60 хв (дефолт)"), id="ind_dur_default", on_click=on_ind_dur_default),
        Button(Const("← Назад"), id="back_ind_dur", on_click=lambda c, b, m: m.switch_to(ScheduleMgmtSG.new_ind_dt)),
        state=ScheduleMgmtSG.new_ind_dur,
    ),
    on_start=on_start,
)
