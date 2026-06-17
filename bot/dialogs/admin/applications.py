from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button


class AdminAppSG(StatesGroup):
    list_view = State()
    review = State()


dialog = Dialog(
    Window(Const("Admin apps placeholder"), Button(Const("OK"), id="ok"), state=AdminAppSG.list_view),
)
