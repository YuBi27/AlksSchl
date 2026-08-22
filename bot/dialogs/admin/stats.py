from typing import Any, Optional
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format


class AdminStatsSG(StatesGroup):
    overview = State()
    att_groups = State()
    att_students = State()
    performance = State()
    pick_group = State()


def _period(manager: DialogManager) -> int:
    return manager.dialog_data.get("period_days", 30)


def _group_id(manager: DialogManager) -> Optional[int]:
    return manager.dialog_data.get("group_id")


def _group_label(manager: DialogManager) -> str:
    name = manager.dialog_data.get("group_name")
    return f"Група: {name}" if name else "Всі групи"


# ---- Getters ----

async def get_overview(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    data = await api_client.get_stats_overview()
    att_lines = "\n".join(
        f"  • {g['group_name']}: {g['percent']}%"
        for g in data.get("attendance_by_group", [])
    ) or "  (немає даних)"
    return {
        "total_students": data.get("total_students", 0),
        "pending_students": data.get("pending_students", 0),
        "total_groups": data.get("total_groups", 0),
        "lessons_today": data.get("lessons_today", 0),
        "lessons_this_week": data.get("lessons_this_week", 0),
        "overdue_homework": data.get("overdue_homework", 0),
        "hw_due_this_week": data.get("hw_due_this_week", 0),
        "att_lines": att_lines,
    }


async def get_att_groups(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    days = _period(dialog_manager)
    data = await api_client.get_attendance_stats(days=days, group_id=_group_id(dialog_manager))
    dialog_manager.dialog_data["_att_raw"] = data
    lines = "\n".join(
        f"  {g['group_name']}: {g['percent']}% ({g['total_lessons']} занять, {g['student_count']} учнів)"
        for g in data.get("by_group", [])
    ) or "  (немає даних)"
    return {
        "days": days,
        "group_label": _group_label(dialog_manager),
        "att_lines": lines,
        "has_students": bool(data.get("by_student")),
    }


async def get_att_students(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data.get("_att_raw", {})
    lines = "\n".join(
        f"  {s.get('full_name') or '—'} ({s.get('group_name') or '—'}): {s['percent']}% "
        f"✅{s['present']} 🕐{s['late']} ❌{s['absent']}"
        for s in data.get("by_student", [])
    ) or "  (немає даних)"
    return {"student_lines": lines, "days": dialog_manager.dialog_data.get("period_days", 30)}


async def get_performance(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    days = _period(dialog_manager)
    data = await api_client.get_performance_stats(days=days, group_id=_group_id(dialog_manager))
    dialog_manager.dialog_data["_perf_raw"] = data
    hw = data.get("homework", {})
    qz = data.get("quizzes", {})
    ranking = data.get("student_ranking", [])
    top3 = "\n".join(
        f"  {i+1}. {s.get('full_name') or '—'} — {s['combined_score']:.1f}"
        for i, s in enumerate(ranking[:3])
    ) or "  (немає даних)"
    return {
        "days": days,
        "group_label": _group_label(dialog_manager),
        "hw_completion": hw.get("completion_rate", 0),
        "hw_submitted": hw.get("submitted_count", 0),
        "hw_assigned": hw.get("assigned_count", 0),
        "quiz_completed": qz.get("completed_count", 0),
        "quiz_avg_pct": qz.get("avg_score_pct", 0),
        "top3": top3,
    }


async def get_pick_group(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    groups = await api_client.get_groups()
    items = [("all", "Всі групи")] + [(str(g["id"]), g["name"]) for g in groups]
    return {"groups": items}


# ---- Handlers ----

async def on_go_att(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminStatsSG.att_groups)


async def on_go_perf(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminStatsSG.performance)


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


async def on_back_overview(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminStatsSG.overview)


async def _set_period(manager: DialogManager, days: int, state: State) -> None:
    manager.dialog_data["period_days"] = days
    await manager.switch_to(state)


async def on_period_30_att(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _set_period(manager, 30, AdminStatsSG.att_groups)

async def on_period_60_att(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _set_period(manager, 60, AdminStatsSG.att_groups)

async def on_period_90_att(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _set_period(manager, 90, AdminStatsSG.att_groups)

async def on_period_30_perf(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _set_period(manager, 30, AdminStatsSG.performance)

async def on_period_60_perf(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _set_period(manager, 60, AdminStatsSG.performance)

async def on_period_90_perf(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _set_period(manager, 90, AdminStatsSG.performance)


async def on_pick_group_att(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["_return_state"] = "att_groups"
    await manager.switch_to(AdminStatsSG.pick_group)

async def on_pick_group_perf(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["_return_state"] = "performance"
    await manager.switch_to(AdminStatsSG.pick_group)


async def on_group_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    if item_id == "all":
        manager.dialog_data["group_id"] = None
        manager.dialog_data["group_name"] = None
    else:
        api_client = manager.middleware_data["api_client"]
        groups = await api_client.get_groups()
        g = next((g for g in groups if str(g["id"]) == item_id), None)
        manager.dialog_data["group_id"] = int(item_id)
        manager.dialog_data["group_name"] = g["name"] if g else item_id

    return_state = manager.dialog_data.get("_return_state", "att_groups")
    state_map = {
        "att_groups": AdminStatsSG.att_groups,
        "performance": AdminStatsSG.performance,
    }
    await manager.switch_to(state_map.get(return_state, AdminStatsSG.att_groups))


async def on_view_students(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminStatsSG.att_students)


async def _send_excel(callback: CallbackQuery, manager: DialogManager) -> None:
    from bot.services.excel_reports import generate_analytics_report
    api_client = manager.middleware_data["api_client"]
    days = _period(manager)
    gid = _group_id(manager)

    attendance = await api_client.get_attendance_stats(days=days, group_id=gid)
    performance = await api_client.get_performance_stats(days=days, group_id=gid)

    xlsx = generate_analytics_report(None, attendance, performance, days)
    from datetime import date
    filename = f"analytics_{date.today().isoformat()}.xlsx"
    file = BufferedInputFile(xlsx, filename=filename)
    await callback.message.answer_document(file, caption=f"📊 Аналітика за {days} днів")


async def on_excel_att(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _send_excel(callback, manager)

async def on_excel_perf(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _send_excel(callback, manager)


# ---- Dialog ----

dialog = Dialog(
    Window(
        Format(
            "📊 Статистика школи\n\n"
            "👥 Учні: {total_students} активних / {pending_students} очікують\n"
            "🏫 Груп: {total_groups}\n\n"
            "📅 Уроків сьогодні: {lessons_today}\n"
            "📅 Уроків цього тижня: {lessons_this_week}\n\n"
            "📚 ДЗ прострочених: {overdue_homework}\n"
            "📚 ДЗ на цей тиждень: {hw_due_this_week}\n\n"
            "📊 Відвідуваність (30 днів):\n{att_lines}"
        ),
        Row(
            Button(Const("📊 Відвідуваність"), id="go_att", on_click=on_go_att),
            Button(Const("📚 Успішність"),    id="go_perf", on_click=on_go_perf),
        ),
        Button(Const("← Меню"), id="stats_back_menu", on_click=on_back_to_menu),
        state=AdminStatsSG.overview,
        getter=get_overview,
    ),
    Window(
        Format(
            "📊 Відвідуваність ({days} днів) — {group_label}\n\n"
            "{att_lines}"
        ),
        Row(
            Button(Const("30д"), id="att_30", on_click=on_period_30_att),
            Button(Const("60д"), id="att_60", on_click=on_period_60_att),
            Button(Const("90д"), id="att_90", on_click=on_period_90_att),
        ),
        Row(
            Button(Const("🏫 Вибрати групу"), id="att_grp", on_click=on_pick_group_att),
            Button(Const("👤 По учнях"), id="att_stu", on_click=on_view_students, when="has_students"),
        ),
        Row(
            Button(Const("📥 Excel-звіт"), id="att_excel", on_click=on_excel_att),
            Button(Const("← Назад"), id="att_back", on_click=on_back_overview),
        ),
        state=AdminStatsSG.att_groups,
        getter=get_att_groups,
    ),
    Window(
        Format("👤 Відвідуваність по учнях ({days} днів)\n\n{student_lines}"),
        Button(
            Const("← До груп"), id="stu_back",
            on_click=lambda c, b, m: m.switch_to(AdminStatsSG.att_groups)
        ),
        state=AdminStatsSG.att_students,
        getter=get_att_students,
    ),
    Window(
        Format(
            "📚 Успішність ({days} днів) — {group_label}\n\n"
            "📝 ДЗ здано: {hw_completion}% ({hw_submitted}/{hw_assigned})\n\n"
            "🧪 Тести завершено: {quiz_completed}\n"
            "   Середній результат: {quiz_avg_pct}%\n\n"
            "🏆 Топ учні:\n{top3}"
        ),
        Row(
            Button(Const("30д"), id="perf_30", on_click=on_period_30_perf),
            Button(Const("60д"), id="perf_60", on_click=on_period_60_perf),
            Button(Const("90д"), id="perf_90", on_click=on_period_90_perf),
        ),
        Row(
            Button(Const("🏫 Вибрати групу"), id="perf_grp", on_click=on_pick_group_perf),
            Button(Const("📥 Excel-звіт"), id="perf_excel", on_click=on_excel_perf),
        ),
        Button(Const("← Назад"), id="perf_back", on_click=on_back_overview),
        state=AdminStatsSG.performance,
        getter=get_performance,
    ),
    Window(
        Const("🏫 Оберіть групу:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"), id="grp_sel",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_selected,
            ),
            id="grp_sg", width=1, height=7,
        ),
        state=AdminStatsSG.pick_group,
        getter=get_pick_group,
    ),
)
