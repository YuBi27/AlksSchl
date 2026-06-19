from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.schemas.schemas import (
    QuizCreate, QuizUpdate, QuizRead,
    QuizQuestionCreate, QuizQuestionRead,
    QuizAssignmentCreate, QuizAssignmentRead,
    QuizAttemptRead, QuizAnswerCreate, QuizAnswerRead,
)
from api.crud.quizzes import (
    create_quiz, get_quiz, list_quizzes, update_quiz, delete_quiz,
    add_question, delete_question,
    create_assignment, list_assignments, list_assignments_for_student, delete_assignment,
    start_attempt, get_attempt, list_attempts, save_answer, finish_attempt, list_results,
)

router = APIRouter(prefix="/quizzes", tags=["quizzes"])
attempts_router = APIRouter(prefix="/quiz-attempts", tags=["quiz-attempts"])
assignments_router = APIRouter(prefix="/quiz-assignments", tags=["quiz-assignments"])


# --- Quizzes ---

@router.post("", response_model=QuizRead, status_code=201)
async def create(body: QuizCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    quiz = await create_quiz(db, **body.model_dump())
    return await get_quiz(db, quiz.id)


@router.get("", response_model=list[QuizRead])
async def list_all(db: Annotated[AsyncSession, Depends(get_db)], creator_id: Optional[int] = None):
    quizzes = await list_quizzes(db, creator_id=creator_id)
    result = []
    for quiz in quizzes:
        full = await get_quiz(db, quiz.id)
        result.append(full)
    return result


@router.get("/{quiz_id}", response_model=QuizRead)
async def get_one(quiz_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    quiz = await get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.patch("/{quiz_id}", response_model=QuizRead)
async def update(quiz_id: int, body: QuizUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    quiz = await update_quiz(db, quiz_id, **body.model_dump(exclude_none=True))
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.delete("/{quiz_id}", status_code=204)
async def delete(quiz_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    deleted = await delete_quiz(db, quiz_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Quiz not found")


@router.post("/{quiz_id}/questions", response_model=QuizQuestionRead, status_code=201)
async def add_q(
    quiz_id: int,
    body: QuizQuestionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    quiz = await get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return await add_question(
        db,
        quiz_id=quiz_id,
        order_idx=body.order_idx,
        question_type=body.question_type,
        text=body.text,
        options=[o.model_dump() for o in body.options],
        file_id=body.file_id,
    )


@router.delete("/questions/{question_id}", status_code=204)
async def delete_q(question_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    deleted = await delete_question(db, question_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Question not found")


@router.get("/{quiz_id}/results")
async def get_results(quiz_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    return await list_results(db, quiz_id=quiz_id)


# --- Assignments ---

@assignments_router.post("", response_model=QuizAssignmentRead, status_code=201)
async def create_assign(body: QuizAssignmentCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    return await create_assignment(db, **body.model_dump())


@assignments_router.get("", response_model=list[QuizAssignmentRead])
async def list_assign(
    db: Annotated[AsyncSession, Depends(get_db)],
    quiz_id: Optional[int] = None,
    student_user_id: Optional[int] = None,
    group_id: Optional[int] = None,
):
    return await list_assignments(db, quiz_id=quiz_id, student_user_id=student_user_id, group_id=group_id)


@assignments_router.get("/for-student/{user_id}", response_model=list[QuizAssignmentRead])
async def list_assign_for_student(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    return await list_assignments_for_student(db, student_user_id=user_id)


@assignments_router.delete("/{assignment_id}", status_code=204)
async def delete_assign(assignment_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    deleted = await delete_assignment(db, assignment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Assignment not found")


# --- Attempts ---

@attempts_router.post("", response_model=QuizAttemptRead, status_code=201)
async def start(body: dict, db: Annotated[AsyncSession, Depends(get_db)]):
    attempt = await start_attempt(
        db,
        quiz_id=body["quiz_id"],
        student_user_id=body["student_user_id"],
        assignment_id=body.get("assignment_id"),
    )
    return await get_attempt(db, attempt.id)


@attempts_router.get("", response_model=list[QuizAttemptRead])
async def list_all_attempts(
    db: Annotated[AsyncSession, Depends(get_db)],
    quiz_id: Optional[int] = None,
    student_user_id: Optional[int] = None,
    status: Optional[str] = None,
):
    return await list_attempts(db, quiz_id=quiz_id, student_user_id=student_user_id, status=status)


@attempts_router.get("/{attempt_id}", response_model=QuizAttemptRead)
async def get_one_attempt(attempt_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    attempt = await get_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt


@attempts_router.post("/{attempt_id}/answer", response_model=QuizAnswerRead)
async def answer(
    attempt_id: int,
    body: QuizAnswerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await save_answer(
        db,
        attempt_id=attempt_id,
        question_id=body.question_id,
        selected_options=body.selected_options,
        text_answer=body.text_answer,
    )


@attempts_router.post("/{attempt_id}/finish", response_model=QuizAttemptRead)
async def finish(attempt_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    attempt = await finish_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt
