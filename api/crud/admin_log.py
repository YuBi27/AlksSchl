from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import AdminActionLog


async def log_action(
    db: AsyncSession,
    admin_id: int,
    action: str,
    target_user_id: Optional[int] = None,
    details: Optional[dict] = None,
) -> AdminActionLog:
    entry = AdminActionLog(admin_id=admin_id, action=action, target_user_id=target_user_id, details=details)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry
