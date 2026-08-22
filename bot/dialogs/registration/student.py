from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput


class StudentRegSG(StatesGroup):
    invite_check = State()
    full_name = State()
    birth_date = State()
    phone = State()
    parent_name = State()
    parent_phone = State()
    start_month = State()
    study_format = State()
    extra_info = State()
    confirm = State()


async def on_has_invite(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.registration.teacher import TeacherRegSG
    await manager.start(TeacherRegSG.enter_code, mode=StartMode.RESET_STACK)


async def on_no_invite(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(StudentRegSG.full_name)


async def on_full_name(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    manager.dialog_data["full_name"] = value
    await manager.switch_to(StudentRegSG.birth_date)


async def on_birth_date(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    from datetime import datetime as _dt
    try:
        _dt.strptime(value, "%d.%m.%Y")
    except ValueError:
        await message.answer("❌ Невірний формат дати. Введіть у форматі ДД.ММ.РРРР (наприклад, 15.03.2005):")
        return
    manager.dialog_data["birth_date_str"] = value
    await manager.switch_to(StudentRegSG.phone)


async def on_phone(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    manager.dialog_data["phone"] = value
    await manager.switch_to(StudentRegSG.parent_name)


async def on_parent_name(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    manager.dialog_data["parent_name"] = value
    await manager.switch_to(StudentRegSG.parent_phone)


async def on_parent_phone(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    manager.dialog_data["parent_phone"] = value
    await manager.switch_to(StudentRegSG.start_month)


async def on_start_month(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    manager.dialog_data["study_start_month"] = value
    await manager.switch_to(StudentRegSG.study_format)


async def on_format_selected(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["study_format"] = button.widget_id
    await manager.switch_to(StudentRegSG.extra_info)


async def on_extra_info(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    manager.dialog_data["extra_info"] = value
    await manager.switch_to(StudentRegSG.confirm)


async def on_skip_extra(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["extra_info"] = None
    await manager.switch_to(StudentRegSG.confirm)


async def get_confirm_summary(dialog_manager: DialogManager, **kwargs) -> dict:
    d = dialog_manager.dialog_data
    fmt = d.get("study_format", "—")
    fmt_ua = {"online": "Онлайн", "offline": "Офлайн", "hybrid": "Гібрид"}.get(fmt, fmt)
    text = (
        f"📋 Перевірте вашу заявку:\n\n"
        f"👤 ПІБ: {d.get('full_name', '—')}\n"
        f"🎂 Дата народження: {d.get('birth_date_str', '—')}\n"
        f"📱 Телефон: {d.get('phone', '—')}\n"
        f"👨‍👩‍👧 ПІБ батьків: {d.get('parent_name', '—')}\n"
        f"📱 Тел. батьків: {d.get('parent_phone', '—')}\n"
        f"📅 Початок навчання: {d.get('study_start_month', '—')}\n"
        f"🎓 Формат: {fmt_ua}\n"
        f"💬 Додатково: {d.get('extra_info') or '—'}"
    )
    return {"confirm_text": text}


async def on_send_to_admin(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _submit_registration(manager)


async def _submit_registration(manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    user_data = manager.middleware_data["user_data"]
    d = manager.dialog_data

    birth_date = None
    if d.get("birth_date_str"):
        try:
            parts = d["birth_date_str"].split(".")
            birth_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
        except (IndexError, ValueError):
            birth_date = None

    start_month = None
    if d.get("study_start_month"):
        try:
            parts = d["study_start_month"].split(".")
            start_month = f"{parts[1]}-{parts[0]}"
        except (IndexError, ValueError):
            start_month = None

    await api_client.create_student_profile(
        user_data["id"],
        {
            "full_name": d.get("full_name", ""),
            "birth_date": birth_date,
            "phone": d.get("phone"),
            "parent_name": d.get("parent_name"),
            "parent_phone": d.get("parent_phone"),
            "study_start_month": start_month,
            "study_format": d.get("study_format"),
            "extra_info": d.get("extra_info"),
            "notion_link": f"https://notion.so/PLACEHOLDER-{user_data['id']}",
        },
    )

    await api_client.update_status(user_data["id"], "pending")

    await api_client.log_admin_action(
        admin_id=0,
        action="new_student_application",
        target_user_id=user_data["id"],
        details={"full_name": d.get("full_name"), "phone": d.get("phone")},
    )

    bot = manager.middleware_data.get("bot")
    if bot:
        from bot.config import settings
        notification = (
            f"📩 Нова заявка учня на реєстрацію!\n\n"
            f"👤 ПІБ: {d.get('full_name', '—')}\n"
            f"📱 Телефон: {d.get('phone', '—')}\n"
            f"🎓 Формат: {d.get('study_format', '—')}"
        )
        for admin_id in settings.admin_id_list:
            try:
                await bot.send_message(admin_id, notification)
            except Exception:
                pass

    await manager.done(result={"submitted": True})


dialog = Dialog(
    Window(
        Const("Маєте запрошення від викладача? / Do you have an invite code?"),
        Row(
            Button(Const("✅ Так / Yes"), id="yes_invite", on_click=on_has_invite),
            Button(Const("❌ Ні / No"), id="no_invite", on_click=on_no_invite),
        ),
        state=StudentRegSG.invite_check,
    ),
    Window(
        Const("👤 Введіть ваше повне ім'я (ПІБ):"),
        TextInput(id="full_name_input", on_success=on_full_name),
        state=StudentRegSG.full_name,
    ),
    Window(
        Const("🎂 Введіть дату народження (ДД.ММ.РРРР):"),
        TextInput(id="birth_date_input", on_success=on_birth_date),
        state=StudentRegSG.birth_date,
    ),
    Window(
        Const("📱 Введіть ваш номер телефону:"),
        TextInput(id="phone_input", on_success=on_phone),
        state=StudentRegSG.phone,
    ),
    Window(
        Const("👨‍👩‍👧 Введіть ПІБ одного з батьків:"),
        TextInput(id="parent_name_input", on_success=on_parent_name),
        state=StudentRegSG.parent_name,
    ),
    Window(
        Const("📱 Введіть номер телефону батьків:"),
        TextInput(id="parent_phone_input", on_success=on_parent_phone),
        state=StudentRegSG.parent_phone,
    ),
    Window(
        Const("📅 Вкажіть місяць початку навчання (ММ.РРРР):"),
        TextInput(id="start_month_input", on_success=on_start_month),
        state=StudentRegSG.start_month,
    ),
    Window(
        Const("🎓 Оберіть формат навчання:"),
        Row(
            Button(Const("💻 Онлайн"), id="online", on_click=on_format_selected),
            Button(Const("🏫 Офлайн"), id="offline", on_click=on_format_selected),
            Button(Const("🔄 Гібрид"), id="hybrid", on_click=on_format_selected),
        ),
        state=StudentRegSG.study_format,
    ),
    Window(
        Const("💬 Додаткова інформація (необов'язково):"),
        TextInput(id="extra_info_input", on_success=on_extra_info),
        Button(Const("⏭ Пропустити"), id="skip_extra", on_click=on_skip_extra),
        state=StudentRegSG.extra_info,
    ),
    Window(
        Format("{confirm_text}"),
        Button(Const("📤 Надіслати адміну на підтвердження"), id="send_to_admin", on_click=on_send_to_admin),
        state=StudentRegSG.confirm,
        getter=get_confirm_summary,
    ),
)
