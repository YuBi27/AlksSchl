from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import (
    String, BigInteger, ForeignKey, DateTime, Date, Text, Integer, JSON,
    UniqueConstraint, Time, SmallInteger, Boolean
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
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
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
