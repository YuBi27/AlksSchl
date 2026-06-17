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


dialog = Dialog(
    Window(
        Const("👨‍🏫 Панель викладача\n\nОберіть розділ:"),
        Button(Const("📋 Заняття"), id="btn_lessons", on_click=on_lessons),
        Button(Const("📝 ДЗ"), id="btn_homework", on_click=on_homework),
        Button(Const("👤 Учні"), id="btn_students", on_click=on_students),
        state=TeacherMenuSG.main,
    ),
    on_start=on_start,
)
