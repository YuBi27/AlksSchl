from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Homework, HomeworkGrade
from api.schemas.schemas import HomeworkCreate


async def get_homeworks(
    db: AsyncSession,
    teacher_id: Optional[int] = None,
    group_id: Optional[int] = None,
    student_user_id: Optional[int] = None,
) -> list[Homework]:
    q = select(Homework)
    if teacher_id is not None:
        q = q.where(Homework.teacher_id == teacher_id)
    if group_id is not None:
        q = q.where(Homework.group_id == group_id)
    if student_user_id is not None:
        q = q.where(Homework.student_user_id == student_user_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_homework(db: AsyncSession, data: HomeworkCreate) -> Homework:
    hw = Homework(**data.model_dump())
    db.add(hw)
    await db.commit()
    await db.refresh(hw)
    return hw


async def get_homework(db: AsyncSession, homework_id: int) -> Optional[Homework]:
    result = await db.execute(select(Homework).where(Homework.id == homework_id))
    return result.scalar_one_or_none()


async def update_homework(db: AsyncSession, homework_id: int, **kwargs) -> Optional[Homework]:
    hw = await get_homework(db, homework_id)
    if not hw:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(hw, key, value)
    await db.commit()
    await db.refresh(hw)
    return hw


async def delete_homework(db: AsyncSession, homework_id: int) -> bool:
    hw = await get_homework(db, homework_id)
    if not hw:
        return False
    await db.delete(hw)
    await db.commit()
    return True


async def get_homework_grades(db: AsyncSession, homework_id: int) -> list[HomeworkGrade]:
    result = await db.execute(
        select(HomeworkGrade).where(HomeworkGrade.homework_id == homework_id)
    )
    return list(result.scalars().all())


async def upsert_grade(
    db: AsyncSession,
    homework_id: int,
    student_user_id: int,
    grade_text: str,
    graded_by: Optional[int] = None,
) -> HomeworkGrade:
    result = await db.execute(
        select(HomeworkGrade).where(
            HomeworkGrade.homework_id == homework_id,
            HomeworkGrade.student_user_id == student_user_id,
        )
    )
    grade = result.scalar_one_or_none()
    if grade:
        grade.grade_text = grade_text
        if graded_by is not None:
            grade.graded_by = graded_by
    else:
        grade = HomeworkGrade(
            homework_id=homework_id,
            student_user_id=student_user_id,
            grade_text=grade_text,
            graded_by=graded_by,
        )
        db.add(grade)
    await db.commit()
    await db.refresh(grade)
    return grade
