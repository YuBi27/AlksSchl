from fastapi import Header, HTTPException, status
from api.config import settings

async def verify_bot_secret(x_bot_secret: str = Header(...)) -> None:
    if x_bot_secret != settings.bot_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid bot secret",
        )
