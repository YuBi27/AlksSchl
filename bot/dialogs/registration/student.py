from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button


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


dialog = Dialog(
    Window(Const("Student reg placeholder"), Button(Const("OK"), id="ok"), state=StudentRegSG.invite_check),
)
