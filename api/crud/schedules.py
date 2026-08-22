from datetime import datetime, date, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Schedule, Lesson


async def _drop_future_lessons(db: AsyncSession, schedule_id: int) -> None:
    """Remove future non-completed lessons of a template.

    Used when a template is edited or deleted: stale occurrences must vanish
    from the schedule entirely (not linger as "cancelled" clutter). Explicitly
    cancelled single lessons are unaffected — this only runs on template change.
    """
    now_utc = datetime.now(tz=ZoneInfo("UTC"))
    await db.execute(
        delete(Lesson).where(
            Lesson.schedule_id == schedule_id,
            Lesson.scheduled_at > now_utc,
            Lesson.status != "completed",
        )
    )

KYIV_TZ = ZoneInfo("Europe/Kyiv")
WEEKS_AHEAD = 8


def _kyiv_to_utc(d: date, t: time) -> datetime:
    """Combine a Kyiv-timezone date+time and return UTC-aware datetime."""
    naive = datetime.combine(d, t)
    kyiv_aware = naive.replace(tzinfo=KYIV_TZ)
    return kyiv_aware.astimezone(ZoneInfo("UTC"))


def _parse_time(s: str) -> time:
    """Parse 'HH:MM' string to datetime.time."""
    return datetime.strptime(s, "%H:%M").time()


async def generate_lessons_for_schedule(
    db: AsyncSession, schedule: Schedule, from_date: Optional[date] = None
) -> int:
    """Generate lessons for the next WEEKS_AHEAD weeks. Returns count created."""
    today = from_date or date.today()
    end_date = today + timedelta(weeks=WEEKS_AHEAD)

    days_until = (schedule.day_of_week - today.weekday()) % 7
    current = today + timedelta(days=days_until)

    created = 0
    while current <= end_date:
        scheduled_at = _kyiv_to_utc(current, schedule.start_time)
        existing = await db.execute(
            select(Lesson).where(
                Lesson.schedule_id == schedule.id,
                Lesson.scheduled_at == scheduled_at,
            )
        )
        if not existing.scalar_one_or_none():
            db.add(Lesson(
                group_id=schedule.group_id,
                schedule_id=schedule.id,
                scheduled_at=scheduled_at,
                duration_min=schedule.duration_min,
            ))
            created += 1
        current += timedelta(days=7)

    await db.commit()
    return created


async def get_schedule(db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    return result.scalar_one_or_none()


async def get_schedules_by_group(
    db: AsyncSession, group_id: int
) -> list[Schedule]:
    result = await db.execute(
        select(Schedule).where(
            Schedule.group_id == group_id,
            Schedule.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


async def create_schedule(
    db: AsyncSession,
    group_id: int,
    day_of_week: int,
    start_time_str: str,
    duration_min: int = 60,
) -> Schedule:
    t = _parse_time(start_time_str)
    schedule = Schedule(
        group_id=group_id,
        day_of_week=day_of_week,
        start_time=t,
        duration_min=duration_min,
    )
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    await generate_lessons_for_schedule(db, schedule)
    return schedule


async def update_schedule(
    db: AsyncSession,
    schedule_id: int,
    **kwargs,
) -> Optional[Schedule]:
    schedule = await get_schedule(db, schedule_id)
    if not schedule:
        return None
    if "start_time" in kwargs:
        kwargs["start_time"] = _parse_time(kwargs["start_time"])
    for key, value in kwargs.items():
        setattr(schedule, key, value)
    await db.commit()
    await db.refresh(schedule)
    # Stale future lessons must disappear from the schedule, not become "cancelled"
    await _drop_future_lessons(db, schedule_id)
    await db.commit()
    # Regenerate future lessons only
    await generate_lessons_for_schedule(db, schedule)
    return schedule


async def delete_schedule(db: AsyncSession, schedule_id: int) -> bool:
    schedule = await get_schedule(db, schedule_id)
    if not schedule:
        return False
    await _drop_future_lessons(db, schedule_id)
    schedule.is_active = False
    await db.commit()
    return True


async def generate_all_upcoming(db: AsyncSession) -> int:
    """Generate lessons for all active schedules. Called by weekly bot task."""
    result = await db.execute(
        select(Schedule).where(Schedule.is_active.is_(True))
    )
    schedules = list(result.scalars().all())
    total = 0
    for schedule in schedules:
        total += await generate_lessons_for_schedule(db, schedule)
    return total
