from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.func(lambda msg: True))
async def blocked_message(message: Message, user_data: dict | None = None):
    if not user_data:
        return
    status = user_data.get("status")
    if status == "pending":
        await message.answer("⏳ Вашу заявку ще не підтверджено. Очікуйте рішення адміністратора.")
    elif status == "banned":
        await message.answer("🚫 Ваш доступ заблоковано. Зверніться до адміністратора.")
    elif status == "inactive":
        await message.answer("❌ Ваш акаунт деактивовано.")
