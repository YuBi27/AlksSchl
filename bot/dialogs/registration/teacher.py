from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button


class TeacherRegSG(StatesGroup):
    enter_code = State()
    full_name = State()
    photo = State()
    bio = State()
    specialization = State()
    experience = State()


dialog = Dialog(
    Window(Const("Teacher reg placeholder"), Button(Const("OK"), id="ok"), state=TeacherRegSG.enter_code),
)
