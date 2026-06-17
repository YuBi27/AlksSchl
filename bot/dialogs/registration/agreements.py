from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const


class AgreementSG(StatesGroup):
    rules = State()
    contract = State()


RULES_TEXT_UK = (
    "📋 <b>Правила школи</b>\n\n"
    "Перед початком навчання просимо ознайомитись з правилами:\n\n"
    "• Дотримуйтесь розкладу занять\n"
    "• Виконуйте домашні завдання вчасно\n"
    "• Повідомляйте заздалегідь про відсутність\n"
    "• Поважайте викладача та однокласників"
)

CONTRACT_TEXT_UK = (
    "📄 <b>Договір-оферта</b>\n\n"
    "Умови надання освітніх послуг:\n\n"
    "• Оплата щомісяця до 10 числа\n"
    "• Перенесення заняття за 24 год попередження\n"
    "• Повернення коштів: протягом 3 днів після першого заняття"
)


async def on_agree_rules(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    user_data = manager.middleware_data["user_data"]
    await api_client.record_agreement(user_data["id"], user_data["telegram_id"], "rules")
    await manager.switch_to(AgreementSG.contract)


async def on_agree_contract(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    user_data = manager.middleware_data["user_data"]
    await api_client.record_agreement(user_data["id"], user_data["telegram_id"], "contract")

    from bot.dialogs.registration.student import StudentRegSG
    await manager.start(StudentRegSG.invite_check, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const(RULES_TEXT_UK),
        Button(Const("✅ Погоджуюсь з правилами"), id="agree_rules", on_click=on_agree_rules),
        state=AgreementSG.rules,
    ),
    Window(
        Const(CONTRACT_TEXT_UK),
        Button(Const("✅ Погоджуюсь з умовами"), id="agree_contract", on_click=on_agree_contract),
        state=AgreementSG.contract,
    ),
)
