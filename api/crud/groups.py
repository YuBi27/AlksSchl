from typing import Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Group, StudentGroup, User, StudentProfile


async def get_group(db: AsyncSession, group_id: int) -> Optional[Group]:
    result = await db.execute(select(Group).where(Group.id == group_id))
    return result.scalar_one_or_none()


async def get_all_groups(db: AsyncSession, teacher_id: Optional[int] = None) -> list[dict]:
    stmt = (
        select(
            Group.id,
            Group.name,
            Group.level,
            Group.teacher_id,
            Group.description,
            Group.created_at,
            func.count(StudentGroup.id).label("student_count"),
        )
        .outerjoin(StudentGroup, StudentGroup.group_id == Group.id)
        .group_by(Group.id)
    )
    if teacher_id is not None:
        stmt = stmt.where(Group.teacher_id == teacher_id)
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "level": r.level,
            "teacher_id": r.teacher_id,
            "description": r.description,
            "created_at": r.created_at,
            "student_count": r.student_count,
        }
        for r in rows
    ]


async def create_group(
    db: AsyncSession,
    name: str,
    level: Optional[str] = None,
    description: Optional[str] = None,
    teacher_id: Optional[int] = None,
) -> Group:
    group = Group(name=name, level=level, description=description, teacher_id=teacher_id)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def update_group(
    db: AsyncSession, group_id: int, **kwargs
) -> Optional[Group]:
    group = await get_group(db, group_id)
    if not group:
        return None
    for key, value in kwargs.items():
        setattr(group, key, value)
    await db.commit()
    await db.refresh(group)
    return group


async def delete_group(db: AsyncSession, group_id: int) -> bool:
    group = await get_group(db, group_id)
    if not group:
        return False
    await db.delete(group)
    await db.commit()
    return True


async def get_group_students(
    db: AsyncSession, group_id: int, offset: int = 0, limit: int = 10
) -> list[dict]:
    result = await db.execute(
        select(User, StudentProfile)
        .join(StudentGroup, StudentGroup.user_id == User.id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(StudentGroup.group_id == group_id)
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "status": user.status,
            "full_name": profile.full_name if profile else None,
            "phone": profile.phone if profile else None,
            "english_level": profile.english_level if profile else None,
        }
        for user, profile in rows
    ]
