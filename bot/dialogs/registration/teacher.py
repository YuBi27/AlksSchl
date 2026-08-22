from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput


class TeacherRegSG(StatesGroup):
    enter_code = State()
    full_name = State()
    photo = State()
    bio = State()
    specialization = State()
    experience = State()
    confirm = State()


async def on_invite_code(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    api_client = manager.middleware_data["api_client"]
    user_data = manager.middleware_data["user_data"]

    result = await api_client.validate_invite_code(value.strip())
    if not result.get("valid"):
        await message.answer("❌ Невірний або вже використаний код. Спробуйте ще раз.")
        return

    await api_client.use_invite_code(value.strip(), user_data["id"])
    manager.dialog_data["invite_code"] = value.strip()
    manager.middleware_data["user_data"]["role"] = "teacher"
    await manager.switch_to(TeacherRegSG.full_name)


async def on_full_name(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    manager.dialog_data["full_name"] = value
    await manager.switch_to(TeacherRegSG.photo)


async def on_photo(message: Message, widget: MessageInput, manager: DialogManager) -> None:
    if message.photo:
        manager.dialog_data["photo_file_id"] = message.photo[-1].file_id
    await manager.switch_to(TeacherRegSG.bio)


async def on_skip_photo(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["photo_file_id"] = None
    await manager.switch_to(TeacherRegSG.bio)


async def on_bio(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    manager.dialog_data["bio"] = value
    await manager.switch_to(TeacherRegSG.specialization)


async def on_specialization(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    manager.dialog_data["specialization"] = value
    await manager.switch_to(TeacherRegSG.experience)


async def on_experience(message: Message, widget: TextInput, manager: DialogManager, value: str) -> None:
    try:
        years = int(value.strip())
    except ValueError:
        years = None
    manager.dialog_data["experience_years"] = years
    await manager.switch_to(TeacherRegSG.confirm)


async def get_confirm_summary(dialog_manager: DialogManager, **kwargs) -> dict:
    d = dialog_manager.dialog_data
    text = (
        f"📋 Перевірте вашу заявку:\n\n"
        f"👤 ПІБ: {d.get('full_name', '—')}\n"
        f"🎓 Спеціалізація: {d.get('specialization', '—')}\n"
        f"🏆 Досвід: {d.get('experience_years', '—')} р.\n"
        f"📝 Про себе: {d.get('bio', '—')}\n"
        f"📷 Фото: {'✅' if d.get('photo_file_id') else 'не завантажено'}"
    )
    return {"confirm_text": text}


async def on_send_to_admin(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    user_data = manager.middleware_data["user_data"]
    d = manager.dialog_data

    await api_client.create_teacher_profile(
        user_data["id"],
        {
            "full_name": d.get("full_name", ""),
            "photo_file_id": d.get("photo_file_id"),
            "bio": d.get("bio"),
            "specialization": d.get("specialization"),
            "experience_years": d.get("experience_years"),
        },
    )

    await api_client.update_status(user_data["id"], "pending")

    bot = manager.middleware_data.get("bot")
    if bot:
        from bot.config import settings
        notification = (
            f"👩‍🏫 Нова заявка викладача на реєстрацію!\n\n"
            f"👤 ПІБ: {d.get('full_name', '—')}\n"
            f"🎓 Спеціалізація: {d.get('specialization', '—')}"
        )
        for admin_id in settings.admin_id_list:
            try:
                await bot.send_message(admin_id, notification)
            except Exception:
                pass

    await callback.message.answer("✅ Заявку надіслано адміністратору. Очікуйте підтвердження.")
    await manager.done()


dialog = Dialog(
    Window(
        Const("🔑 Введіть ваш інвайт-код:"),
        TextInput(id="invite_code_input", on_success=on_invite_code),
        state=TeacherRegSG.enter_code,
    ),
    Window(
        Const("👤 Введіть ваше повне ім'я:"),
        TextInput(id="teacher_name_input", on_success=on_full_name),
        state=TeacherRegSG.full_name,
    ),
    Window(
        Const("📷 Надішліть ваше фото (або натисніть «Пропустити»):"),
        MessageInput(on_photo),
        Button(Const("⏭ Пропустити"), id="skip_photo", on_click=on_skip_photo),
        state=TeacherRegSG.photo,
    ),
    Window(
        Const("📝 Розкажіть про себе:"),
        TextInput(id="bio_input", on_success=on_bio),
        state=TeacherRegSG.bio,
    ),
    Window(
        Const("🎓 Ваша спеціалізація:"),
        TextInput(id="spec_input", on_success=on_specialization),
        state=TeacherRegSG.specialization,
    ),
    Window(
        Const("🏆 Скільки років досвіду? (введіть число):"),
        TextInput(id="exp_input", on_success=on_experience),
        state=TeacherRegSG.experience,
    ),
    Window(
        Format("{confirm_text}"),
        Button(Const("📤 Надіслати адміну на підтвердження"), id="teacher_send_to_admin", on_click=on_send_to_admin),
        state=TeacherRegSG.confirm,
        getter=get_confirm_summary,
    ),
)
