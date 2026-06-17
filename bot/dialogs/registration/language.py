from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button, Row


class LanguageSG(StatesGroup):
    select = State()


async def _on_lang(callback, button, manager):
    pass


dialog = Dialog(
    Window(
        Const("🇺🇦 Оберіть мову / Choose language 🇬🇧"),
        Row(
            Button(Const("🇺🇦 Українська"), id="uk", on_click=_on_lang),
            Button(Const("🇬🇧 English"), id="en", on_click=_on_lang),
        ),
        state=LanguageSG.select,
    )
)
