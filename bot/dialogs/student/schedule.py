from typing import Any
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
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


async def get_student_schedule(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_data = dialog_manager.middleware_data["user_data"]
    user_id = user_data["id"]

    student = await api_client.get_student(user_id)
    group_names = student.get("group_names", [])

    all_groups = await api_client.get_groups()
    group_ids = [g["id"] for g in all_groups if g["name"] in group_names]

    now = datetime.now(tz=timezone.utc)
    to_dt = now + timedelta(days=7)

    all_lessons = []
    for gid in group_ids:
        lessons = await api_client.get_lessons(
            group_id=gid,
            from_dt=now.isoformat(),
            to_dt=to_dt.isoformat(),
            status="scheduled",
        )
        for l in lessons:
            l["_group_name"] = next(
                (g["name"] for g in all_groups if g["id"] == gid), "Група"
            )
            all_lessons.append(l)

    all_lessons.sort(key=lambda l: l["scheduled_at"])

    items = []
    for l in all_lessons:
        scheduled = datetime.fromisoformat(l["scheduled_at"])
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=ZoneInfo("UTC"))
        date_str = _format_kyiv_date(scheduled)
        zoom_icon = " 🔗" if l.get("zoom_link") else ""
        label = f"{date_str}{zoom_icon} — {l['_group_name']}"
        items.append((str(l["id"]), label))

    dialog_manager.dialog_data["_lessons_cache"] = {
        str(l["id"]): l for l in all_lessons
    }

    return {
        "lessons": items,
        "count": len(items),
    }


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
        Format("📅 Ваш розклад на 7 днів ({count} занять):"),
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
