from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.crud.payments import save_payment, list_payments, list_debtors, update_payment_status, update_payment_fields, delete_payment
from api.schemas.schemas import PaymentCreate, PaymentRead, PaymentStatusUpdate, PaymentUpdate

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
        months_paid=data.months_paid,
        confirmed_by=data.confirmed_by,
        comment=data.comment,
        status=data.status,
    )


@router.patch("/{payment_id}/fields", response_model=PaymentRead)
async def patch_payment_fields(
    payment_id: int,
    body: PaymentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = body.model_dump(exclude_none=True)
    payment = await update_payment_fields(db, payment_id, **data)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.patch("/{payment_id}/status", response_model=PaymentRead)
async def patch_payment_status(
    payment_id: int,
    body: PaymentStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payment = await update_payment_status(db, payment_id, body.status, months_paid=body.months_paid)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.delete("/{payment_id}", status_code=204)
async def delete_payment_route(
    payment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    deleted = await delete_payment(db, payment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Payment not found")


@router.get("/debtors")
async def get_debtors(db: Annotated[AsyncSession, Depends(get_db)]):
    return await list_debtors(db)


@router.get("", response_model=list[PaymentRead])
async def get_payments_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
):
    return await list_payments(db, user_id=user_id, status=status, limit=limit)
