from typing import Any
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format


class AdminAppSG(StatesGroup):
    list_view = State()
    review = State()


async def get_pending_applications(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    apps = await api_client.get_pending_applications()
    items = []
    for a in apps:
        profile = a.get("student_profile") or {}
        name = profile.get("full_name", f"Учень #{a['id']}")
        items.append((str(a["id"]), name))
    return {"applications": items, "count": len(apps)}


async def on_select_application(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["selected_user_id"] = int(item_id)
    await manager.switch_to(AdminAppSG.review)


async def get_application_detail(dialog_manager: DialogManager, **kwargs) -> dict:
    api_client = dialog_manager.middleware_data["api_client"]
    user_id = dialog_manager.dialog_data.get("selected_user_id", 0)
    apps = await api_client.get_pending_applications()
    user = next((a for a in apps if a["id"] == user_id), {})
    profile = user.get("student_profile") or {}
    return {
        "full_name": profile.get("full_name", "—"),
        "phone": profile.get("phone", "—"),
        "study_format": profile.get("study_format", "—"),
        "start_month": profile.get("study_start_month", "—"),
        "user_id": user_id,
        "telegram_id": user.get("telegram_id", 0),
    }


async def on_approve(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    admin_data = manager.middleware_data["user_data"]
    user_id = manager.dialog_data["selected_user_id"]

    await api_client.update_status(user_id, "active")
    await api_client.log_admin_action(admin_data["id"], "approve_student", user_id)

    user_detail = await api_client.get_user(user_id)
    bot = manager.middleware_data.get("bot")
    if bot:
        try:
            await bot.send_message(
                user_detail["telegram_id"],
                "🎉 Вашу заявку підтверджено! Ласкаво просимо до школи.",
            )
        except Exception:
            pass

    await callback.answer("✅ Заявку підтверджено")
    await manager.switch_to(AdminAppSG.list_view)


async def on_reject(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    admin_data = manager.middleware_data["user_data"]
    user_id = manager.dialog_data["selected_user_id"]

    await api_client.update_status(user_id, "inactive")
    await api_client.log_admin_action(admin_data["id"], "reject_student", user_id)

    user_detail = await api_client.get_user(user_id)
    bot = manager.middleware_data.get("bot")
    if bot:
        try:
            await bot.send_message(
                user_detail["telegram_id"],
                "❌ На жаль, вашу заявку відхилено. Зв'яжіться з адміністратором.",
            )
        except Exception:
            pass

    await callback.answer("❌ Заявку відхилено")
    await manager.switch_to(AdminAppSG.list_view)


async def on_back_to_list(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminAppSG.list_view)


dialog = Dialog(
    Window(
        Format("📋 Заявки на реєстрацію: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="apps_select",
                item_id_getter=lambda x: x[0],
                items="applications",
                on_click=on_select_application,
            ),
            id="apps_scroll",
            width=1,
            height=5,
        ),
        state=AdminAppSG.list_view,
        getter=get_pending_applications,
    ),
    Window(
        Format(
            "📩 Заявка #{user_id}\n\n"
            "👤 ПІБ: {full_name}\n"
            "📱 Телефон: {phone}\n"
            "🎓 Формат: {study_format}\n"
            "📅 Початок: {start_month}"
        ),
        Button(Const("✅ Підтвердити"), id="approve", on_click=on_approve),
        Button(Const("❌ Відхилити"), id="reject", on_click=on_reject),
        Button(Const("← Назад"), id="back_list", on_click=on_back_to_list),
        state=AdminAppSG.review,
        getter=get_application_detail,
    ),
)
