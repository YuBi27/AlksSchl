from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import User


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_users_by_status(db: AsyncSession, status: str) -> list[User]:
    result = await db.execute(select(User).where(User.status == status))
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    role: str,
    status: str,
    language: str = "uk",
) -> User:
    user = User(telegram_id=telegram_id, username=username, role=role, status=status, language=language)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_language(db: AsyncSession, user_id: int, language: str) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    user.language = language
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_status(db: AsyncSession, user_id: int, status: str) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    user.status = status
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_role(db: AsyncSession, user_id: int, role: str) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    user.role = role
    await db.commit()
    await db.refresh(user)
    return user
