from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import BotContent, TeacherProfile


async def get_content(db: AsyncSession, key: str) -> Optional[BotContent]:
    result = await db.execute(select(BotContent).where(BotContent.key == key))
    return result.scalar_one_or_none()


async def upsert_content(
    db: AsyncSession,
    key: str,
    value: str,
    updated_by: Optional[int] = None,
) -> BotContent:
    result = await db.execute(select(BotContent).where(BotContent.key == key))
    existing = result.scalar_one_or_none()
    if existing:
        existing.value = value
        existing.updated_by = updated_by
        existing.updated_at = datetime.now(tz=timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return existing
    item = BotContent(key=key, value=value, updated_by=updated_by)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_all_teacher_profiles(db: AsyncSession) -> list[TeacherProfile]:
    result = await db.execute(select(TeacherProfile))
    return list(result.scalars().all())
