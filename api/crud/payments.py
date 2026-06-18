from datetime import date
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Payment, User, StudentProfile


async def save_payment(
    db: AsyncSession,
    user_id: int,
    amount: float,
    period_start: date,
    period_end: date,
    payment_type: str,
    confirmed_by: Optional[int] = None,
    comment: Optional[str] = None,
) -> Payment:
    p = Payment(
        user_id=user_id,
        amount=amount,
        period_start=period_start,
        period_end=period_end,
        payment_type=payment_type,
        confirmed_by=confirmed_by,
        comment=comment,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def list_payments(
    db: AsyncSession,
    user_id: Optional[int] = None,
    limit: int = 20,
) -> list[Payment]:
    q = select(Payment).order_by(Payment.created_at.desc()).limit(limit)
    if user_id is not None:
        q = q.where(Payment.user_id == user_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_debtors(db: AsyncSession) -> list[dict]:
    """Active students with no payment where period_end >= first day of current month."""
    first_of_month = date.today().replace(day=1)

    paid_subq = (
        select(Payment.user_id)
        .where(Payment.period_end >= first_of_month)
        .scalar_subquery()
    )

    q = (
        select(User, StudentProfile)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(
            User.role == "student",
            User.status == "active",
            User.id.not_in(paid_subq),
        )
    )
    result = await db.execute(q)
    return [
        {
            "id": user.id,
            "full_name": profile.full_name if profile else None,
            "phone": profile.phone if profile else None,
        }
        for user, profile in result.all()
    ]
