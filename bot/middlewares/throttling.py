from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from redis.asyncio import Redis


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis, rate_limit: float = 1.0):
        self.redis = redis
        self.rate_limit = rate_limit

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        key = f"throttle:{user.id}"
        result = await self.redis.set(key, "1", ex=int(self.rate_limit), nx=True)

        if result is None:
            if isinstance(event, Message):
                await event.answer("⏳ Не так швидко, спробуйте через секунду.")
            return

        return await handler(event, data)
