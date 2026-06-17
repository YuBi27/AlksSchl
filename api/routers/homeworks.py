from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import (
    HomeworkCreate, HomeworkUpdate, HomeworkRead,
    HomeworkGradeCreate, HomeworkGradeRead,
)
from api.crud.homeworks import (
    get_homeworks, create_homework, get_homework,
    update_homework, delete_homework,
    get_homework_grades, upsert_grade,
)

router = APIRouter(prefix="/homeworks", tags=["homeworks"])


@router.get("", response_model=list[HomeworkRead])
async def list_homeworks(
    db: Annotated[AsyncSession, Depends(get_db)],
    teacher_id: Optional[int] = None,
    group_id: Optional[int] = None,
    student_user_id: Optional[int] = None,
):
    return await get_homeworks(db, teacher_id=teacher_id, group_id=group_id, student_user_id=student_user_id)


@router.post("", response_model=HomeworkRead, status_code=201)
async def create(body: HomeworkCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    return await create_homework(db, body)


@router.get("/{homework_id}", response_model=HomeworkRead)
async def get_one(homework_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    hw = await get_homework(db, homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    return hw


@router.patch("/{homework_id}", response_model=HomeworkRead)
async def update(
    homework_id: int,
    body: HomeworkUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    hw = await update_homework(db, homework_id, **body.model_dump(exclude_none=True))
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    return hw


@router.delete("/{homework_id}", status_code=204)
async def delete(homework_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    deleted = await delete_homework(db, homework_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Homework not found")


@router.get("/{homework_id}/grades", response_model=list[HomeworkGradeRead])
async def list_grades(homework_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    hw = await get_homework(db, homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    return await get_homework_grades(db, homework_id)


@router.post("/{homework_id}/grades", response_model=HomeworkGradeRead)
async def upsert(
    homework_id: int,
    body: HomeworkGradeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    hw = await get_homework(db, homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    return await upsert_grade(db, homework_id, body.student_user_id, body.grade_text, body.graded_by)
