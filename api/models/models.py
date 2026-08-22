from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import (
    String, BigInteger, ForeignKey, DateTime, Date, Text, Integer, JSON,
    UniqueConstraint, Time, SmallInteger, Boolean, Numeric, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(2), default="uk", nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher_profile: Mapped[Optional["TeacherProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    agreements: Mapped[list["Agreement"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    parent_name: Mapped[Optional[str]] = mapped_column(String(128))
    parent_phone: Mapped[Optional[str]] = mapped_column(String(20))
    study_start_month: Mapped[Optional[str]] = mapped_column(String(7))
    study_format: Mapped[Optional[str]] = mapped_column(String(16))
    extra_info: Mapped[Optional[str]] = mapped_column(Text)
    notion_link: Mapped[Optional[str]] = mapped_column(String(512))
    english_level: Mapped[Optional[str]] = mapped_column(String(8))

    user: Mapped["User"] = relationship(back_populates="student_profile")


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(256))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    specialization: Mapped[Optional[str]] = mapped_column(String(256))
    experience_years: Mapped[Optional[int]] = mapped_column(Integer)

    user: Mapped["User"] = relationship(back_populates="teacher_profile")


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(16), default="teacher", nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    used_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Agreement(Base):
    __tablename__ = "agreements"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    agreed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    user: Mapped["User"] = relationship(back_populates="agreements")


class AdminActionLog(Base):
    __tablename__ = "admin_actions_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    target_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[Optional[str]] = mapped_column(String(8))
    teacher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student_groups: Mapped[list["StudentGroup"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class StudentGroup(Base):
    __tablename__ = "student_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (UniqueConstraint("user_id", "group_id"),)

    group: Mapped["Group"] = relationship(back_populates="student_groups")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_min: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="schedule",
        cascade="save-update, merge",
        passive_deletes=True,
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=True
    )
    student_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    schedule_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("schedules.id", ondelete="SET NULL")
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration_min: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    zoom_link: Mapped[Optional[str]] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="scheduled", nullable=False)
    reminder_24h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_2h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_30m_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    schedule: Mapped[Optional["Schedule"]] = relationship(back_populates="lessons")


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint("lesson_id", "student_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    student_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lesson: Mapped["Lesson"] = relationship()
    student: Mapped["User"] = relationship(foreign_keys=[student_user_id])


class Homework(Base):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    student_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    grades: Mapped[list["HomeworkGrade"]] = relationship(back_populates="homework", cascade="all, delete-orphan")


class HomeworkGrade(Base):
    __tablename__ = "homework_grades"
    __table_args__ = (UniqueConstraint("homework_id", "student_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id", ondelete="CASCADE"), nullable=False)
    student_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    graded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    grade_text: Mapped[str] = mapped_column(String(512), nullable=False)
    graded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    homework: Mapped["Homework"] = relationship(back_populates="grades")
    student: Mapped["User"] = relationship(foreign_keys=[student_user_id])


class TeacherNote(Base):
    __tablename__ = "teacher_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    student_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped[Optional["User"]] = relationship(foreign_keys=[student_user_id])
    lesson: Mapped[Optional["Lesson"]] = relationship()


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # No FK constraint: polymorphic reference (points to either group_id or user_id based on target_type)
    target_id: Mapped[Optional[int]] = mapped_column()
    message_type: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text)
    file_id: Mapped[Optional[str]] = mapped_column(String(256))
    recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class BotContent(Base):
    __tablename__ = "bot_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    file_id: Mapped[Optional[str]] = mapped_column(String(256))
    file_type: Mapped[Optional[str]] = mapped_column(String(16))  # photo / video / document
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    payment_type: Mapped[str] = mapped_column(String(16), nullable=False)
    months_paid: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="created")
    comment: Mapped[Optional[str]] = mapped_column(Text)
    confirmed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    creator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    time_limit_min: Mapped[Optional[int]] = mapped_column(Integer)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_idx"
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    order_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    file_id: Mapped[Optional[str]] = mapped_column(String(256))

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
    options: Mapped[list["QuizOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class QuizOption(Base):
    __tablename__ = "quiz_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    question: Mapped["QuizQuestion"] = relationship(back_populates="options")


class QuizAssignment(Base):
    __tablename__ = "quiz_assignments"
    __table_args__ = (
        CheckConstraint(
            "(group_id IS NULL) != (student_user_id IS NULL)",
            name="quiz_assignment_exactly_one_target",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    assigned_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    student_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assignment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quiz_assignments.id", ondelete="SET NULL"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    score: Mapped[float] = mapped_column(Numeric(6, 2), default=0, nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(6, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="in_progress", nullable=False)

    answers: Mapped[list["QuizAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    selected_options: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    text_answer: Mapped[Optional[str]] = mapped_column(Text)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    points_earned: Mapped[float] = mapped_column(Numeric(6, 2), default=0, nullable=False)

    attempt: Mapped["QuizAttempt"] = relationship(back_populates="answers")
