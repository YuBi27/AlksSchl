from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import LessonCreate, LessonRead, LessonUpdate, ReminderUpdate
from api.crud.lessons import (
    get_lesson, get_lessons, create_lesson, update_lesson,
    cancel_lesson, get_due_reminders,
)

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/due-reminders", response_model=list[LessonRead])
async def due_reminders_endpoint(db: AsyncSession = Depends(get_db)):
    return await get_due_reminders(db)


@router.get("", response_model=list[LessonRead])
async def list_lessons_endpoint(
    group_id: Optional[int] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await get_lessons(db, group_id, from_dt, to_dt, status)


@router.post("", status_code=201, response_model=LessonRead)
async def create_lesson_endpoint(
    data: LessonCreate, db: AsyncSession = Depends(get_db)
):
    return await create_lesson(
        db, data.group_id, data.scheduled_at, data.duration_min, data.zoom_link
    )


@router.get("/{lesson_id}", response_model=LessonRead)
async def get_lesson_endpoint(
    lesson_id: int, db: AsyncSession = Depends(get_db)
):
    lesson = await get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.patch("/{lesson_id}/reminders", response_model=LessonRead)
async def update_reminders_endpoint(
    lesson_id: int, data: ReminderUpdate, db: AsyncSession = Depends(get_db)
):
    lesson = await update_lesson(db, lesson_id, **data.model_dump(exclude_none=True))
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.patch("/{lesson_id}", response_model=LessonRead)
async def update_lesson_endpoint(
    lesson_id: int, data: LessonUpdate, db: AsyncSession = Depends(get_db)
):
    lesson = await update_lesson(db, lesson_id, **data.model_dump(exclude_none=True))
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.delete("/{lesson_id}", status_code=204)
async def cancel_lesson_endpoint(
    lesson_id: int, db: AsyncSession = Depends(get_db)
):
    ok = await cancel_lesson(db, lesson_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Lesson not found")
