import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
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
from bot.dialogs.admin import applications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)
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
    dp.include_router(language.dialog)
    dp.include_router(agreements.dialog)
    dp.include_router(student.dialog)
    dp.include_router(teacher.dialog)
    dp.include_router(applications.dialog)

    setup_dialogs(dp)

    dp["bot"] = bot

    try:
        logger.info("Bot started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await api_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
