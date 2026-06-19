from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format


class AdminMenuSG(StatesGroup):
    main = State()


_MENU_ITEMS = [
    ("applications", "📋 Заявки"),
    ("students", "👥 Учні"),
    ("groups", "🏫 Групи"),
    ("schedule", "📅 Розклад"),
    ("teachers", "👨‍🏫 Вчителі"),
    ("my_teacher", "👨‍🏫 Моя панель викладача"),
    ("invites", "🔑 Інвайт для викладача"),
    ("broadcasts", "📢 Розсилки"),
    ("stats", "📊 Статистика"),
    ("content", "📄 Контент"),
    ("payments", "💳 Оплати"),
    ("quizzes", "📋 Тести"),
]


async def get_menu_items(**kwargs) -> dict:
    return {"items": _MENU_ITEMS}


async def on_menu_select(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    if item_id == "applications":
        from bot.dialogs.admin.applications import AdminAppSG
        await manager.start(AdminAppSG.list_view, mode=StartMode.RESET_STACK)
    elif item_id == "students":
        from bot.dialogs.admin.students import StudentMgmtSG
        await manager.start(StudentMgmtSG.list_view, mode=StartMode.RESET_STACK)
    elif item_id == "groups":
        from bot.dialogs.admin.groups import GroupMgmtSG
        await manager.start(GroupMgmtSG.list_view, mode=StartMode.RESET_STACK)
    elif item_id == "schedule":
        from bot.dialogs.admin.schedule import ScheduleMgmtSG
        await manager.start(ScheduleMgmtSG.list_groups, mode=StartMode.RESET_STACK)
    elif item_id == "teachers":
        from bot.dialogs.admin.teacher_proxy import TeacherProxySG
        await manager.start(TeacherProxySG.teacher_list, mode=StartMode.RESET_STACK)
    elif item_id == "my_teacher":
        from bot.dialogs.teacher.menu import TeacherMenuSG
        await manager.start(TeacherMenuSG.main, mode=StartMode.RESET_STACK)
    elif item_id == "invites":
        from bot.dialogs.admin.invite_codes import InviteCodeMgmtSG
        await manager.start(InviteCodeMgmtSG.main, mode=StartMode.RESET_STACK)
    elif item_id == "broadcasts":
        from bot.dialogs.admin.broadcasts import AdminBroadcastSG
        await manager.start(AdminBroadcastSG.target_select, mode=StartMode.RESET_STACK)
    elif item_id == "stats":
        from bot.dialogs.admin.stats import AdminStatsSG
        await manager.start(AdminStatsSG.overview, mode=StartMode.RESET_STACK)
    elif item_id == "content":
        from bot.dialogs.admin.content import AdminContentSG
        await manager.start(AdminContentSG.list_view, mode=StartMode.RESET_STACK)
    elif item_id == "payments":
        from bot.dialogs.admin.payments import AdminPaymentSG
        await manager.start(AdminPaymentSG.list_view, mode=StartMode.RESET_STACK)
    elif item_id == "quizzes":
        from bot.dialogs.admin.quizzes import AdminQuizSG
        await manager.start(AdminQuizSG.quiz_list, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const("🏫 Адмін-панель\n\nОберіть розділ:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="admin_menu_sel",
                item_id_getter=lambda x: x[0],
                items="items",
                on_click=on_menu_select,
            ),
            id="admin_menu_sg",
            width=1,
            height=5,
        ),
        state=AdminMenuSG.main,
        getter=get_menu_items,
    )
)
