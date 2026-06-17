from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import InviteCode


async def get_invite_code(db: AsyncSession, code: str) -> Optional[InviteCode]:
    result = await db.execute(select(InviteCode).where(InviteCode.code == code))
    return result.scalar_one_or_none()


async def create_invite_code(
    db: AsyncSession,
    code: str,
    created_by: Optional[int],
    role: str = "teacher",
    expires_at: Optional[datetime] = None,
) -> InviteCode:
    invite = InviteCode(code=code, created_by=created_by, role=role, expires_at=expires_at)
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


async def use_invite_code(db: AsyncSession, code: str, user_id: int) -> Optional[InviteCode]:
    invite = await get_invite_code(db, code)
    if not invite or invite.used_by is not None:
        return None
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        return None
    invite.used_by = user_id
    invite.used_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(invite)
    return invite


def is_code_valid(invite: InviteCode) -> bool:
    if invite.used_by is not None:
        return False
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        return False
    return True
