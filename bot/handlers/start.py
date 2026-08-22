from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram_dialog import DialogManager, StartMode
from bot.dialogs.registration.language import LanguageSG

router = Router()

MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📋 Меню")]],
    resize_keyboard=True,
    persistent=True,
)


async def _open_menu(message: Message, user_data: dict, dialog_manager: DialogManager):
    role = user_data.get("role", "student")
    status = user_data.get("status", "pending")

    if role == "admin":
        from bot.dialogs.admin.menu import AdminMenuSG
        await dialog_manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)
        return

    if role == "teacher" and status == "active":
        from bot.dialogs.teacher.menu import TeacherMenuSG
        await dialog_manager.start(TeacherMenuSG.main, mode=StartMode.RESET_STACK)
        return

    if status == "active":
        from bot.dialogs.student.menu import StudentMenuSG
        await dialog_manager.start(StudentMenuSG.main, mode=StartMode.RESET_STACK)
        return

    await dialog_manager.start(LanguageSG.select, mode=StartMode.RESET_STACK)


@router.message(CommandStart())
async def cmd_start(message: Message, user_data: dict, dialog_manager: DialogManager):
    await message.answer("👋", reply_markup=MENU_KEYBOARD)
    await _open_menu(message, user_data, dialog_manager)


@router.message(Command("menu"))
async def cmd_menu(message: Message, user_data: dict, dialog_manager: DialogManager):
    await _open_menu(message, user_data, dialog_manager)


@router.message(F.text == "📋 Меню")
async def btn_menu(message: Message, user_data: dict, dialog_manager: DialogManager):
    await _open_menu(message, user_data, dialog_manager)
