from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button


class AgreementSG(StatesGroup):
    rules = State()
    contract = State()


dialog = Dialog(
    Window(Const("Rules placeholder"), Button(Const("OK"), id="ok"), state=AgreementSG.rules),
    Window(Const("Contract placeholder"), Button(Const("OK"), id="ok2"), state=AgreementSG.contract),
)
