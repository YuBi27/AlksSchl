from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import GroupCreate, GroupRead, GroupUpdate
from api.crud.groups import (
    get_all_groups, create_group, get_group,
    update_group, delete_group, get_group_students,
)

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("")
async def list_groups(db: AsyncSession = Depends(get_db)):
    return await get_all_groups(db)


@router.post("", status_code=201, response_model=GroupRead)
async def create_group_endpoint(
    data: GroupCreate, db: AsyncSession = Depends(get_db)
):
    group = await create_group(db, data.name, data.level, data.description)
    return {
        "id": group.id,
        "name": group.name,
        "level": group.level,
        "description": group.description,
        "teacher_id": group.teacher_id,
        "created_at": group.created_at,
        "student_count": 0,
    }


@router.get("/{group_id}")
async def get_group_endpoint(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return {
        "id": group.id,
        "name": group.name,
        "level": group.level,
        "teacher_id": group.teacher_id,
        "description": group.description,
        "created_at": group.created_at,
        "student_count": 0,
    }


@router.patch("/{group_id}")
async def update_group_endpoint(
    group_id: int, data: GroupUpdate, db: AsyncSession = Depends(get_db)
):
    group = await update_group(
        db, group_id, **data.model_dump(exclude_none=True)
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return {
        "id": group.id,
        "name": group.name,
        "level": group.level,
        "description": group.description,
        "teacher_id": group.teacher_id,
        "created_at": group.created_at,
        "student_count": 0,
    }


@router.delete("/{group_id}", status_code=204)
async def delete_group_endpoint(
    group_id: int, db: AsyncSession = Depends(get_db)
):
    ok = await delete_group(db, group_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Group not found")


@router.get("/{group_id}/students")
async def get_group_students_endpoint(
    group_id: int,
    offset: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    group = await get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return await get_group_students(db, group_id, offset, limit)
