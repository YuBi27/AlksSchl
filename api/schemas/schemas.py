from datetime import datetime, date, time
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator, Field


class AuthStartRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    telegram_id: int
    username: Optional[str] = None
    language: str
    role: str
    status: str
    created_at: Optional[datetime] = None


class UserLanguageUpdate(BaseModel):
    language: str


class UserStatusUpdate(BaseModel):
    status: str


class StudentProfileCreate(BaseModel):
    full_name: str
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    study_start_month: Optional[str] = None
    study_format: Optional[str] = None
    extra_info: Optional[str] = None
    notion_link: Optional[str] = None


class StudentProfileOut(StudentProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int


class TeacherProfileCreate(BaseModel):
    full_name: str
    photo_file_id: Optional[str] = None
    bio: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None


class TeacherProfileOut(TeacherProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int


class InviteCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    role: str
    expires_at: Optional[datetime] = None
    used_by: Optional[int] = None
    used_at: Optional[datetime] = None


class InviteCodeUseRequest(BaseModel):
    user_id: int


class AgreementCreate(BaseModel):
    user_id: int
    telegram_id: int
    type: str


class AgreementOut(AgreementCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    agreed_at: datetime


class AdminLogCreate(BaseModel):
    admin_id: int
    action: str
    target_user_id: Optional[int] = None
    details: Optional[dict] = None


class GroupCreate(BaseModel):
    name: str
    level: Optional[str] = None
    description: Optional[str] = None
    teacher_id: Optional[int] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    description: Optional[str] = None


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    level: Optional[str] = None
    teacher_id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    student_count: int = 0


class StudentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    telegram_id: int
    username: Optional[str] = None
    status: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    english_level: Optional[str] = None
    group_names: list[str] = []


class StudentLevelUpdate(BaseModel):
    level: Literal["novice", "A1", "A2", "B1", "B2", "C1", "C2"]


class StudentGroupsUpdate(BaseModel):
    group_ids: list[int]


class ImportRow(BaseModel):
    full_name: str
    phone: str
    level: Optional[str] = None
    group_name: Optional[str] = None


class ImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[str] = []


class ScheduleCreate(BaseModel):
    group_id: int
    day_of_week: int = Field(ge=0, le=6)  # 0=Mon, 6=Sun
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")   # "HH:MM" format, interpreted as Europe/Kyiv
    duration_min: int = Field(default=60, gt=0)


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: int
    day_of_week: int
    start_time: str
    duration_min: int
    is_active: bool
    created_at: Optional[datetime] = None

    @field_validator("start_time", mode="before")
    @classmethod
    def format_start_time(cls, v):
        if isinstance(v, time):
            return v.strftime("%H:%M")
        return v


class LessonCreate(BaseModel):
    group_id: Optional[int] = None
    student_user_id: Optional[int] = None
    scheduled_at: datetime   # UTC-aware ISO string
    duration_min: int = 60
    zoom_link: Optional[str] = None

    @field_validator("scheduled_at")
    @classmethod
    def must_be_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware (UTC)")
        return v

    @model_validator(mode="after")
    def exactly_one_target(self) -> "LessonCreate":
        if (self.group_id is None) == (self.student_user_id is None):
            raise ValueError("Exactly one of group_id or student_user_id must be set")
        return self


class LessonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: Optional[int] = None
    student_user_id: Optional[int] = None
    schedule_id: Optional[int] = None
    scheduled_at: datetime
    duration_min: int
    zoom_link: Optional[str] = None
    status: str
    reminder_24h_sent: bool = False
    reminder_2h_sent: bool = False
    reminder_30m_sent: bool = False
    created_at: Optional[datetime] = None


class LessonUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    duration_min: Optional[int] = Field(default=None, gt=0)
    zoom_link: Optional[str] = Field(default=None, max_length=512)
    status: Optional[Literal["scheduled", "completed", "cancelled"]] = None


class ReminderUpdate(BaseModel):
    reminder_24h_sent: Optional[bool] = None
    reminder_2h_sent: Optional[bool] = None
    reminder_30m_sent: Optional[bool] = None


# --- Attendance ---

class AttendanceUpsert(BaseModel):
    lesson_id: int
    student_user_id: int
    status: Literal["present", "late", "absent", "excused"]


class AttendanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lesson_id: int
    student_user_id: int
    status: str
    created_at: Optional[datetime] = None


# --- Homework ---

class HomeworkCreate(BaseModel):
    teacher_id: int
    group_id: Optional[int] = None
    student_user_id: Optional[int] = None
    title: str = Field(max_length=256)
    description: str
    due_at: datetime

    @field_validator("due_at")
    @classmethod
    def must_be_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("due_at must be timezone-aware (UTC)")
        return v

    @model_validator(mode="after")
    def exactly_one_target(self) -> "HomeworkCreate":
        if (self.group_id is None) == (self.student_user_id is None):
            raise ValueError("Exactly one of group_id or student_user_id must be set")
        return self


class HomeworkUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=256)
    description: Optional[str] = None
    due_at: Optional[datetime] = None


class HomeworkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None
    student_user_id: Optional[int] = None
    title: str
    description: str
    due_at: datetime
    created_at: Optional[datetime] = None


# --- HomeworkGrade ---

class HomeworkGradeCreate(BaseModel):
    student_user_id: int
    graded_by: Optional[int] = None
    grade_text: str = Field(max_length=512)


class HomeworkGradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    homework_id: int
    student_user_id: int
    graded_by: Optional[int] = None
    grade_text: str
    graded_at: Optional[datetime] = None


# --- TeacherNote ---

class TeacherNoteCreate(BaseModel):
    teacher_id: Optional[int] = None
    student_user_id: Optional[int] = None
    lesson_id: Optional[int] = None
    text: str

    @model_validator(mode="after")
    def at_least_one_target(self) -> "TeacherNoteCreate":
        if self.student_user_id is None and self.lesson_id is None:
            raise ValueError("At least one of student_user_id or lesson_id must be set")
        return self


class TeacherNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    teacher_id: Optional[int] = None
    student_user_id: Optional[int] = None
    lesson_id: Optional[int] = None
    text: str
    created_at: Optional[datetime] = None


class BroadcastCreate(BaseModel):
    sender_id: Optional[int] = None
    target_type: str
    target_id: Optional[int] = None
    message_type: str
    text: Optional[str] = None
    file_id: Optional[str] = None
    recipient_count: int = 0


class BroadcastRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender_id: Optional[int] = None
    target_type: str
    target_id: Optional[int] = None
    message_type: str
    text: Optional[str] = None
    file_id: Optional[str] = None
    recipient_count: int
    sent_at: datetime


class BotContentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: str
    updated_at: datetime


class BotContentUpdate(BaseModel):
    value: str
    updated_by: Optional[int] = None


class PaymentCreate(BaseModel):
    user_id: int
    amount: float
    period_start: date
    period_end: date
    payment_type: str  # "monthly" | "one_time"
    comment: Optional[str] = None
    confirmed_by: Optional[int] = None


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int] = None
    amount: float
    period_start: date
    period_end: date
    payment_type: str
    comment: Optional[str] = None
    confirmed_by: Optional[int] = None
    created_at: datetime
