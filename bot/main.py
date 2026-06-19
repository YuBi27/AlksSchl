import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram_dialog import setup_dialogs
from redis.asyncio import Redis
from bot.config import settings
from bot.services.api_client import APIClient
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.api_client import APIClientMiddleware
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.i18n import setup_i18n
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.handlers import start, blocked
from bot.dialogs.registration import language, agreements, student, teacher
from bot.dialogs.admin import applications, menu, students as admin_students, groups as admin_groups
from bot.dialogs.admin import schedule as admin_schedule
from bot.dialogs.admin import invite_codes as admin_invite_codes
from bot.dialogs.admin.excel_import import router as excel_router
from bot.dialogs.student import menu as student_menu, schedule as student_schedule
from bot.dialogs.student import homework as student_homework, profile as student_profile
from bot.dialogs.teacher import menu as teacher_menu, lessons as teacher_lessons
from bot.dialogs.teacher import homework as teacher_homework, students as teacher_students
from bot.dialogs.teacher import groups as teacher_groups
from bot.dialogs.admin import teacher_proxy
from bot.dialogs.admin import broadcasts as admin_broadcasts, stats as admin_stats, content as admin_content
from bot.dialogs.student import info as student_info
from bot.dialogs.teacher import broadcasts as teacher_broadcasts
from bot.dialogs.admin import payments as admin_payments
from bot.dialogs.student import payments as student_payments
from bot.tasks.reminders import reminder_loop
from bot.tasks.schedule_generator import schedule_generator_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_destiny=True))
    dp = Dispatcher(storage=storage)

    api_client = APIClient(base_url=settings.api_url, secret=settings.bot_secret)
    await api_client.start()

    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(APIClientMiddleware(api_client=api_client))
    dp.update.outer_middleware(AuthMiddleware(admin_ids=settings.admin_id_list))
    setup_i18n(dp)
    dp.update.outer_middleware(ThrottlingMiddleware(redis=redis))

    dp.include_router(start.router)
    dp.include_router(blocked.router)
    dp.include_router(excel_router)
    dp.include_router(language.dialog)
    dp.include_router(agreements.dialog)
    dp.include_router(student.dialog)
    dp.include_router(teacher.dialog)
    dp.include_router(applications.dialog)
    dp.include_router(menu.dialog)
    dp.include_router(admin_students.dialog)
    dp.include_router(admin_groups.dialog)
    dp.include_router(admin_schedule.dialog)
    dp.include_router(student_menu.dialog)
    dp.include_router(student_schedule.dialog)
    dp.include_router(student_homework.dialog)
    dp.include_router(student_profile.dialog)
    dp.include_router(teacher_menu.dialog)
    dp.include_router(teacher_lessons.dialog)
    dp.include_router(teacher_homework.dialog)
    dp.include_router(teacher_students.dialog)
    dp.include_router(teacher_groups.dialog)
    dp.include_router(teacher_proxy.dialog)
    dp.include_router(admin_invite_codes.dialog)
    dp.include_router(admin_broadcasts.dialog)
    dp.include_router(admin_stats.dialog)
    dp.include_router(admin_content.dialog)
    dp.include_router(student_info.dialog)
    dp.include_router(teacher_broadcasts.dialog)
    dp.include_router(admin_payments.dialog)
    dp.include_router(student_payments.dialog)

    setup_dialogs(dp)

    dp["bot"] = bot

    asyncio.create_task(reminder_loop(bot, api_client, redis))
    asyncio.create_task(schedule_generator_loop(api_client))

    try:
        logger.info("Bot started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await api_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
