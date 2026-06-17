from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from bot.services.api_client import APIClient


class APIClientMiddleware(BaseMiddleware):
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["api_client"] = self.api_client
        return await handler(event, data)
