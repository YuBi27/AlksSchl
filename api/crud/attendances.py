from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Attendance


async def upsert_attendance(
    db: AsyncSession,
    lesson_id: int,
    student_user_id: int,
    status: str,
) -> Attendance:
    result = await db.execute(
        select(Attendance).where(
            Attendance.lesson_id == lesson_id,
            Attendance.student_user_id == student_user_id,
        )
    )
    att = result.scalar_one_or_none()
    if att:
        att.status = status
    else:
        att = Attendance(
            lesson_id=lesson_id,
            student_user_id=student_user_id,
            status=status,
        )
        db.add(att)
    await db.commit()
    await db.refresh(att)
    return att


async def get_attendances(
    db: AsyncSession,
    lesson_id: Optional[int] = None,
    student_user_id: Optional[int] = None,
) -> list[Attendance]:
    q = select(Attendance)
    if lesson_id is not None:
        q = q.where(Attendance.lesson_id == lesson_id)
    if student_user_id is not None:
        q = q.where(Attendance.student_user_id == student_user_id)
    result = await db.execute(q)
    return list(result.scalars().all())
