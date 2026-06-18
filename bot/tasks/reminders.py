import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from bot.services.api_client import APIClient

logger = logging.getLogger(__name__)
KYIV_TZ = ZoneInfo("Europe/Kyiv")
DAYS_UK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
MONTHS_UK = [
    "", "січня", "лютого", "березня", "квітня", "травня", "червня",
    "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"
]


def _format_kyiv(dt_utc: datetime) -> str:
    dt_kyiv = dt_utc.astimezone(KYIV_TZ)
    day = DAYS_UK[dt_kyiv.weekday()]
    return f"{day}, {dt_kyiv.day} {MONTHS_UK[dt_kyiv.month]} о {dt_kyiv.strftime('%H:%M')}"


def _get_reminder_types(lesson: dict, now: datetime) -> list[str]:
    scheduled = datetime.fromisoformat(lesson["scheduled_at"])
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=ZoneInfo("UTC"))
    delta = (scheduled - now).total_seconds()
    types = []
    if not lesson["reminder_24h_sent"] and delta <= 24 * 3600:
        types.append("24h")
    if not lesson["reminder_2h_sent"] and delta <= 2 * 3600:
        types.append("2h")
    if not lesson["reminder_30m_sent"] and delta <= 30 * 60:
        types.append("30min")
    return types


def _build_reminder_text(lesson: dict, group_name: str, reminder_type: str) -> str:
    scheduled = datetime.fromisoformat(lesson["scheduled_at"])
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=ZoneInfo("UTC"))
    dt_kyiv = scheduled.astimezone(KYIV_TZ)
    time_str = dt_kyiv.strftime("%H:%M")

    when_map = {
        "24h": f"завтра о {time_str}",
        "2h": f"через 2 години о {time_str}",
        "30min": "через 30 хвилин",
    }
    when = when_map[reminder_type]
    zoom = f"\n🔗 {lesson['zoom_link']}" if lesson.get("zoom_link") else ""
    date_str = _format_kyiv(scheduled)

    return (
        f"⏰ Нагадування про заняття!\n\n"
        f"👥 {group_name}\n"
        f"📅 {date_str} ({when}){zoom}\n\n"
        f"Гарного заняття! 🎓"
    )


async def _send_to_user(bot: Bot, telegram_id: int, text: str) -> None:
    if telegram_id <= 0:
        return
    try:
        await bot.send_message(telegram_id, text)
    except Exception as e:
        logger.warning("Failed to send reminder to %d: %s", telegram_id, e)


async def _process_lesson(bot: Bot, api_client: APIClient, lesson: dict) -> None:
    now = datetime.now(tz=ZoneInfo("UTC"))
    reminder_types = _get_reminder_types(lesson, now)
    if not reminder_types:
        return

    try:
        group = await api_client.get_group(lesson["group_id"])
        students = await api_client.get_group_students(lesson["group_id"])
    except Exception as e:
        logger.error("Failed to fetch group data for lesson %d: %s", lesson["id"], e)
        return

    group_name = group.get("name", "Група")

    for reminder_type in reminder_types:
        text = _build_reminder_text(lesson, group_name, reminder_type)

        for student in students:
            await _send_to_user(bot, student["telegram_id"], text)

        teacher_user_id = group.get("teacher_id")
        if teacher_user_id:
            try:
                teacher = await api_client.get_user(teacher_user_id)
                await _send_to_user(bot, teacher["telegram_id"], text)
            except Exception as e:
                logger.warning("Failed to fetch teacher %d: %s", teacher_user_id, e)

        try:
            await api_client.mark_reminder_sent(lesson["id"], reminder_type)
        except Exception as e:
            logger.error("Failed to mark reminder sent for lesson %d: %s", lesson["id"], e)


async def reminder_loop(bot: Bot, api_client: APIClient) -> None:
    """Background task: poll for due reminders every 2 minutes."""
    logger.info("Reminder loop started")
    while True:
        try:
            lessons = await api_client.get_due_reminders()
            for lesson in lessons:
                await _process_lesson(bot, api_client, lesson)
        except Exception as e:
            logger.error("Reminder loop error: %s", e)
        await asyncio.sleep(120)
