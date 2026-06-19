from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const


class TeacherMenuSG(StatesGroup):
    main = State()


async def on_start(start_data: dict, manager: DialogManager) -> None:
    if isinstance(start_data, dict) and "teacher_override_id" in start_data:
        manager.dialog_data["teacher_override_id"] = start_data["teacher_override_id"]


def _data(manager: DialogManager) -> dict:
    oid = manager.dialog_data.get("teacher_override_id")
    return {"teacher_override_id": oid} if oid else {}


def _is_admin_mode(manager: DialogManager) -> bool:
    return (
        manager.dialog_data.get("teacher_override_id") is not None
        or manager.middleware_data["user_data"]["role"] == "admin"
    )


async def on_lessons(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.teacher.lessons import TeacherLessonSG
    await m.start(TeacherLessonSG.list_groups, mode=StartMode.RESET_STACK, data=_data(m))

async def on_homework(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.teacher.homework import TeacherHomeworkSG
    await m.start(TeacherHomeworkSG.hw_list, mode=StartMode.RESET_STACK, data=_data(m))

async def on_students(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.teacher.students import TeacherStudentSG
    await m.start(TeacherStudentSG.student_list, mode=StartMode.RESET_STACK, data=_data(m))

async def on_groups(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.teacher.groups import TeacherGroupSG
    await m.start(TeacherGroupSG.list_view, mode=StartMode.RESET_STACK, data=_data(m))

async def on_schedule(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.schedule import ScheduleMgmtSG
    d = {"origin": "teacher"}
    oid = m.dialog_data.get("teacher_override_id")
    if oid:
        d["teacher_override_id"] = oid
    await m.start(ScheduleMgmtSG.list_groups, mode=StartMode.RESET_STACK, data=d)

async def on_broadcasts(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.teacher.broadcasts import TeacherBroadcastSG
    await m.start(TeacherBroadcastSG.group_select, mode=StartMode.RESET_STACK, data=_data(m))

async def on_quizzes(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.teacher.quizzes import TeacherQuizSG
    await m.start(TeacherQuizSG.quiz_list, mode=StartMode.RESET_STACK, data=_data(m))

async def on_back_to_admin(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await m.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


async def get_menu_data(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"is_admin": _is_admin_mode(dialog_manager)}


dialog = Dialog(
    Window(
        Const("👨‍🏫 Панель викладача\n\nОберіть розділ:"),
        Row(
            Button(Const("📋 Заняття"),     id="tm_lessons",    on_click=on_lessons),
            Button(Const("📝 ДЗ"),          id="tm_hw",         on_click=on_homework),
        ),
        Row(
            Button(Const("👤 Учні"),        id="tm_students",   on_click=on_students),
            Button(Const("🏫 Мої групи"),   id="tm_groups",     on_click=on_groups),
        ),
        Row(
            Button(Const("📅 Розклад"),     id="tm_schedule",   on_click=on_schedule),
            Button(Const("📢 Розсилки"),    id="tm_bcast",      on_click=on_broadcasts),
        ),
        Button(Const("📋 Тести"),           id="tm_quizzes",    on_click=on_quizzes),
        Button(
            Const("← До адміна"),
            id="tm_back_admin",
            on_click=on_back_to_admin,
            when="is_admin",
        ),
        state=TeacherMenuSG.main,
        getter=get_menu_data,
    ),
    on_start=on_start,
)
