from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Format, Const


class StudentProfileSG(StatesGroup):
    main = State()


STATUS_EMOJI = {"present": "✅", "late": "🕐", "absent": "❌", "excused": "📋"}


async def get_profile(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_data = dialog_manager.middleware_data["user_data"]
    user_id = user_data["id"]

    student = await api_client.get_student(user_id)
    attendances = await api_client.get_attendances(student_user_id=user_id)
    att_sorted = sorted(attendances, key=lambda a: a.get("created_at", ""), reverse=True)

    total = len(att_sorted)
    present_count = sum(1 for a in att_sorted if a["status"] in ("present", "late"))
    absent_count = sum(1 for a in att_sorted if a["status"] == "absent")
    last_5 = " ".join(STATUS_EMOJI.get(a["status"], "—") for a in att_sorted[:5]) or "—"

    groups = ", ".join(student.get("group_names") or []) or "Не призначений"
    pct = f"{round(present_count / total * 100)}%" if total else "—"

    return {
        "full_name": student.get("full_name") or "—",
        "phone": student.get("phone") or "—",
        "level": student.get("english_level") or "Не вказано",
        "groups": groups,
        "status": student.get("status") or "—",
        "att_total": total,
        "att_present": present_count,
        "att_absent": absent_count,
        "att_pct": pct,
        "last_5": last_5,
    }


async def _back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    from bot.dialogs.student.menu import StudentMenuSG
    await manager.start(StudentMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format(
            "👤 <b>{full_name}</b>\n\n"
            "📱 Телефон: {phone}\n"
            "🎓 Рівень англійської: {level}\n"
            "👥 Групи: {groups}\n"
            "🔘 Статус: {status}\n\n"
            "📊 <b>Відвідуваність:</b>\n"
            "Всього занять: {att_total}\n"
            "Відвідано: {att_present} ({att_pct})\n"
            "Пропущено: {att_absent}\n"
            "Останні 5: {last_5}"
        ),
        Button(Const("← Меню"), id="back_profile_menu", on_click=_back_to_menu),
        state=StudentProfileSG.main,
        getter=get_profile,
    ),
)
