from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const


class LanguageSG(StatesGroup):
    select = State()


async def on_language_selected(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    language = button.widget_id  # "uk" or "en"
    api_client = manager.middleware_data["api_client"]
    user_data = manager.middleware_data["user_data"]
    await api_client.update_language(user_data["telegram_id"], language)
    manager.middleware_data["user_data"]["language"] = language

    from bot.dialogs.registration.agreements import AgreementSG
    await manager.start(AgreementSG.rules, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const("🇺🇦 Оберіть мову / Choose language 🇬🇧"),
        Row(
            Button(Const("🇺🇦 Українська"), id="uk", on_click=on_language_selected),
            Button(Const("🇬🇧 English"), id="en", on_click=on_language_selected),
        ),
        state=LanguageSG.select,
    )
)
