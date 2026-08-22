import logging
from aiogram import Bot
from bot.services.api_client import APIClient

logger = logging.getLogger(__name__)


async def notify_group_students(
    bot: Bot,
    api_client: APIClient,
    group_id: int,
    text: str,
) -> None:
    """Send a message to all active students in the given group."""
    try:
        students = await api_client.get_group_students(group_id)
    except Exception as e:
        logger.warning("notify_group_students: failed to get students for group %d: %s", group_id, e)
        return
    for s in students:
        tg_id = s.get("telegram_id", 0)
        if tg_id and tg_id > 0:
            try:
                await bot.send_message(tg_id, text, parse_mode="HTML")
            except Exception as e:
                logger.warning("notify_group_students: failed to send to %d: %s", tg_id, e)


async def notify_admins(
    bot: Bot,
    admin_ids: list[int],
    text: str,
) -> None:
    """Send a message to all admins."""
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logger.warning("notify_admins: failed to send to %d: %s", admin_id, e)


async def notify_user(bot: Bot, telegram_id: int, text: str, parse_mode: str = "HTML") -> None:
    """Send a message to a single user, swallowing errors."""
    if not telegram_id or telegram_id <= 0:
        return
    try:
        await bot.send_message(telegram_id, text, parse_mode=parse_mode)
    except Exception as e:
        logger.warning("notify_user: failed to send to %d: %s", telegram_id, e)
