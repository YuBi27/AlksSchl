from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Broadcast


async def save_broadcast(
    db: AsyncSession,
    target_type: str,
    message_type: str,
    recipient_count: int,
    sender_id: Optional[int] = None,
    target_id: Optional[int] = None,
    text: Optional[str] = None,
    file_id: Optional[str] = None,
) -> Broadcast:
    b = Broadcast(
        sender_id=sender_id,
        target_type=target_type,
        target_id=target_id,
        message_type=message_type,
        text=text,
        file_id=file_id,
        recipient_count=recipient_count,
    )
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


async def list_broadcasts(
    db: AsyncSession,
    sender_id: Optional[int] = None,
    limit: int = 20,
) -> list[Broadcast]:
    q = select(Broadcast).order_by(Broadcast.sent_at.desc()).limit(limit)
    if sender_id is not None:
        q = q.where(Broadcast.sender_id == sender_id)
    result = await db.execute(q)
    return list(result.scalars().all())
