from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.crud.stats import get_stats_overview

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
async def stats_overview_endpoint(db: Annotated[AsyncSession, Depends(get_db)]):
    return await get_stats_overview(db)
