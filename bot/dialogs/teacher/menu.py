from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format


class TeacherMenuSG(StatesGroup):
    main = State()


_MENU_ITEMS = [
    ("lessons", "📋 Заняття"),
    ("homework", "📝 ДЗ"),
    ("students", "👤 Учні"),
    ("groups", "🏫 Мої групи"),
    ("schedule", "📅 Розклад"),
    ("broadcasts", "📢 Повідомлення групі"),
    ("quizzes", "📋 Тести"),
]


async def on_start(start_data: dict, manager: DialogManager) -> None:
    if isinstance(start_data, dict) and "teacher_override_id" in start_data:
        manager.dialog_data["teacher_override_id"] = start_data["teacher_override_id"]


async def get_menu_items(**kwargs) -> dict:
    return {"items": _MENU_ITEMS}


async def on_menu_select(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    override_id = manager.dialog_data.get("teacher_override_id")
    data = {"teacher_override_id": override_id} if override_id else {}

    if item_id == "lessons":
        from bot.dialogs.teacher.lessons import TeacherLessonSG
        await manager.start(TeacherLessonSG.list_groups, mode=StartMode.RESET_STACK, data=data)
    elif item_id == "homework":
        from bot.dialogs.teacher.homework import TeacherHomeworkSG
        await manager.start(TeacherHomeworkSG.hw_list, mode=StartMode.RESET_STACK, data=data)
    elif item_id == "students":
        from bot.dialogs.teacher.students import TeacherStudentSG
        await manager.start(TeacherStudentSG.student_list, mode=StartMode.RESET_STACK, data=data)
    elif item_id == "groups":
        from bot.dialogs.teacher.groups import TeacherGroupSG
        await manager.start(TeacherGroupSG.list_view, mode=StartMode.RESET_STACK, data=data)
    elif item_id == "schedule":
        from bot.dialogs.admin.schedule import ScheduleMgmtSG
        sched_data = {"origin": "teacher"}
        if override_id:
            sched_data["teacher_override_id"] = override_id
        await manager.start(ScheduleMgmtSG.list_groups, mode=StartMode.RESET_STACK, data=sched_data)
    elif item_id == "broadcasts":
        from bot.dialogs.teacher.broadcasts import TeacherBroadcastSG
        await manager.start(TeacherBroadcastSG.group_select, mode=StartMode.RESET_STACK, data=data)
    elif item_id == "quizzes":
        from bot.dialogs.teacher.quizzes import TeacherQuizSG
        await manager.start(TeacherQuizSG.quiz_list, mode=StartMode.RESET_STACK, data=data)


dialog = Dialog(
    Window(
        Const("👨‍🏫 Панель викладача\n\nОберіть розділ:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="teacher_menu_sel",
                item_id_getter=lambda x: x[0],
                items="items",
                on_click=on_menu_select,
            ),
            id="teacher_menu_sg",
            width=1,
            height=5,
        ),
        state=TeacherMenuSG.main,
        getter=get_menu_items,
    ),
    on_start=on_start,
)
