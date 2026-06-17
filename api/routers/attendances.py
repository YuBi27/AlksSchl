from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import AttendanceUpsert, AttendanceRead
from api.crud.attendances import upsert_attendance, get_attendances

router = APIRouter(prefix="/attendances", tags=["attendances"])


@router.post("", response_model=AttendanceRead)
async def upsert(
    body: AttendanceUpsert,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await upsert_attendance(db, body.lesson_id, body.student_user_id, body.status)


@router.get("", response_model=list[AttendanceRead])
async def list_attendances(
    db: Annotated[AsyncSession, Depends(get_db)],
    lesson_id: Optional[int] = None,
    student_user_id: Optional[int] = None,
):
    return await get_attendances(db, lesson_id=lesson_id, student_user_id=student_user_id)
