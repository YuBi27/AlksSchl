from typing import Optional
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import StudentProfile, TeacherProfile


async def create_student_profile(
    db: AsyncSession,
    user_id: int,
    full_name: str,
    birth_date: Optional[date] = None,
    phone: Optional[str] = None,
    parent_name: Optional[str] = None,
    parent_phone: Optional[str] = None,
    study_start_month: Optional[str] = None,
    study_format: Optional[str] = None,
    extra_info: Optional[str] = None,
    notion_link: Optional[str] = None,
) -> StudentProfile:
    profile = await get_student_profile(db, user_id)
    if profile:
        profile.full_name = full_name
        profile.birth_date = birth_date
        profile.phone = phone
        profile.parent_name = parent_name
        profile.parent_phone = parent_phone
        profile.study_start_month = study_start_month
        profile.study_format = study_format
        profile.extra_info = extra_info
        if notion_link:
            profile.notion_link = notion_link
    else:
        profile = StudentProfile(
            user_id=user_id, full_name=full_name, birth_date=birth_date,
            phone=phone, parent_name=parent_name, parent_phone=parent_phone,
            study_start_month=study_start_month, study_format=study_format,
            extra_info=extra_info, notion_link=notion_link,
        )
        db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_student_profile(db: AsyncSession, user_id: int) -> Optional[StudentProfile]:
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def create_teacher_profile(
    db: AsyncSession,
    user_id: int,
    full_name: str,
    photo_file_id: Optional[str] = None,
    bio: Optional[str] = None,
    specialization: Optional[str] = None,
    experience_years: Optional[int] = None,
) -> TeacherProfile:
    profile = TeacherProfile(
        user_id=user_id, full_name=full_name, photo_file_id=photo_file_id,
        bio=bio, specialization=specialization, experience_years=experience_years,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_teacher_profile(db: AsyncSession, user_id: int) -> Optional[TeacherProfile]:
    result = await db.execute(select(TeacherProfile).where(TeacherProfile.user_id == user_id))
    return result.scalar_one_or_none()
