from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import AuthStartRequest, UserOut
from api.crud.users import get_user_by_telegram_id, create_user
from api.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/start", response_model=UserOut)
async def auth_start(
    body: AuthStartRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    user = await get_user_by_telegram_id(db, body.telegram_id)
    if user:
        return user
    if body.telegram_id in settings.admin_id_list:
        role, status = "admin", "active"
    else:
        # "new" — ще проходить реєстрацію; "pending" ставиться після подання заявки.
        # Якщо створити одразу "pending", blocked-роутер перехоплює текстові
        # повідомлення і реєстрація обривається на першому текстовому кроці (ПІБ).
        role, status = "student", "new"
    return await create_user(db, telegram_id=body.telegram_id, username=body.username, role=role, status=status)
