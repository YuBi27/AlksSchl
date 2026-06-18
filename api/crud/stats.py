from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import User, Group, StudentGroup, Lesson, Homework, HomeworkGrade, Attendance


async def get_stats_overview(db: AsyncSession) -> dict:
    now = datetime.now(tz=timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_end = today_start + timedelta(days=7)
    thirty_days_ago = today_start - timedelta(days=30)

    total_students = (await db.execute(
        select(func.count(User.id)).where(User.role == "student", User.status == "active")
    )).scalar_one()

    pending_students = (await db.execute(
        select(func.count(User.id)).where(User.role == "student", User.status == "pending")
    )).scalar_one()

    total_groups = (await db.execute(
        select(func.count(Group.id))
    )).scalar_one()

    lessons_today = (await db.execute(
        select(func.count(Lesson.id)).where(
            Lesson.scheduled_at >= today_start,
            Lesson.scheduled_at < today_end,
        )
    )).scalar_one()

    lessons_this_week = (await db.execute(
        select(func.count(Lesson.id)).where(
            Lesson.scheduled_at >= today_start,
            Lesson.scheduled_at < week_end,
        )
    )).scalar_one()

    overdue_hw_subq = (
        select(HomeworkGrade.id)
        .where(HomeworkGrade.homework_id == Homework.id)
        .correlate(Homework)
        .exists()
    )
    overdue_homework = (await db.execute(
        select(func.count(Homework.id)).where(
            Homework.due_at < now,
            ~overdue_hw_subq,
        )
    )).scalar_one()

    hw_due_this_week = (await db.execute(
        select(func.count(Homework.id)).where(
            Homework.due_at >= now,
            Homework.due_at < week_end,
        )
    )).scalar_one()

    groups_result = await db.execute(select(Group))
    all_groups = list(groups_result.scalars().all())

    attendance_by_group = []
    for group in all_groups:
        lessons_result = await db.execute(
            select(Lesson.id).where(
                Lesson.group_id == group.id,
                Lesson.scheduled_at >= thirty_days_ago,
                Lesson.scheduled_at < now,
            )
        )
        lesson_ids = [row[0] for row in lessons_result.all()]
        if not lesson_ids:
            continue

        student_count = (await db.execute(
            select(func.count(StudentGroup.id)).where(StudentGroup.group_id == group.id)
        )).scalar_one()

        total_possible = len(lesson_ids) * student_count
        if total_possible == 0:
            continue

        attended = (await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.lesson_id.in_(lesson_ids),
                Attendance.status == "present",
            )
        )).scalar_one()

        attendance_by_group.append({
            "group_id": group.id,
            "group_name": group.name,
            "total_lessons": len(lesson_ids),
            "attended": attended,
            "percent": round(attended * 100 / total_possible),
        })

    return {
        "total_students": total_students,
        "pending_students": pending_students,
        "total_groups": total_groups,
        "lessons_today": lessons_today,
        "lessons_this_week": lessons_this_week,
        "overdue_homework": overdue_homework,
        "hw_due_this_week": hw_due_this_week,
        "attendance_by_group": attendance_by_group,
    }
