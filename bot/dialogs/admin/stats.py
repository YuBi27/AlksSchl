from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format


class AdminStatsSG(StatesGroup):
    overview = State()


async def get_stats_overview(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    data = await api_client.get_stats_overview()

    attendance_lines = "\n".join(
        f"  • {g['group_name']}: {g['percent']}%"
        for g in data.get("attendance_by_group", [])
    ) or "  (немає даних)"

    stats_text = (
        f"📊 Статистика школи\n\n"
        f"👥 Учні: {data.get('total_students', 0)} активних / {data.get('pending_students', 0)} очікують\n"
        f"🏫 Груп: {data.get('total_groups', 0)}\n\n"
        f"📅 Уроків сьогодні: {data.get('lessons_today', 0)}\n"
        f"📅 Уроків цього тижня: {data.get('lessons_this_week', 0)}\n\n"
        f"📚 ДЗ прострочених: {data.get('overdue_homework', 0)}\n"
        f"📚 ДЗ на цей тиждень: {data.get('hw_due_this_week', 0)}\n\n"
        f"📊 Відвідуваність (30 днів):\n{attendance_lines}"
    )

    return {"stats_text": stats_text}


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("{stats_text}"),
        Button(Const("← Меню"), id="stats_back_menu", on_click=on_back_to_menu),
        state=AdminStatsSG.overview,
        getter=get_stats_overview,
    )
)
