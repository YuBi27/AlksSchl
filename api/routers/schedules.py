from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import ScheduleCreate, ScheduleRead
from api.crud.schedules import (
    get_schedule, get_schedules_by_group, create_schedule,
    update_schedule, delete_schedule, generate_all_upcoming,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/generate-upcoming")
async def generate_upcoming_endpoint(db: AsyncSession = Depends(get_db)):
    generated = await generate_all_upcoming(db)
    return {"generated": generated}


@router.get("", response_model=list[ScheduleRead])
async def list_schedules(
    group_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    if group_id is None:
        return []
    return await get_schedules_by_group(db, group_id)


@router.post("", status_code=201, response_model=ScheduleRead)
async def create_schedule_endpoint(
    data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_schedule(
        db, data.group_id, data.day_of_week, data.start_time, data.duration_min
    )


@router.get("/{schedule_id}", response_model=ScheduleRead)
async def get_schedule_endpoint(
    schedule_id: int, db: AsyncSession = Depends(get_db)
):
    schedule = await get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.patch("/{schedule_id}", response_model=ScheduleRead)
async def update_schedule_endpoint(
    schedule_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    schedule = await update_schedule(db, schedule_id, **data)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule_endpoint(
    schedule_id: int, db: AsyncSession = Depends(get_db)
):
    ok = await delete_schedule(db, schedule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Schedule not found")
