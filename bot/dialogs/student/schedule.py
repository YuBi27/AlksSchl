from typing import Any
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

KYIV_TZ = ZoneInfo("Europe/Kyiv")
DAYS_UK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
MONTHS_UK = [
    "", "січня", "лютого", "березня", "квітня", "травня", "червня",
    "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"
]


class StudentScheduleSG(StatesGroup):
    schedule_view = State()
    lesson_detail = State()


def _format_kyiv_date(dt_utc: datetime) -> str:
    dt_k = dt_utc.astimezone(KYIV_TZ)
    day_name = DAYS_UK[dt_k.weekday()]
    return f"{day_name}, {dt_k.day} {MONTHS_UK[dt_k.month]} о {dt_k.strftime('%H:%M')}"


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


async def get_student_schedule(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_data = dialog_manager.middleware_data["user_data"]
    user_id = user_data["id"]

    student = await api_client.get_student(user_id)
    group_names = student.get("group_names", [])

    all_groups = await api_client.get_groups()
    group_ids = [g["id"] for g in all_groups if g["name"] in group_names]

    week_offset = dialog_manager.dialog_data.get("week_offset", 0)
    from_utc, to_utc, week_label = _week_bounds(week_offset)
    now = from_utc
    to_dt = to_utc

    all_lessons = []
    seen_ids: set[int] = set()
    for gid in group_ids:
        lessons = await api_client.get_lessons(
            group_id=gid,
            from_dt=now.isoformat(),
            to_dt=to_dt.isoformat(),
        )
        for l in lessons:
            if l["id"] not in seen_ids:
                seen_ids.add(l["id"])
                l["_group_name"] = next(
                    (g["name"] for g in all_groups if g["id"] == gid), "Група"
                )
                all_lessons.append(l)

    # Also fetch individual lessons for this student
    ind_lessons = await api_client.get_lessons(
        student_user_id=user_id,
        from_dt=now.isoformat(),
        to_dt=to_dt.isoformat(),
    )
    for l in ind_lessons:
        if l["id"] not in seen_ids:
            seen_ids.add(l["id"])
            l["_group_name"] = "Індивідуальне"
            all_lessons.append(l)

    all_lessons.sort(key=lambda l: l["scheduled_at"])

    items = []
    for l in all_lessons:
        scheduled = datetime.fromisoformat(l["scheduled_at"])
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=ZoneInfo("UTC"))
        date_str = _format_kyiv_date(scheduled)
        zoom_icon = " 🔗" if l.get("zoom_link") else ""
        cancelled = " ❌" if l.get("status") == "cancelled" else ""
        label = f"{date_str}{zoom_icon}{cancelled} — {l['_group_name']}"
        items.append((str(l["id"]), label))

    dialog_manager.dialog_data["_lessons_cache"] = {
        str(l["id"]): l for l in all_lessons
    }

    return {
        "lessons": items,
        "count": len(items),
        "week_label": week_label,
    }


async def on_prev_week(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["week_offset"] = manager.dialog_data.get("week_offset", 0) - 1
    await manager.switch_to(StudentScheduleSG.schedule_view)


async def on_next_week(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["week_offset"] = manager.dialog_data.get("week_offset", 0) + 1
    await manager.switch_to(StudentScheduleSG.schedule_view)


async def on_this_week(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["week_offset"] = 0
    await manager.switch_to(StudentScheduleSG.schedule_view)


async def on_select_lesson(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["selected_lesson_id"] = item_id
    await manager.switch_to(StudentScheduleSG.lesson_detail)


async def get_lesson_detail(dialog_manager: DialogManager, **kwargs) -> dict:
    lesson_id = dialog_manager.dialog_data.get("selected_lesson_id")
    cache = dialog_manager.dialog_data.get("_lessons_cache", {})
    lesson = cache.get(lesson_id)
    if not lesson:
        return {
            "group_name": "—", "scheduled_str": "—",
            "duration": 0, "zoom_link": "не вказано", "status": "—"
        }
    scheduled = datetime.fromisoformat(lesson["scheduled_at"])
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=ZoneInfo("UTC"))
    return {
        "group_name": lesson.get("_group_name", "Група"),
        "scheduled_str": _format_kyiv_date(scheduled),
        "duration": lesson["duration_min"],
        "zoom_link": lesson.get("zoom_link") or "не вказано",
        "status": lesson["status"],
    }


async def _back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.student.menu import StudentMenuSG
    await manager.start(StudentMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("📅 Ваш розклад — тиждень {week_label}\nЗанять: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="student_lessons_sel",
                item_id_getter=lambda x: x[0],
                items="lessons",
                on_click=on_select_lesson,
            ),
            id="student_lessons_scroll",
            width=1,
            height=8,
        ),
        Row(
            Button(Const("◀️"), id="st_week_prev", on_click=on_prev_week),
            Button(Const("Сьогодні"), id="st_week_now", on_click=on_this_week),
            Button(Const("▶️"), id="st_week_next", on_click=on_next_week),
        ),
        Button(
            Const("← Назад"),
            id="back_student_menu",
            on_click=_back_to_menu,
        ),
        state=StudentScheduleSG.schedule_view,
        getter=get_student_schedule,
    ),
    Window(
        Format(
            "📌 {group_name}\n"
            "📅 {scheduled_str}\n"
            "⏱ {duration} хв\n"
            "🔗 {zoom_link}\n"
            "🔘 {status}"
        ),
        Button(
            Const("← Назад"),
            id="back_to_schedule",
            on_click=lambda c, b, m: m.switch_to(StudentScheduleSG.schedule_view),
        ),
        state=StudentScheduleSG.lesson_detail,
        getter=get_lesson_detail,
    ),
)
