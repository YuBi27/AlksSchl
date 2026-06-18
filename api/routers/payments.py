from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.crud.payments import save_payment, list_payments, list_debtors
from api.schemas.schemas import PaymentCreate, PaymentRead

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentRead, status_code=201)
async def create_payment(
    data: PaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await save_payment(
        db,
        user_id=data.user_id,
        amount=data.amount,
        period_start=data.period_start,
        period_end=data.period_end,
        payment_type=data.payment_type,
        confirmed_by=data.confirmed_by,
        comment=data.comment,
    )


@router.get("/debtors")
async def get_debtors(db: Annotated[AsyncSession, Depends(get_db)]):
    return await list_debtors(db)


@router.get("", response_model=list[PaymentRead])
async def get_payments_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Optional[int] = Query(None),
    limit: int = Query(20, le=100),
):
    return await list_payments(db, user_id=user_id, limit=limit)
