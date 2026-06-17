from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from bot.dialogs.registration.language import LanguageSG

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user_data: dict, dialog_manager: DialogManager):
    role = user_data.get("role", "student")
    status = user_data.get("status", "pending")

    if role == "admin":
        from bot.dialogs.admin.menu import AdminMenuSG
        await dialog_manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)
        return

    if status == "active":
        await message.answer("👋 Ласкаво просимо! Головне меню буде додано в наступних версіях.")
        return

    await dialog_manager.start(LanguageSG.select, mode=StartMode.RESET_STACK)
