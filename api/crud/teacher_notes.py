from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import TeacherNote
from api.schemas.schemas import TeacherNoteCreate


async def get_notes(
    db: AsyncSession,
    student_user_id: Optional[int] = None,
    lesson_id: Optional[int] = None,
) -> list[TeacherNote]:
    q = select(TeacherNote)
    if student_user_id is not None:
        q = q.where(TeacherNote.student_user_id == student_user_id)
    if lesson_id is not None:
        q = q.where(TeacherNote.lesson_id == lesson_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_note(db: AsyncSession, data: TeacherNoteCreate) -> TeacherNote:
    note = TeacherNote(**data.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(db: AsyncSession, note_id: int) -> bool:
    result = await db.execute(select(TeacherNote).where(TeacherNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        return False
    await db.delete(note)
    await db.commit()
    return True
