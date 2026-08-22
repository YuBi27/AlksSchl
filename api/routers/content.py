from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.crud.content import get_content, upsert_content, get_all_teacher_profiles
from api.schemas.schemas import BotContentRead, BotContentUpdate, TeacherProfileOut

router = APIRouter(tags=["content"])


@router.get("/bot-content/{key}", response_model=BotContentRead)
async def get_content_endpoint(
    key: str, db: Annotated[AsyncSession, Depends(get_db)]
):
    item = await get_content(db, key)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return item


@router.put("/bot-content/{key}", response_model=BotContentRead)
async def upsert_content_endpoint(
    key: str,
    data: BotContentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await upsert_content(
        db, key, data.value, data.updated_by,
        file_id=data.file_id, file_type=data.file_type,
    )


@router.get("/teacher-profiles", response_model=list[TeacherProfileOut])
async def list_teacher_profiles(db: Annotated[AsyncSession, Depends(get_db)]):
    return await get_all_teacher_profiles(db)
