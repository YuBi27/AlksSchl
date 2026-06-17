from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import StudentLevelUpdate, StudentGroupsUpdate, ImportRow, ImportResult, StudentListItem
from api.crud.students import (
    list_students, get_student, set_student_level,
    set_student_groups, remove_from_group, soft_delete_student,
    bulk_import_students,
)

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/import", response_model=ImportResult)
async def import_students_endpoint(
    rows: list[ImportRow], db: AsyncSession = Depends(get_db)
):
    result = await bulk_import_students(db, [r.model_dump() for r in rows])
    return result


@router.get("", response_model=list[StudentListItem])
async def list_students_endpoint(
    search: Optional[str] = None,
    group_id: Optional[int] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await list_students(db, search, group_id, level, status, offset, limit)


@router.get("/{user_id}", response_model=StudentListItem)
async def get_student_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    student = await get_student(db, user_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.patch("/{user_id}/level", status_code=204)
async def set_level_endpoint(
    user_id: int, data: StudentLevelUpdate, db: AsyncSession = Depends(get_db)
):
    ok = await set_student_level(db, user_id, data.level)
    if not ok:
        raise HTTPException(status_code=404, detail="Student profile not found")


@router.post("/{user_id}/groups", status_code=204)
async def assign_groups_endpoint(
    user_id: int, data: StudentGroupsUpdate, db: AsyncSession = Depends(get_db)
):
    student = await get_student(db, user_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    await set_student_groups(db, user_id, data.group_ids)


@router.delete("/{user_id}/groups/{group_id}", status_code=204)
async def remove_from_group_endpoint(
    user_id: int, group_id: int, db: AsyncSession = Depends(get_db)
):
    ok = await remove_from_group(db, user_id, group_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Membership not found")


@router.delete("/{user_id}", status_code=204)
async def delete_student_endpoint(
    user_id: int, db: AsyncSession = Depends(get_db)
):
    ok = await soft_delete_student(db, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Student not found")
