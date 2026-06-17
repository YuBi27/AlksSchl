import io
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.services.api_client import APIClient

router = Router()

_pending_imports: dict[int, list[dict]] = {}


def _parse_xlsx(data: bytes) -> list[dict]:
    import openpyxl
    wb = openpyxl.load_workbook(filename=io.BytesIO(data), read_only=True)
    ws = wb.active
    rows = []
    headers = None
    HEADER_MAP = {
        "піб": "full_name",
        "пiб": "full_name",
        "повне імя": "full_name",
        "full name": "full_name",
        "телефон": "phone",
        "phone": "phone",
        "рівень": "level",
        "level": "level",
        "група": "group_name",
        "group": "group_name",
    }
    for row in ws.iter_rows(values_only=True):
        if headers is None:
            headers = [HEADER_MAP.get((str(c or "")).strip().lower(), (str(c or "")).strip().lower()) for c in row]
            continue
        if all(c is None for c in row):
            continue
        entry = {}
        for key, val in zip(headers, row):
            entry[key] = str(val).strip() if val is not None else ""
        if entry.get("full_name") and entry.get("phone"):
            rows.append(entry)
    wb.close()
    return rows


@router.message(F.document)
async def handle_excel_document(
    message: Message, user_data: dict, api_client: APIClient, bot: Bot
) -> None:
    if user_data.get("role") != "admin":
        return

    doc = message.document
    if not doc.file_name or not doc.file_name.endswith(".xlsx"):
        await message.answer("❌ Підтримуються тільки файли .xlsx")
        return

    file_bytes = io.BytesIO()
    await bot.download(doc.file_id, destination=file_bytes)
    file_bytes.seek(0)

    try:
        rows = _parse_xlsx(file_bytes.read())
    except Exception as e:
        await message.answer(f"❌ Помилка читання файлу: {e}")
        return

    if not rows:
        await message.answer("❌ У файлі не знайдено рядків із ПІБ та телефоном.")
        return

    _pending_imports[message.from_user.id] = rows

    preview_lines = [f"• {r.get('full_name', '—')} | {r.get('phone', '—')}" for r in rows[:5]]
    preview = "\n".join(preview_lines)
    extra = f"\n...та ще {len(rows) - 5}" if len(rows) > 5 else ""
    text = f"📊 Знайдено <b>{len(rows)}</b> записів.\n\nПерших 5:\n{preview}{extra}"

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Імпортувати", callback_data="excel_import:confirm"),
        InlineKeyboardButton(text="❌ Скасувати", callback_data="excel_import:cancel"),
    ]])
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "excel_import:confirm")
async def on_confirm_import(
    callback: CallbackQuery, user_data: dict, api_client: APIClient
) -> None:
    if user_data.get("role") != "admin":
        return
    rows = _pending_imports.pop(callback.from_user.id, [])
    if not rows:
        await callback.answer("Немає даних для імпорту.", show_alert=True)
        return
    result = await api_client.import_students(rows)
    text = (
        f"✅ Імпорт завершено!\n\n"
        f"Додано: {result['created']}\n"
        f"Пропущено (дублікати): {result['skipped']}"
    )
    if result.get("errors"):
        text += f"\n⚠️ Попередження: {len(result['errors'])}"
    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer()


@router.callback_query(F.data == "excel_import:cancel")
async def on_cancel_import(callback: CallbackQuery) -> None:
    _pending_imports.pop(callback.from_user.id, None)
    await callback.message.edit_text("❌ Імпорт скасовано.", reply_markup=None)
    await callback.answer()
