from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.crud.stats import get_stats_overview
from api.crud.analytics import get_financial_stats, get_attendance_stats, get_performance_stats
from api.schemas.schemas import FinancialStats, AttendanceStats, PerformanceStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
async def stats_overview_endpoint(db: Annotated[AsyncSession, Depends(get_db)]):
    return await get_stats_overview(db)


@router.get("/financial", response_model=FinancialStats)
async def financial(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = 30,
):
    if not (7 <= days <= 365):
        raise HTTPException(status_code=400, detail="days must be between 7 and 365")
    return await get_financial_stats(db, days=days)


@router.get("/attendance", response_model=AttendanceStats)
async def attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = 30,
    group_id: Optional[int] = None,
):
    if not (7 <= days <= 365):
        raise HTTPException(status_code=400, detail="days must be between 7 and 365")
    return await get_attendance_stats(db, days=days, group_id=group_id)


@router.get("/performance", response_model=PerformanceStats)
async def performance(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = 30,
    group_id: Optional[int] = None,
):
    if not (7 <= days <= 365):
        raise HTTPException(status_code=400, detail="days must be between 7 and 365")
    return await get_performance_stats(db, days=days, group_id=group_id)
