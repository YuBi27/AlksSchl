from datetime import date
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Payment, User, StudentProfile, StudentGroup, Group


async def save_payment(
    db: AsyncSession,
    user_id: int,
    amount: float,
    period_start: date,
    period_end: date,
    payment_type: str,
    months_paid: int = 1,
    confirmed_by: Optional[int] = None,
    comment: Optional[str] = None,
    status: str = "created",
) -> Payment:
    p = Payment(
        user_id=user_id,
        amount=amount,
        period_start=period_start,
        period_end=period_end,
        payment_type=payment_type,
        months_paid=months_paid,
        confirmed_by=confirmed_by,
        comment=comment,
        status=status,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def list_payments(
    db: AsyncSession,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 20,
) -> list[Payment]:
    q = select(Payment).order_by(Payment.created_at.desc()).limit(limit)
    if user_id is not None:
        q = q.where(Payment.user_id == user_id)
    if status is not None:
        q = q.where(Payment.status == status)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_payment_status(
    db: AsyncSession,
    payment_id: int,
    status: str,
    months_paid: Optional[int] = None,
) -> Optional[Payment]:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        return None
    payment.status = status
    if months_paid is not None:
        payment.months_paid = months_paid
    await db.commit()
    await db.refresh(payment)
    return payment


async def update_payment_fields(
    db: AsyncSession,
    payment_id: int,
    **kwargs,
) -> Optional[Payment]:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        return None
    for key, value in kwargs.items():
        setattr(payment, key, value)
    await db.commit()
    await db.refresh(payment)
    return payment


async def delete_payment(db: AsyncSession, payment_id: int) -> bool:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        return False
    await db.delete(payment)
    await db.commit()
    return True


async def list_debtors(db: AsyncSession) -> list[dict]:
    """Active students with at least one overdue unpaid payment (period_end < today, status created/pending)."""
    today = date.today()

    debt_subq = (
        select(
            Payment.user_id,
            func.sum(Payment.amount).label("debt_total"),
            func.count(Payment.id).label("debt_count"),
        )
        .where(
            Payment.period_end < today,
            Payment.status.in_(["created", "pending_confirmation"]),
        )
        .group_by(Payment.user_id)
        .subquery()
    )

    groups_subq = (
        select(
            StudentGroup.user_id,
            func.string_agg(Group.name, ", ").label("group_names_str"),
        )
        .join(Group, Group.id == StudentGroup.group_id)
        .group_by(StudentGroup.user_id)
        .subquery()
    )

    q = (
        select(
            User,
            StudentProfile,
            debt_subq.c.debt_total,
            debt_subq.c.debt_count,
            groups_subq.c.group_names_str,
        )
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .join(debt_subq, debt_subq.c.user_id == User.id)
        .outerjoin(groups_subq, groups_subq.c.user_id == User.id)
        .where(
            User.role == "student",
            User.status == "active",
        )
    )
    result = await db.execute(q)
    return [
        {
            "id": user.id,
            "full_name": profile.full_name if profile else None,
            "phone": profile.phone if profile else None,
            "debt_total": float(debt_total) if debt_total else 0.0,
            "debt_count": int(debt_count) if debt_count else 0,
            "group_names": group_names_str.split(", ") if group_names_str else [],
        }
        for user, profile, debt_total, debt_count, group_names_str in result.all()
    ]
