from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const


class AdminMenuSG(StatesGroup):
    main = State()


async def on_applications(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.applications import AdminAppSG
    await manager.start(AdminAppSG.list_view, mode=StartMode.RESET_STACK)


async def on_students(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.students import StudentMgmtSG
    await manager.start(StudentMgmtSG.list_view, mode=StartMode.RESET_STACK)


async def on_groups(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.groups import GroupMgmtSG
    await manager.start(GroupMgmtSG.list_view, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const("🏫 Адмін-панель\n\nОберіть розділ:"),
        Button(Const("📋 Заявки"), id="btn_applications", on_click=on_applications),
        Button(Const("👥 Учні"), id="btn_students", on_click=on_students),
        Button(Const("🏫 Групи"), id="btn_groups", on_click=on_groups),
        state=AdminMenuSG.main,
    )
)
