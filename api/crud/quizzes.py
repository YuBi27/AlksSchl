from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import (
    Quiz, QuizQuestion, QuizOption, QuizAssignment,
    QuizAttempt, QuizAnswer,
)


async def create_quiz(db: AsyncSession, **kwargs) -> Quiz:
    quiz = Quiz(**kwargs)
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return quiz


async def get_quiz(db: AsyncSession, quiz_id: int) -> Optional[Quiz]:
    result = await db.execute(
        select(Quiz)
        .where(Quiz.id == quiz_id)
        .options(selectinload(Quiz.questions).selectinload(QuizQuestion.options))
    )
    return result.scalar_one_or_none()


async def list_quizzes(db: AsyncSession, creator_id: Optional[int] = None) -> list[Quiz]:
    q = select(Quiz).order_by(Quiz.created_at.desc())
    if creator_id is not None:
        q = q.where(Quiz.creator_id == creator_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_quiz(db: AsyncSession, quiz_id: int, **kwargs) -> Optional[Quiz]:
    quiz = await get_quiz(db, quiz_id)
    if not quiz:
        return None
    for key, value in kwargs.items():
        setattr(quiz, key, value)
    await db.commit()
    await db.refresh(quiz)
    return quiz


async def delete_quiz(db: AsyncSession, quiz_id: int) -> bool:
    quiz = await get_quiz(db, quiz_id)
    if not quiz:
        return False
    await db.delete(quiz)
    await db.commit()
    return True


async def add_question(
    db: AsyncSession,
    quiz_id: int,
    order_idx: int,
    question_type: str,
    text: str,
    options: list[dict],
    file_id: Optional[str] = None,
) -> QuizQuestion:
    q = QuizQuestion(
        quiz_id=quiz_id,
        order_idx=order_idx,
        question_type=question_type,
        text=text,
        file_id=file_id,
    )
    db.add(q)
    await db.flush()
    for opt in options:
        db.add(QuizOption(question_id=q.id, text=opt["text"], is_correct=opt.get("is_correct", False)))
    await db.commit()
    result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.id == q.id)
        .options(selectinload(QuizQuestion.options))
    )
    return result.scalar_one()


async def delete_question(db: AsyncSession, question_id: int) -> bool:
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        return False
    await db.delete(q)
    await db.commit()
    return True


async def create_assignment(db: AsyncSession, **kwargs) -> QuizAssignment:
    a = QuizAssignment(**kwargs)
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


async def list_assignments(
    db: AsyncSession,
    quiz_id: Optional[int] = None,
    student_user_id: Optional[int] = None,
    group_id: Optional[int] = None,
) -> list[QuizAssignment]:
    q = select(QuizAssignment)
    if quiz_id is not None:
        q = q.where(QuizAssignment.quiz_id == quiz_id)
    if student_user_id is not None:
        q = q.where(QuizAssignment.student_user_id == student_user_id)
    if group_id is not None:
        q = q.where(QuizAssignment.group_id == group_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_assignments_for_student(
    db: AsyncSession, student_user_id: int
) -> list[QuizAssignment]:
    from api.models.models import StudentGroup
    groups_result = await db.execute(
        select(StudentGroup.group_id).where(StudentGroup.user_id == student_user_id)
    )
    group_ids = [r[0] for r in groups_result.all()]
    conditions = [QuizAssignment.student_user_id == student_user_id]
    if group_ids:
        conditions.append(QuizAssignment.group_id.in_(group_ids))
    result = await db.execute(
        select(QuizAssignment).where(or_(*conditions))
    )
    return list(result.scalars().all())


async def delete_assignment(db: AsyncSession, assignment_id: int) -> bool:
    result = await db.execute(select(QuizAssignment).where(QuizAssignment.id == assignment_id))
    a = result.scalar_one_or_none()
    if not a:
        return False
    await db.delete(a)
    await db.commit()
    return True


async def start_attempt(
    db: AsyncSession,
    quiz_id: int,
    student_user_id: int,
    assignment_id: Optional[int] = None,
) -> QuizAttempt:
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_user_id=student_user_id,
        assignment_id=assignment_id,
        status="in_progress",
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return attempt


async def get_attempt(db: AsyncSession, attempt_id: int) -> Optional[QuizAttempt]:
    result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.id == attempt_id)
        .options(selectinload(QuizAttempt.answers))
    )
    return result.scalar_one_or_none()


async def list_attempts(
    db: AsyncSession,
    quiz_id: Optional[int] = None,
    student_user_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[QuizAttempt]:
    q = select(QuizAttempt)
    if quiz_id is not None:
        q = q.where(QuizAttempt.quiz_id == quiz_id)
    if student_user_id is not None:
        q = q.where(QuizAttempt.student_user_id == student_user_id)
    if status is not None:
        q = q.where(QuizAttempt.status == status)
    result = await db.execute(q)
    return list(result.scalars().all())


async def save_answer(
    db: AsyncSession,
    attempt_id: int,
    question_id: int,
    selected_options: list[int],
    text_answer: Optional[str] = None,
) -> QuizAnswer:
    result = await db.execute(
        select(QuizAnswer).where(
            QuizAnswer.attempt_id == attempt_id,
            QuizAnswer.question_id == question_id,
        )
    )
    answer = result.scalar_one_or_none()
    if answer:
        answer.selected_options = selected_options
        answer.text_answer = text_answer
    else:
        answer = QuizAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_options=selected_options,
            text_answer=text_answer,
        )
        db.add(answer)
    await db.commit()
    await db.refresh(answer)
    return answer


async def finish_attempt(db: AsyncSession, attempt_id: int) -> Optional[QuizAttempt]:
    attempt = await get_attempt(db, attempt_id)
    if not attempt or attempt.status == "completed":
        return attempt

    quiz = await get_quiz(db, attempt.quiz_id)
    answer_map = {a.question_id: a for a in attempt.answers}

    score = 0.0
    max_score = 0.0
    for question in quiz.questions:
        if question.question_type == "text":
            continue
        max_score += 1.0
        answer = answer_map.get(question.id)
        if not answer:
            continue
        correct_ids = {opt.id for opt in question.options if opt.is_correct}
        selected_ids = set(answer.selected_options or [])
        is_correct = selected_ids == correct_ids
        answer.is_correct = is_correct
        answer.points_earned = 1.0 if is_correct else 0.0
        if is_correct:
            score += 1.0

    attempt.score = score
    attempt.max_score = max_score
    attempt.status = "completed"
    attempt.finished_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(attempt)
    return attempt


async def list_results(
    db: AsyncSession,
    quiz_id: Optional[int] = None,
    student_user_id: Optional[int] = None,
) -> list[dict]:
    from api.models.models import User, StudentProfile
    q = (
        select(QuizAttempt, User, StudentProfile)
        .join(User, User.id == QuizAttempt.student_user_id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(QuizAttempt.status == "completed")
    )
    if quiz_id is not None:
        q = q.where(QuizAttempt.quiz_id == quiz_id)
    if student_user_id is not None:
        q = q.where(QuizAttempt.student_user_id == student_user_id)
    result = await db.execute(q)
    return [
        {
            "id": attempt.id,
            "quiz_id": attempt.quiz_id,
            "student_user_id": attempt.student_user_id,
            "student_name": profile.full_name if profile else None,
            "score": float(attempt.score),
            "max_score": float(attempt.max_score),
            "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
            "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
            "status": attempt.status,
        }
        for attempt, user, profile in result.all()
    ]
