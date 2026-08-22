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
        username = a.get("username")
        display = f"@{username}" if username else f"ID {a['telegram_id']}"
        role = a.get("role", "student")
        role_emoji = "👩‍🏫" if role == "teacher" else "🎓"
        items.append((str(a["id"]), f"{role_emoji} {display}"))
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
    user = await api_client.get_user(user_id)
    username = user.get("username")
    tg_display = f"@{username}" if username else f"ID {user.get('telegram_id', '—')}"
    role = user.get("role", "student")

    if role == "teacher":
        try:
            profile = await api_client.get_teacher_profile(user_id)
        except Exception:
            profile = {}
        detail = (
            f"👩‍🏫 Заявка ВИКЛАДАЧА\n\n"
            f"👤 ПІБ: {profile.get('full_name') or '—'}\n"
            f"🎓 Спеціалізація: {profile.get('specialization') or '—'}\n"
            f"🏆 Досвід: {profile.get('experience_years') or '—'} р.\n"
            f"📝 Про себе: {profile.get('bio') or '—'}\n"
            f"✈️ Telegram: {tg_display}"
        )
        return {
            "detail_text": detail,
            "user_id": user_id,
        }
    else:
        profile = await api_client.get_user_student_profile(user_id)
        fmt_map = {"online": "💻 Онлайн", "offline": "🏫 Офлайн", "hybrid": "🔄 Гібрид"}
        study_format = fmt_map.get(profile.get("study_format", ""), profile.get("study_format") or "—")
        detail = (
            f"📩 Заявка УЧНЯ\n\n"
            f"👤 ПІБ: {profile.get('full_name') or '—'}\n"
            f"🎂 Дата народження: {profile.get('birth_date') or '—'}\n"
            f"📱 Телефон: {profile.get('phone') or '—'}\n"
            f"👨‍👩‍👧 Батько/мати: {profile.get('parent_name') or '—'}\n"
            f"📱 Тел. батьків: {profile.get('parent_phone') or '—'}\n"
            f"🎓 Формат: {study_format}\n"
            f"📅 Початок: {profile.get('study_start_month') or '—'}\n"
            f"💬 Додатково: {profile.get('extra_info') or '—'}\n"
            f"✈️ Telegram: {tg_display}"
        )
        return {
            "detail_text": detail,
            "user_id": user_id,
        }


async def on_approve(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    admin_data = manager.middleware_data["user_data"]
    user_id = manager.dialog_data["selected_user_id"]

    await api_client.update_status(user_id, "active")
    await api_client.log_admin_action(admin_data["id"], "approve_user", user_id)

    user_detail = await api_client.get_user(user_id)
    role = user_detail.get("role", "student")
    bot = manager.middleware_data.get("bot")
    if bot:
        msg = (
            "🎉 Вашу заявку підтверджено! Ласкаво просимо до школи."
            if role != "teacher"
            else "🎉 Вашу заявку викладача підтверджено! Тепер ви можете користуватися панеллю викладача."
        )
        try:
            await bot.send_message(user_detail["telegram_id"], msg)
        except Exception:
            pass

    role_label = "викладача" if role == "teacher" else "учня"
    await callback.answer(f"✅ Заявку {role_label} підтверджено")
    await callback.message.answer(f"✅ Заявку {role_label} підтверджено та активовано")
    await manager.switch_to(AdminAppSG.list_view)


async def on_reject(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    admin_data = manager.middleware_data["user_data"]
    user_id = manager.dialog_data["selected_user_id"]

    await api_client.update_status(user_id, "inactive")
    await api_client.log_admin_action(admin_data["id"], "reject_user", user_id)

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
    await callback.message.answer("❌ Заявку відхилено")
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
        Format("{detail_text}"),
        Button(Const("✅ Підтвердити"), id="approve", on_click=on_approve),
        Button(Const("❌ Відхилити"), id="reject", on_click=on_reject),
        Button(Const("← Назад"), id="back_list", on_click=on_back_to_list),
        state=AdminAppSG.review,
        getter=get_application_detail,
    ),
)
