from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Lesson


async def get_lesson(db: AsyncSession, lesson_id: int) -> Optional[Lesson]:
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    return result.scalar_one_or_none()


async def get_lessons(
    db: AsyncSession,
    group_id: Optional[int] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    status: Optional[str] = None,
) -> list[Lesson]:
    query = select(Lesson).order_by(Lesson.scheduled_at)
    if group_id is not None:
        query = query.where(Lesson.group_id == group_id)
    if from_dt is not None:
        query = query.where(Lesson.scheduled_at >= from_dt)
    if to_dt is not None:
        query = query.where(Lesson.scheduled_at <= to_dt)
    if status is not None:
        query = query.where(Lesson.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_lesson(
    db: AsyncSession,
    group_id: int,
    scheduled_at: datetime,
    duration_min: int = 60,
    zoom_link: Optional[str] = None,
) -> Lesson:
    lesson = Lesson(
        group_id=group_id,
        scheduled_at=scheduled_at,
        duration_min=duration_min,
        zoom_link=zoom_link,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def update_lesson(
    db: AsyncSession, lesson_id: int, **kwargs
) -> Optional[Lesson]:
    lesson = await get_lesson(db, lesson_id)
    if not lesson:
        return None
    for key, value in kwargs.items():
        setattr(lesson, key, value)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def cancel_lesson(db: AsyncSession, lesson_id: int) -> bool:
    lesson = await get_lesson(db, lesson_id)
    if not lesson:
        return False
    lesson.status = "cancelled"
    await db.commit()
    return True


async def get_due_reminders(db: AsyncSession) -> list[Lesson]:
    """Return lessons that need a reminder sent right now."""
    now = datetime.now(tz=ZoneInfo("UTC"))
    result = await db.execute(
        select(Lesson).where(
            Lesson.status == "scheduled",
            Lesson.scheduled_at > now,
            or_(
                and_(
                    Lesson.scheduled_at <= now + timedelta(hours=24),
                    Lesson.reminder_24h_sent.is_(False),
                ),
                and_(
                    Lesson.scheduled_at <= now + timedelta(hours=2),
                    Lesson.reminder_2h_sent.is_(False),
                ),
                and_(
                    Lesson.scheduled_at <= now + timedelta(minutes=30),
                    Lesson.reminder_30m_sent.is_(False),
                ),
            )
        )
    )
    return list(result.scalars().all())


async def mark_reminder_sent(
    db: AsyncSession,
    lesson_id: int,
    reminder_type: str,
) -> bool:
    """reminder_type: '24h' | '2h' | '30min'"""
    lesson = await get_lesson(db, lesson_id)
    if not lesson:
        return False
    field_map = {
        "24h": "reminder_24h_sent",
        "2h": "reminder_2h_sent",
        "30min": "reminder_30m_sent",
    }
    field = field_map.get(reminder_type)
    if not field:
        return False
    setattr(lesson, field, True)
    await db.commit()
    return True
