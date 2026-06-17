from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import ScheduleRead
from api.crud.schedules import (
    get_schedule, get_schedules_by_group, create_schedule,
    update_schedule, delete_schedule, generate_all_upcoming,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _schedule_to_dict(s) -> dict:
    return {
        "id": s.id,
        "group_id": s.group_id,
        "day_of_week": s.day_of_week,
        "start_time": s.start_time.strftime("%H:%M"),
        "duration_min": s.duration_min,
        "is_active": s.is_active,
        "created_at": s.created_at,
    }


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
    schedules = await get_schedules_by_group(db, group_id)
    return [_schedule_to_dict(s) for s in schedules]


@router.post("", status_code=201, response_model=ScheduleRead)
async def create_schedule_endpoint(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    schedule = await create_schedule(
        db, data["group_id"], data["day_of_week"], data["start_time"], data.get("duration_min", 60)
    )
    return _schedule_to_dict(schedule)


@router.get("/{schedule_id}", response_model=ScheduleRead)
async def get_schedule_endpoint(
    schedule_id: int, db: AsyncSession = Depends(get_db)
):
    schedule = await get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _schedule_to_dict(schedule)


@router.patch("/{schedule_id}", response_model=ScheduleRead)
async def update_schedule_endpoint(
    schedule_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    schedule = await update_schedule(db, schedule_id, **data)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _schedule_to_dict(schedule)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule_endpoint(
    schedule_id: int, db: AsyncSession = Depends(get_db)
):
    ok = await delete_schedule(db, schedule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Schedule not found")
