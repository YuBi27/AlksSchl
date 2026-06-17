from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import TeacherNoteCreate, TeacherNoteRead
from api.crud.teacher_notes import get_notes, create_note, delete_note

router = APIRouter(prefix="/teacher-notes", tags=["teacher-notes"])


@router.get("", response_model=list[TeacherNoteRead])
async def list_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    student_user_id: Optional[int] = None,
    lesson_id: Optional[int] = None,
):
    return await get_notes(db, student_user_id=student_user_id, lesson_id=lesson_id)


@router.post("", response_model=TeacherNoteRead, status_code=201)
async def create(body: TeacherNoteCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    return await create_note(db, body)


@router.delete("/{note_id}", status_code=204)
async def delete(note_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    deleted = await delete_note(db, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
