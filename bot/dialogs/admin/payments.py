from datetime import date
from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput


class AdminPaymentSG(StatesGroup):
    list_view = State()
    select_student = State()
    enter_amount = State()
    select_type = State()
    enter_period = State()
    enter_comment = State()
    confirm = State()
    debtors = State()
    student_history = State()


TYPE_LABELS = {"monthly": "Щомісячний", "one_time": "Разовий"}


def _trunc(text: str, max_len: int = 55) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


# --- list_view handlers ---

async def on_add_payment(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["intent"] = "add"
    await manager.switch_to(AdminPaymentSG.select_student)


async def on_view_history(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["intent"] = "view"
    await manager.switch_to(AdminPaymentSG.select_student)


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


# --- select_student ---

async def get_students_for_payment(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    students = await api_client.get_students(status="active", limit=200)
    items = [
        (str(s["id"]), _trunc(s.get("full_name") or f"Учень #{s['id']}"))
        for s in students
    ]
    return {"students": items, "count": len(items)}


async def on_student_selected(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["selected_student_id"] = int(item_id)
    intent = manager.dialog_data.get("intent", "add")
    if intent == "view":
        await manager.switch_to(AdminPaymentSG.student_history)
    else:
        await manager.switch_to(AdminPaymentSG.enter_amount)


# --- enter_amount ---

async def on_amount_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    value = value.strip().replace(",", ".")
    try:
        float(value)
    except ValueError:
        await message.answer("❌ Невірна сума. Введіть число, наприклад: 1500 або 750.50")
        return
    manager.dialog_data["amount"] = value
    await manager.switch_to(AdminPaymentSG.select_type)


# --- select_type ---

async def on_type_monthly(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    import calendar
    manager.dialog_data["payment_type"] = "monthly"
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    hint = f"{today.replace(day=1).isoformat()} {today.replace(day=last_day).isoformat()}"
    manager.dialog_data["period_hint"] = hint
    await manager.switch_to(AdminPaymentSG.enter_period)


async def on_type_one_time(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["payment_type"] = "one_time"
    today = date.today()
    manager.dialog_data["period_hint"] = f"{today.isoformat()} {today.isoformat()}"
    await manager.switch_to(AdminPaymentSG.enter_period)


# --- enter_period ---

async def get_period_prompt(dialog_manager: DialogManager, **kwargs) -> dict:
    hint = dialog_manager.dialog_data.get("period_hint", "")
    return {"period_hint": hint}


async def on_period_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    parts = value.strip().split()
    if len(parts) != 2:
        await message.answer("❌ Введіть два дати через пробіл: 2026-06-01 2026-06-30")
        return
    try:
        date.fromisoformat(parts[0])
        date.fromisoformat(parts[1])
    except ValueError:
        await message.answer("❌ Невірний формат дати. Приклад: 2026-06-01 2026-06-30")
        return
    manager.dialog_data["period_start"] = parts[0]
    manager.dialog_data["period_end"] = parts[1]
    await manager.switch_to(AdminPaymentSG.enter_comment)


# --- enter_comment ---

async def on_comment_entered(
    message: Message, widget: TextInput, manager: DialogManager, value: str
) -> None:
    manager.dialog_data["comment"] = value.strip()
    await manager.switch_to(AdminPaymentSG.confirm)


async def on_skip_comment(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["comment"] = None
    await manager.switch_to(AdminPaymentSG.confirm)


# --- confirm ---

async def get_confirm(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    dd = dialog_manager.dialog_data
    student_id = dd.get("selected_student_id", 0)
    student = await api_client.get_student(student_id)
    return {
        "student_name": student.get("full_name") or f"Учень #{student_id}",
        "amount": dd.get("amount", ""),
        "period": f"{dd.get('period_start', '')} – {dd.get('period_end', '')}",
        "payment_type_label": TYPE_LABELS.get(dd.get("payment_type", ""), "—"),
        "comment": dd.get("comment") or "—",
    }


async def on_confirm(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    user_data = manager.middleware_data["user_data"]
    dd = manager.dialog_data
    await api_client.save_payment(
        user_id=dd["selected_student_id"],
        amount=dd["amount"],
        period_start=dd["period_start"],
        period_end=dd["period_end"],
        payment_type=dd["payment_type"],
        confirmed_by=user_data.get("id"),
        comment=dd.get("comment"),
    )
    await callback.message.answer("✅ Платіж записано")
    await manager.switch_to(AdminPaymentSG.list_view)


# --- debtors ---

async def get_debtors_list(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    debtors = await api_client.get_debtors()
    items = [
        (str(i), _trunc(f"👤 {d.get('full_name') or 'Без імені'} | {d.get('phone') or '—'}"))
        for i, d in enumerate(debtors)
    ]
    return {"items": items, "count": len(items)}


# --- student_history ---

async def get_student_history(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    student_id = dialog_manager.dialog_data.get("selected_student_id", 0)
    payments = await api_client.get_payments(user_id=student_id, limit=20)
    student = await api_client.get_student(student_id)
    items = [
        (
            str(i),
            _trunc(f"💳 {p['amount']} грн | {p['period_start']}–{p['period_end']} | {TYPE_LABELS.get(p['payment_type'], p['payment_type'])}"),
        )
        for i, p in enumerate(payments)
    ]
    return {
        "student_name": student.get("full_name") or f"Учень #{student_id}",
        "items": items,
        "count": len(items),
    }


dialog = Dialog(
    Window(
        Const("💳 Оплати\n\nОберіть дію:"),
        Button(Const("➕ Додати платіж"), id="pay_add", on_click=on_add_payment),
        Button(Const("⚠️ Боржники"), id="pay_debtors", on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.debtors)),
        Button(Const("📋 Учень → Платежі"), id="pay_view", on_click=on_view_history),
        Button(Const("← Меню"), id="pay_back_menu", on_click=on_back_to_menu),
        state=AdminPaymentSG.list_view,
    ),
    Window(
        Format("👤 Оберіть учня ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="pay_stud_sel",
                item_id_getter=lambda x: x[0],
                items="students",
                on_click=on_student_selected,
            ),
            id="pay_stud_scroll",
            width=1,
            height=10,
        ),
        Button(Const("← Назад"), id="pay_back_list", on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.list_view)),
        state=AdminPaymentSG.select_student,
        getter=get_students_for_payment,
    ),
    Window(
        Const("💰 Введіть суму оплати (наприклад: 1500 або 750.50):"),
        TextInput(id="pay_amount_input", on_success=on_amount_entered),
        Button(Const("← Назад"), id="pay_back_stud", on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.select_student)),
        state=AdminPaymentSG.enter_amount,
    ),
    Window(
        Const("📅 Оберіть тип платежу:"),
        Row(
            Button(Const("📅 Щомісячний"), id="pay_monthly", on_click=on_type_monthly),
            Button(Const("💡 Разовий"), id="pay_one_time", on_click=on_type_one_time),
        ),
        Button(Const("← Назад"), id="pay_back_amount", on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.enter_amount)),
        state=AdminPaymentSG.select_type,
    ),
    Window(
        Format("📅 Введіть період оплати (старт кінець):\nПриклад: {period_hint}"),
        TextInput(id="pay_period_input", on_success=on_period_entered),
        Button(Const("← Назад"), id="pay_back_type", on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.select_type)),
        state=AdminPaymentSG.enter_period,
        getter=get_period_prompt,
    ),
    Window(
        Const("💬 Введіть коментар (необов'язково):"),
        TextInput(id="pay_comment_input", on_success=on_comment_entered),
        Button(Const("⏭ Пропустити"), id="pay_skip_comment", on_click=on_skip_comment),
        Button(Const("← Назад"), id="pay_back_period", on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.enter_period)),
        state=AdminPaymentSG.enter_comment,
    ),
    Window(
        Format(
            "✅ Підтвердіть платіж:\n\n"
            "👤 Учень: {student_name}\n"
            "💰 Сума: {amount} грн\n"
            "📅 Період: {period}\n"
            "🔖 Тип: {payment_type_label}\n"
            "💬 Коментар: {comment}"
        ),
        Row(
            Button(Const("✅ Підтвердити"), id="pay_confirm", on_click=on_confirm),
            Button(Const("← Назад"), id="pay_back_comment", on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.enter_comment)),
        ),
        state=AdminPaymentSG.confirm,
        getter=get_confirm,
    ),
    Window(
        Format("⚠️ Боржники ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="pay_debt_sel",
                item_id_getter=lambda x: x[0],
                items="items",
                on_click=lambda c, w, m, i: None,
            ),
            id="pay_debt_scroll",
            width=1,
            height=10,
        ),
        Button(Const("← Назад"), id="pay_back_debt", on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.list_view)),
        state=AdminPaymentSG.debtors,
        getter=get_debtors_list,
    ),
    Window(
        Format("📋 Платежі учня {student_name} ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="pay_hist_sel",
                item_id_getter=lambda x: x[0],
                items="items",
                on_click=lambda c, w, m, i: None,
            ),
            id="pay_hist_scroll",
            width=1,
            height=8,
        ),
        Button(Const("← Назад"), id="pay_back_hist", on_click=lambda c, b, m: m.switch_to(AdminPaymentSG.select_student)),
        state=AdminPaymentSG.student_history,
        getter=get_student_history,
    ),
)
