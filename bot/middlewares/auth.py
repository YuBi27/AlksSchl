from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from bot.services.api_client import APIClient


class AuthMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        api_client: APIClient = data["api_client"]
        user_data = await api_client.get_or_create_user(user.id, user.username)

        if user.id in self.admin_ids:
            user_data = {**user_data, "role": "admin", "status": "active"}
        elif user_data.get("role") == "admin":
            # User had admin role in DB but is no longer in admin_ids — downgrade
            user_data = {**user_data, "role": "student"}

        data["user_data"] = user_data

        status = data["user_data"].get("status", "pending")
        if status in ("pending", "banned", "inactive"):
            data["blocked_status"] = status

        return await handler(event, data)
