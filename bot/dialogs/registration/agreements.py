from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from bot.config import settings


class AgreementSG(StatesGroup):
    rules = State()
    contract = State()


RULES_TEXT_UK = (
    "📋 <b>Основні правила:</b>\n\n"
    "• оплата абонемента щомісяця до 10 числа\n"
    "• повідомлення про відсутність на занятті за 4 години до початку\n"
    "• ввічливе та толерантне ставлення до колег по навчанню та репетиторів\n"
    "• виконання вказівок репетитора\n"
    "• згода на фото/відеозйомку та публікацію в мережі Інтернет"
)

CONTRACT_TEXT_UK = "📄 <b>Договір-оферта</b>\n\nБудь ласка, ознайомтесь з договором-офертою:"


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


async def on_show_contract(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    pdf = FSInputFile(settings.OFERT_PDF_PATH, filename="ofert.pdf")
    await callback.message.answer_document(pdf, caption="📄 Договір-оферта")


dialog = Dialog(
    Window(
        Const(RULES_TEXT_UK),
        Button(Const("✅ Погоджуюсь з правилами"), id="agree_rules", on_click=on_agree_rules),
        state=AgreementSG.rules,
    ),
    Window(
        Const(CONTRACT_TEXT_UK),
        Button(Const("📎 Переглянути договір-оферту"), id="show_contract", on_click=on_show_contract),
        Button(Const("✅ Погоджуюсь з умовами"), id="agree_contract", on_click=on_agree_contract),
        state=AgreementSG.contract,
    ),
)
