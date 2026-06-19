from datetime import datetime, timedelta, timezone, date
from typing import Optional
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import (
    User, Group, StudentGroup, Lesson, Homework, HomeworkGrade,
    Attendance, Payment, QuizAttempt, StudentProfile,
)


async def get_financial_stats(db: AsyncSession, days: int = 30) -> dict:
    now = datetime.now(tz=timezone.utc)
    period_start = now - timedelta(days=days)

    status_result = await db.execute(
        select(Payment.status, func.count(Payment.id), func.sum(Payment.amount))
        .where(Payment.created_at >= period_start)
        .group_by(Payment.status)
    )
    totals: dict[str, tuple[int, float]] = {}
    for status, cnt, total in status_result.all():
        totals[status] = (cnt, float(total or 0))

    confirmed = totals.get("confirmed", (0, 0.0))
    pending = totals.get("pending_confirmation", (0, 0.0))
    rejected = totals.get("rejected", (0, 0.0))

    six_months_ago = now - timedelta(days=180)
    monthly_raw = await db.execute(
        select(Payment.amount, Payment.created_at)
        .where(Payment.status == "confirmed", Payment.created_at >= six_months_ago)
    )
    monthly_map: dict[str, dict] = {}
    for amount, created_at in monthly_raw.all():
        key = created_at.strftime("%Y-%m") if created_at else "unknown"
        if key not in monthly_map:
            monthly_map[key] = {"month": key, "revenue": 0.0, "count": 0}
        monthly_map[key]["revenue"] += float(amount or 0)
        monthly_map[key]["count"] += 1
    monthly_revenue = sorted(monthly_map.values(), key=lambda x: x["month"])

    today = date.today()
    first_of_month = today.replace(day=1)

    paid_subq = (
        select(Payment.user_id)
        .where(Payment.status == "confirmed", Payment.period_end >= first_of_month)
        .scalar_subquery()
    )
    debtors_result = await db.execute(
        select(User, StudentProfile)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(
            User.role == "student",
            User.status == "active",
            User.id.not_in(paid_subq),
        )
    )
    debtors = []
    for user, profile in debtors_result.all():
        groups_res = await db.execute(
            select(Group.name)
            .join(StudentGroup, StudentGroup.group_id == Group.id)
            .where(StudentGroup.user_id == user.id)
        )
        group_names = [r[0] for r in groups_res.all()]

        last_pay_res = await db.execute(
            select(Payment.created_at)
            .where(Payment.user_id == user.id, Payment.status == "confirmed")
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        last_pay = last_pay_res.scalar_one_or_none()
        debtors.append({
            "user_id": user.id,
            "full_name": (profile.full_name if profile else None) or user.username,
            "group_names": group_names,
            "last_payment_at": last_pay.isoformat() if last_pay else None,
        })

    avg_res = await db.execute(
        select(func.avg(Payment.amount)).where(Payment.status == "confirmed")
    )
    avg_amount = float(avg_res.scalar_one() or 0)
    debtors_total_estimate = avg_amount * len(debtors)

    return {
        "period_days": days,
        "total_confirmed": confirmed[1],
        "total_pending": pending[1],
        "total_rejected": rejected[1],
        "confirmed_count": confirmed[0],
        "pending_count": pending[0],
        "rejected_count": rejected[0],
        "debtors_count": len(debtors),
        "debtors_total_estimate": debtors_total_estimate,
        "monthly_revenue": monthly_revenue,
        "debtors": debtors,
    }


async def get_attendance_stats(
    db: AsyncSession, days: int = 30, group_id: Optional[int] = None
) -> dict:
    now = datetime.now(tz=timezone.utc)
    period_start = now - timedelta(days=days)

    grp_q = select(Group)
    if group_id:
        grp_q = grp_q.where(Group.id == group_id)
    groups_res = await db.execute(grp_q)
    groups = list(groups_res.scalars().all())

    by_group = []
    by_student: list[dict] = []
    seen_students: set[int] = set()

    for group in groups:
        lesson_ids_res = await db.execute(
            select(Lesson.id).where(
                Lesson.group_id == group.id,
                Lesson.scheduled_at >= period_start,
                Lesson.scheduled_at <= now,
            )
        )
        lesson_ids = [r[0] for r in lesson_ids_res.all()]
        total_lessons = len(lesson_ids)
        if not lesson_ids:
            continue

        student_ids_res = await db.execute(
            select(StudentGroup.user_id).where(StudentGroup.group_id == group.id)
        )
        student_ids = [r[0] for r in student_ids_res.all()]
        student_count = len(student_ids)
        if not student_ids:
            continue

        grp_att_res = await db.execute(
            select(Attendance.status, func.count(Attendance.id))
            .where(
                Attendance.lesson_id.in_(lesson_ids),
                Attendance.student_user_id.in_(student_ids),
            )
            .group_by(Attendance.status)
        )
        att_map = {row[0]: row[1] for row in grp_att_res.all()}
        present_count = att_map.get("present", 0) + att_map.get("late", 0)
        possible_count = total_lessons * student_count
        pct = round(present_count * 100 / possible_count) if possible_count > 0 else 0

        by_group.append({
            "group_id": group.id,
            "group_name": group.name,
            "total_lessons": total_lessons,
            "student_count": student_count,
            "present_count": present_count,
            "possible_count": possible_count,
            "percent": pct,
        })

        for sid in student_ids:
            if sid in seen_students:
                continue
            seen_students.add(sid)

            profile_res = await db.execute(
                select(StudentProfile.full_name).where(StudentProfile.user_id == sid)
            )
            full_name = profile_res.scalar_one_or_none()

            stu_att_res = await db.execute(
                select(Attendance.status, func.count(Attendance.id))
                .where(
                    Attendance.lesson_id.in_(lesson_ids),
                    Attendance.student_user_id == sid,
                )
                .group_by(Attendance.status)
            )
            stu_map = {row[0]: row[1] for row in stu_att_res.all()}
            present = stu_map.get("present", 0)
            late = stu_map.get("late", 0)
            absent = stu_map.get("absent", 0)
            excused = stu_map.get("excused", 0)
            pct_stu = round((present + late) * 100 / total_lessons) if total_lessons > 0 else 0

            by_student.append({
                "user_id": sid,
                "full_name": full_name,
                "group_name": group.name,
                "total": total_lessons,
                "present": present,
                "late": late,
                "absent": absent,
                "excused": excused,
                "percent": pct_stu,
            })

    return {
        "period_days": days,
        "group_id": group_id,
        "by_group": by_group,
        "by_student": by_student,
    }


async def get_performance_stats(
    db: AsyncSession, days: int = 30, group_id: Optional[int] = None
) -> dict:
    now = datetime.now(tz=timezone.utc)
    period_start = now - timedelta(days=days)

    stu_q = (
        select(User.id, StudentProfile.full_name)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(User.role == "student", User.status == "active")
    )
    if group_id:
        stu_q = stu_q.join(
            StudentGroup, StudentGroup.user_id == User.id
        ).where(StudentGroup.group_id == group_id)
    stu_res = await db.execute(stu_q)
    students = list(stu_res.all())

    hw_assigned_res = await db.execute(
        select(func.count(Homework.id)).where(Homework.created_at >= period_start)
    )
    assigned_count = hw_assigned_res.scalar_one() or 0

    hw_submitted_res = await db.execute(
        select(func.count(HomeworkGrade.id))
        .join(Homework, Homework.id == HomeworkGrade.homework_id)
        .where(Homework.created_at >= period_start)
    )
    submitted_count = hw_submitted_res.scalar_one() or 0
    completion_rate = round(submitted_count * 100 / assigned_count) if assigned_count > 0 else 0

    attempts_res = await db.execute(
        select(func.count(QuizAttempt.id)).where(QuizAttempt.started_at >= period_start)
    )
    attempts_count = attempts_res.scalar_one() or 0

    completed_res = await db.execute(
        select(func.count(QuizAttempt.id)).where(
            QuizAttempt.started_at >= period_start,
            QuizAttempt.status == "completed",
        )
    )
    completed_count = completed_res.scalar_one() or 0

    scores_res = await db.execute(
        select(QuizAttempt.score, QuizAttempt.max_score).where(
            QuizAttempt.started_at >= period_start,
            QuizAttempt.status == "completed",
            QuizAttempt.max_score > 0,
        )
    )
    scores = scores_res.all()
    avg_score_pct = (
        round(sum(float(r.score) / float(r.max_score) * 100 for r in scores) / len(scores))
        if scores else 0
    )

    student_ranking = []
    for user_id, full_name in students:
        stu_hw_res = await db.execute(
            select(func.count(Homework.id.distinct())).where(
                Homework.created_at >= period_start,
                or_(
                    Homework.student_user_id == user_id,
                    Homework.group_id.in_(
                        select(StudentGroup.group_id).where(StudentGroup.user_id == user_id)
                    ),
                ),
            )
        )
        stu_assigned = stu_hw_res.scalar_one() or 0

        stu_submitted_res = await db.execute(
            select(func.count(HomeworkGrade.id))
            .join(Homework, Homework.id == HomeworkGrade.homework_id)
            .where(
                HomeworkGrade.student_user_id == user_id,
                Homework.created_at >= period_start,
            )
        )
        stu_submitted = stu_submitted_res.scalar_one() or 0
        hw_completion_pct = round(stu_submitted * 100 / stu_assigned) if stu_assigned > 0 else 0

        stu_scores_res = await db.execute(
            select(QuizAttempt.score, QuizAttempt.max_score).where(
                QuizAttempt.student_user_id == user_id,
                QuizAttempt.started_at >= period_start,
                QuizAttempt.status == "completed",
                QuizAttempt.max_score > 0,
            )
        )
        stu_scores = stu_scores_res.all()
        quiz_avg_pct = (
            round(sum(float(r.score) / float(r.max_score) * 100 for r in stu_scores) / len(stu_scores))
            if stu_scores else 0
        )

        combined_score = round(0.6 * (hw_completion_pct / 10) + 0.4 * (quiz_avg_pct / 10), 1)

        grp_name_res = await db.execute(
            select(Group.name)
            .join(StudentGroup, StudentGroup.group_id == Group.id)
            .where(StudentGroup.user_id == user_id)
            .limit(1)
        )
        group_name = grp_name_res.scalar_one_or_none()

        student_ranking.append({
            "user_id": user_id,
            "full_name": full_name,
            "group_name": group_name,
            "hw_completion_pct": hw_completion_pct,
            "quiz_avg_pct": quiz_avg_pct,
            "combined_score": combined_score,
        })

    student_ranking.sort(key=lambda x: x["combined_score"], reverse=True)

    return {
        "period_days": days,
        "group_id": group_id,
        "homework": {
            "assigned_count": assigned_count,
            "submitted_count": submitted_count,
            "completion_rate": completion_rate,
        },
        "quizzes": {
            "attempts_count": attempts_count,
            "completed_count": completed_count,
            "avg_score_pct": avg_score_pct,
        },
        "student_ranking": student_ranking,
    }
