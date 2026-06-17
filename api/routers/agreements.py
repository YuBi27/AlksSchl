from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import AgreementCreate, AgreementOut
from api.crud.agreements import create_agreement

router = APIRouter(prefix="/agreements", tags=["agreements"])


@router.post("", response_model=AgreementOut)
async def record_agreement(
    body: AgreementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await create_agreement(db, body.user_id, body.telegram_id, body.type)
