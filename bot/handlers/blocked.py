from aiogram import Router
from aiogram.filters import BaseFilter
from aiogram.types import Message


class BlockedStatusFilter(BaseFilter):
    async def __call__(self, message: Message, user_data: dict | None = None) -> bool:
        if not user_data:
            return False
        return user_data.get("status") in ("pending", "banned")


router = Router()


@router.message(BlockedStatusFilter())
async def blocked_message(message: Message, user_data: dict):
    status = user_data.get("status")
    if status == "pending":
        await message.answer("⏳ Вашу заявку ще не підтверджено. Очікуйте рішення адміністратора.")
    elif status == "banned":
        await message.answer("🚫 Ваш доступ заблоковано. Зверніться до адміністратора.")
