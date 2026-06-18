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


async def on_schedule(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.schedule import ScheduleMgmtSG
    await manager.start(ScheduleMgmtSG.list_groups, mode=StartMode.RESET_STACK)


async def on_teachers(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.teacher_proxy import TeacherProxySG
    await manager.start(TeacherProxySG.teacher_list, mode=StartMode.RESET_STACK)


async def on_my_teacher_panel(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.teacher.menu import TeacherMenuSG
    await manager.start(TeacherMenuSG.main, mode=StartMode.RESET_STACK)


async def on_invites(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.invite_codes import InviteCodeMgmtSG
    await manager.start(InviteCodeMgmtSG.main, mode=StartMode.RESET_STACK)


async def on_broadcasts(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.broadcasts import AdminBroadcastSG
    await manager.start(AdminBroadcastSG.target_select, mode=StartMode.RESET_STACK)


async def on_stats(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.stats import AdminStatsSG
    await manager.start(AdminStatsSG.overview, mode=StartMode.RESET_STACK)


async def on_content(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.admin.content import AdminContentSG
    await manager.start(AdminContentSG.list_view, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const("🏫 Адмін-панель\n\nОберіть розділ:"),
        Button(Const("📋 Заявки"), id="btn_applications", on_click=on_applications),
        Button(Const("👥 Учні"), id="btn_students", on_click=on_students),
        Button(Const("🏫 Групи"), id="btn_groups", on_click=on_groups),
        Button(Const("📅 Розклад"), id="btn_schedule", on_click=on_schedule),
        Button(Const("👨‍🏫 Вчителі"), id="btn_teachers", on_click=on_teachers),
        Button(Const("👨‍🏫 Моя панель викладача"), id="btn_my_teacher", on_click=on_my_teacher_panel),
        Button(Const("🔑 Інвайт для викладача"), id="btn_invites", on_click=on_invites),
        Button(Const("📢 Розсилки"), id="btn_broadcasts", on_click=on_broadcasts),
        Button(Const("📊 Статистика"), id="btn_stats", on_click=on_stats),
        Button(Const("📄 Контент"), id="btn_content", on_click=on_content),
        state=AdminMenuSG.main,
    )
)
