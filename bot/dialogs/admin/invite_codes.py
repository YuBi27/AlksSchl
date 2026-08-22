from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format


class InviteCodeMgmtSG(StatesGroup):
    main = State()
    code_generated = State()


async def get_invite_main(dialog_manager: DialogManager, **kwargs) -> dict:
    return {}


async def on_generate(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    api_client = manager.middleware_data["api_client"]
    user_data = manager.middleware_data["user_data"]
    invite = await api_client.generate_invite_code(created_by=user_data["id"], role="teacher")
    manager.dialog_data["generated_code"] = invite["code"]
    await manager.switch_to(InviteCodeMgmtSG.code_generated)


async def get_generated_code(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"code": dialog_manager.dialog_data.get("generated_code", "—")}


async def on_back(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    from bot.dialogs.admin.menu import AdminMenuSG
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


dialog = Dialog(
    Window(
        Const(
            "🔑 Генерація інвайт-коду для викладача\n\n"
            "Натисніть кнопку нижче, щоб згенерувати унікальний код.\n"
            "Передайте його викладачу — він введе його при реєстрації."
        ),
        Button(Const("➕ Згенерувати код"), id="gen_code", on_click=on_generate),
        Button(Const("← Назад"), id="back", on_click=on_back),
        state=InviteCodeMgmtSG.main,
        getter=get_invite_main,
    ),
    Window(
        Format(
            "✅ Інвайт-код створено!\n\n"
            "🔑 Код: <code>{code}</code>\n\n"
            "Передайте цей код викладачу. Код одноразовий."
        ),
        Button(Const("➕ Ще один код"), id="gen_another", on_click=on_generate),
        Button(Const("← В меню"), id="back2", on_click=on_back),
        state=InviteCodeMgmtSG.code_generated,
        getter=get_generated_code,
    ),
)
