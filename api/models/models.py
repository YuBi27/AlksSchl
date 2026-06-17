from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    String, BigInteger, ForeignKey, DateTime, Date, Text, Integer, JSON
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
