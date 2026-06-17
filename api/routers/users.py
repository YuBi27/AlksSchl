from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import (
    UserOut, UserLanguageUpdate, UserStatusUpdate,
    StudentProfileCreate, StudentProfileOut,
    TeacherProfileCreate, TeacherProfileOut,
)
from api.crud.users import (
    get_user_by_telegram_id, get_user_by_id,
    update_user_language, update_user_status, get_users_by_status,
)
from api.crud.profiles import (
    create_student_profile, get_student_profile,
    create_teacher_profile, get_teacher_profile,
)
from api.models.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
):
    if status:
        return await get_users_by_status(db, status)
    result = await db.execute(select(User))
    return list(result.scalars().all())


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{telegram_id}/language", response_model=UserOut)
async def set_language(
    telegram_id: int,
    body: UserLanguageUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await update_user_language(db, user.id, body.language)


@router.patch("/{user_id}/status", response_model=UserOut)
async def set_status(
    user_id: int,
    body: UserStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await update_user_status(db, user_id, body.status)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/{user_id}/student-profile", response_model=StudentProfileOut)
async def create_student(
    user_id: int,
    body: StudentProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await create_student_profile(db, user_id=user_id, **body.model_dump())


@router.get("/{user_id}/student-profile", response_model=StudentProfileOut)
async def get_student(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    profile = await get_student_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/{user_id}/teacher-profile", response_model=TeacherProfileOut)
async def create_teacher(
    user_id: int,
    body: TeacherProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await create_teacher_profile(db, user_id=user_id, **body.model_dump())
