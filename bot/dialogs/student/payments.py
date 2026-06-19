from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format


class StudentPaymentSG(StatesGroup):
    main = State()
    history = State()


TYPE_LABELS = {"monthly": "Щомісячний", "one_time": "Разовий"}


async def get_payment_details(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    content = await api_client.get_content("payment_details")
    return {"payment_details": content.get("value", "—")}


async def get_payment_history(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_data = dialog_manager.middleware_data["user_data"]
    user_id = user_data.get("id")
    payments = await api_client.get_payments(user_id=user_id, limit=20)
    items = [
        (
            str(i),
            f"💳 {p['amount']} грн | {p['period_start']}–{p['period_end']} | {TYPE_LABELS.get(p['payment_type'], p['payment_type'])}",
        )
        for i, p in enumerate(payments)
    ]
    return {"items": items, "count": len(items)}


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.student.menu import StudentMenuSG
    await manager.start(StudentMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Format("💳 Оплата\n\n{payment_details}"),
        Button(Const("📋 Моя історія платежів"), id="sp_history", on_click=lambda c, b, m: m.switch_to(StudentPaymentSG.history)),
        Button(Const("← Меню"), id="sp_back_menu", on_click=on_back_to_menu),
        state=StudentPaymentSG.main,
        getter=get_payment_details,
    ),
    Window(
        Format("📋 Мої платежі ({count}):"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="sp_hist_sel",
                item_id_getter=lambda x: x[0],
                items="items",
                on_click=lambda c, w, m, i: None,
            ),
            id="sp_hist_scroll",
            width=1,
            height=8,
        ),
        Button(Const("← Назад"), id="sp_back_main", on_click=lambda c, b, m: m.switch_to(StudentPaymentSG.main)),
        state=StudentPaymentSG.history,
        getter=get_payment_history,
    ),
)
