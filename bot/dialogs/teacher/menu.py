from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const


class TeacherMenuSG(StatesGroup):
    main = State()


async def on_start(start_data: dict, manager: DialogManager) -> None:
    if isinstance(start_data, dict) and "teacher_override_id" in start_data:
        manager.dialog_data["teacher_override_id"] = start_data["teacher_override_id"]


async def on_lessons(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.teacher.lessons import TeacherLessonSG
    override_id = manager.dialog_data.get("teacher_override_id")
    data = {"teacher_override_id": override_id} if override_id else {}
    await manager.start(TeacherLessonSG.list_groups, mode=StartMode.RESET_STACK, data=data)


async def on_homework(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.teacher.homework import TeacherHomeworkSG
    override_id = manager.dialog_data.get("teacher_override_id")
    data = {"teacher_override_id": override_id} if override_id else {}
    await manager.start(TeacherHomeworkSG.hw_list, mode=StartMode.RESET_STACK, data=data)


async def on_students(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.teacher.students import TeacherStudentSG
    override_id = manager.dialog_data.get("teacher_override_id")
    data = {"teacher_override_id": override_id} if override_id else {}
    await manager.start(TeacherStudentSG.student_list, mode=StartMode.RESET_STACK, data=data)


async def on_schedule(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.admin.schedule import ScheduleMgmtSG
    override_id = manager.dialog_data.get("teacher_override_id")
    data = {"origin": "teacher"}
    if override_id:
        data["teacher_override_id"] = override_id
    await manager.start(ScheduleMgmtSG.list_groups, mode=StartMode.RESET_STACK, data=data)


async def on_groups(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.teacher.groups import TeacherGroupSG
    override_id = manager.dialog_data.get("teacher_override_id")
    data = {"teacher_override_id": override_id} if override_id else {}
    await manager.start(TeacherGroupSG.list_view, mode=StartMode.RESET_STACK, data=data)


async def on_broadcasts(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.teacher.broadcasts import TeacherBroadcastSG
    override_id = manager.dialog_data.get("teacher_override_id")
    data = {"teacher_override_id": override_id} if override_id else {}
    await manager.start(TeacherBroadcastSG.group_select, mode=StartMode.RESET_STACK, data=data)


async def on_quizzes(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.teacher.quizzes import TeacherQuizSG
    override_id = manager.dialog_data.get("teacher_override_id")
    data = {"teacher_override_id": override_id} if override_id else {}
    await manager.start(TeacherQuizSG.quiz_list, mode=StartMode.RESET_STACK, data=data)


dialog = Dialog(
    Window(
        Const("👨‍🏫 Панель викладача\n\nОберіть розділ:"),
        Button(Const("📋 Заняття"), id="btn_lessons", on_click=on_lessons),
        Button(Const("📝 ДЗ"), id="btn_homework", on_click=on_homework),
        Button(Const("👤 Учні"), id="btn_students", on_click=on_students),
        Button(Const("🏫 Мої групи"), id="btn_groups", on_click=on_groups),
        Button(Const("📅 Розклад"), id="btn_schedule", on_click=on_schedule),
        Button(Const("📢 Повідомлення групі"), id="btn_broadcasts", on_click=on_broadcasts),
        Button(Const("📋 Тести"), id="btn_quizzes", on_click=on_quizzes),
        state=TeacherMenuSG.main,
    ),
    on_start=on_start,
)
