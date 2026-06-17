import random
from typing import Optional
from sqlalchemy import select, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import User, StudentProfile, StudentGroup, Group

LEVEL_MAP = {
    "Новачок": "novice",
    "novice": "novice",
    "A1": "A1",
    "A2": "A2",
    "B1": "B1",
    "B2": "B2",
    "C1": "C1",
    "C2": "C2",
}


async def list_students(
    db: AsyncSession,
    search: Optional[str] = None,
    group_id: Optional[int] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict]:
    query = (
        select(User, StudentProfile)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(User.role == "student")
    )
    if search:
        query = query.where(
            or_(
                StudentProfile.full_name.ilike(f"%{search}%"),
                StudentProfile.phone.ilike(f"%{search}%"),
            )
        )
    if level:
        query = query.where(StudentProfile.english_level == level)
    if status:
        query = query.where(User.status == status)
    if group_id:
        query = query.join(
            StudentGroup, StudentGroup.user_id == User.id
        ).where(StudentGroup.group_id == group_id)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return []

    user_ids = [user.id for user, _ in rows]
    groups_result = await db.execute(
        select(StudentGroup.user_id, Group.name)
        .join(Group, Group.id == StudentGroup.group_id)
        .where(StudentGroup.user_id.in_(user_ids))
    )
    groups_by_user: dict[int, list[str]] = {}
    for user_id, group_name in groups_result.all():
        groups_by_user.setdefault(user_id, []).append(group_name)

    return [
        {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "status": user.status,
            "full_name": profile.full_name if profile else None,
            "phone": profile.phone if profile else None,
            "english_level": profile.english_level if profile else None,
            "group_names": groups_by_user.get(user.id, []),
        }
        for user, profile in rows
    ]


async def get_student(db: AsyncSession, user_id: int) -> Optional[dict]:
    result = await db.execute(
        select(User, StudentProfile)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(User.id == user_id, User.role == "student")
    )
    row = result.first()
    if not row:
        return None
    user, profile = row
    groups_result = await db.execute(
        select(Group.name)
        .join(StudentGroup, StudentGroup.group_id == Group.id)
        .where(StudentGroup.user_id == user.id)
    )
    group_names = list(groups_result.scalars().all())
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "status": user.status,
        "full_name": profile.full_name if profile else None,
        "phone": profile.phone if profile else None,
        "english_level": profile.english_level if profile else None,
        "group_names": group_names,
    }


async def set_student_level(db: AsyncSession, user_id: int, level: str) -> bool:
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return False
    profile.english_level = level
    await db.commit()
    return True


async def set_student_groups(
    db: AsyncSession, user_id: int, group_ids: list[int]
) -> None:
    await db.execute(delete(StudentGroup).where(StudentGroup.user_id == user_id))
    for gid in group_ids:
        db.add(StudentGroup(user_id=user_id, group_id=gid))
    await db.commit()


async def remove_from_group(
    db: AsyncSession, user_id: int, group_id: int
) -> bool:
    result = await db.execute(
        select(StudentGroup).where(
            StudentGroup.user_id == user_id,
            StudentGroup.group_id == group_id,
        )
    )
    sg = result.scalar_one_or_none()
    if not sg:
        return False
    await db.delete(sg)
    await db.commit()
    return True


async def soft_delete_student(db: AsyncSession, user_id: int) -> bool:
    result = await db.execute(
        select(User).where(User.id == user_id, User.role == "student")
    )
    user = result.scalar_one_or_none()
    if not user:
        return False
    user.status = "inactive"
    await db.commit()
    return True


async def bulk_import_students(
    db: AsyncSession, rows: list[dict]
) -> dict:
    created = 0
    skipped = 0
    errors: list[str] = []

    for row in rows:
        phone = (row.get("phone") or "").strip()
        full_name = (row.get("full_name") or "").strip()
        if not phone or not full_name:
            errors.append("Пропущено рядок: відсутні ПІБ або телефон")
            continue

        existing = await db.execute(
            select(StudentProfile).where(StudentProfile.phone == phone)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        level_raw = (row.get("level") or "").strip()
        level = LEVEL_MAP.get(level_raw)
        if level_raw and not level:
            errors.append(
                f"{full_name}: невідомий рівень '{level_raw}', встановлено None"
            )
            level = None

        fake_tg_id = -(random.randint(10**12, 10**13))
        user = User(
            telegram_id=fake_tg_id,
            username=None,
            language="uk",
            role="student",
            status="active",
        )
        db.add(user)
        await db.flush()

        profile = StudentProfile(
            user_id=user.id,
            full_name=full_name,
            phone=phone,
            english_level=level,
            notion_link=f"https://notion.so/PLACEHOLDER-{user.id}",
        )
        db.add(profile)

        group_name = (row.get("group_name") or "").strip()
        if group_name:
            g_result = await db.execute(
                select(Group).where(Group.name == group_name)
            )
            group = g_result.scalar_one_or_none()
            if not group:
                group = Group(name=group_name, level=level)
                db.add(group)
                await db.flush()
            db.add(StudentGroup(user_id=user.id, group_id=group.id))

        await db.flush()
        created += 1

    await db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}
