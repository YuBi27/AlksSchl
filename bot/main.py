import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram_dialog import setup_dialogs
from aiohttp import web
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
from bot.dialogs.admin import quizzes as admin_quizzes
from bot.dialogs.teacher import quizzes as teacher_quizzes
from bot.dialogs.student import quizzes as student_quizzes
from bot.tasks.reminders import reminder_loop
from bot.tasks.schedule_generator import schedule_generator_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_dispatcher(bot: Bot, redis: Redis, api_client: APIClient) -> Dispatcher:
    storage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_destiny=True))
    dp = Dispatcher(storage=storage)

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
    dp.include_router(admin_quizzes.dialog)
    dp.include_router(teacher_quizzes.dialog)
    dp.include_router(student_quizzes.dialog)

    setup_dialogs(dp)
    dp["bot"] = bot
    return dp


async def on_startup(bot: Bot, api_client: APIClient, redis: Redis, dp: Dispatcher) -> None:
    if settings.webhook_url:
        full_webhook_url = f"{settings.webhook_url.rstrip('/')}{settings.webhook_path}"
        await bot.set_webhook(full_webhook_url)
        logger.info(f"Webhook set to {full_webhook_url}")
    asyncio.create_task(reminder_loop(bot, api_client, redis))
    asyncio.create_task(schedule_generator_loop(api_client))
    logger.info("Bot started")


async def on_shutdown(bot: Bot, api_client: APIClient) -> None:
    if settings.webhook_url:
        await bot.delete_webhook()
    await api_client.close()
    await bot.session.close()


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    redis = Redis.from_url(settings.redis_url)
    api_client = APIClient(base_url=settings.api_url, secret=settings.bot_secret)
    await api_client.start()

    dp = build_dispatcher(bot, redis, api_client)

    if settings.webhook_url:
        # --- Webhook mode ---
        app = web.Application()

        async def _startup(_app):
            await on_startup(bot, api_client, redis, dp)

        async def _shutdown(_app):
            await on_shutdown(bot, api_client)

        app.on_startup.append(_startup)
        app.on_shutdown.append(_shutdown)

        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=settings.webhook_path)
        setup_application(app, dp, bot=bot)

        logger.info(f"Starting webhook on {settings.webhook_host}:{settings.webhook_port}")
        web.run_app(app, host=settings.webhook_host, port=settings.webhook_port)
    else:
        # --- Polling mode (fallback) ---
        try:
            await on_startup(bot, api_client, redis, dp)
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            await on_shutdown(bot, api_client)


if __name__ == "__main__":
    asyncio.run(main())
