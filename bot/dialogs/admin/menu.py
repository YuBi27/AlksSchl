from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const


class AdminMenuSG(StatesGroup):
    main = State()


async def on_applications(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.applications import AdminAppSG
    await m.start(AdminAppSG.list_view, mode=StartMode.RESET_STACK)

async def on_students(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.students import StudentMgmtSG
    await m.start(StudentMgmtSG.list_view, mode=StartMode.RESET_STACK)

async def on_groups(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.groups import GroupMgmtSG
    await m.start(GroupMgmtSG.list_view, mode=StartMode.RESET_STACK)

async def on_schedule(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.schedule import ScheduleMgmtSG
    await m.start(ScheduleMgmtSG.list_groups, mode=StartMode.RESET_STACK)

async def on_teachers(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.teacher_proxy import TeacherProxySG
    await m.start(TeacherProxySG.teacher_list, mode=StartMode.RESET_STACK)

async def on_my_teacher_panel(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.teacher.menu import TeacherMenuSG
    await m.start(TeacherMenuSG.main, mode=StartMode.RESET_STACK)

async def on_invites(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.invite_codes import InviteCodeMgmtSG
    await m.start(InviteCodeMgmtSG.main, mode=StartMode.RESET_STACK)

async def on_broadcasts(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.broadcasts import AdminBroadcastSG
    await m.start(AdminBroadcastSG.target_select, mode=StartMode.RESET_STACK)

async def on_stats(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.stats import AdminStatsSG
    await m.start(AdminStatsSG.overview, mode=StartMode.RESET_STACK)

async def on_content(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.content import AdminContentSG
    await m.start(AdminContentSG.list_view, mode=StartMode.RESET_STACK)

async def on_payments(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.payments import AdminPaymentSG
    await m.start(AdminPaymentSG.list_view, mode=StartMode.RESET_STACK)

async def on_quizzes(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.quizzes import AdminQuizSG
    await m.start(AdminQuizSG.quiz_list, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const("🏫 Адмін-панель\n\nОберіть розділ:"),
        Row(
            Button(Const("📋 Заявки"),       id="m_apps",      on_click=on_applications),
            Button(Const("👥 Учні"),         id="m_students",  on_click=on_students),
        ),
        Row(
            Button(Const("🏫 Групи"),        id="m_groups",    on_click=on_groups),
            Button(Const("📅 Розклад"),      id="m_schedule",  on_click=on_schedule),
        ),
        Row(
            Button(Const("👨‍🏫 Вчителі"),    id="m_teachers",  on_click=on_teachers),
            Button(Const("👨‍🏫 Моя панель"), id="m_my_teach",  on_click=on_my_teacher_panel),
        ),
        Row(
            Button(Const("🔑 Інвайти"),      id="m_invites",   on_click=on_invites),
            Button(Const("📢 Розсилки"),     id="m_bcast",     on_click=on_broadcasts),
        ),
        Row(
            Button(Const("📊 Статистика"),   id="m_stats",     on_click=on_stats),
            Button(Const("📄 Контент"),      id="m_content",   on_click=on_content),
        ),
        Row(
            Button(Const("💳 Оплати"),       id="m_payments",  on_click=on_payments),
            Button(Const("📋 Тести"),        id="m_quizzes",   on_click=on_quizzes),
        ),
        state=AdminMenuSG.main,
    )
)
