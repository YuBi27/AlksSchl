from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Agreement


async def create_agreement(
    db: AsyncSession, user_id: int, telegram_id: int, agreement_type: str
) -> Agreement:
    agreement = Agreement(user_id=user_id, telegram_id=telegram_id, type=agreement_type)
    db.add(agreement)
    await db.commit()
    await db.refresh(agreement)
    return agreement
