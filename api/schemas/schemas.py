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
    months_paid: int = 1
    comment: Optional[str] = None
    confirmed_by: Optional[int] = None
    status: str = "created"


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int] = None
    amount: float
    period_start: date
    period_end: date
    payment_type: str
    months_paid: int = 1
    status: str = "created"
    comment: Optional[str] = None
    confirmed_by: Optional[int] = None
    created_at: datetime


class PaymentStatusUpdate(BaseModel):
    status: str  # "pending_confirmation" | "confirmed" | "rejected"
    months_paid: Optional[int] = None


class PaymentUpdate(BaseModel):
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    comment: Optional[str] = None


# --- Quiz ---

class QuizOptionCreate(BaseModel):
    text: str = Field(max_length=512)
    is_correct: bool = False


class QuizOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_id: int
    text: str
    is_correct: bool


class QuizQuestionCreate(BaseModel):
    order_idx: int
    question_type: Literal["single", "multi", "text"]
    text: str
    file_id: Optional[str] = None
    options: list[QuizOptionCreate] = []


class QuizQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    quiz_id: int
    order_idx: int
    question_type: str
    text: str
    file_id: Optional[str] = None
    options: list[QuizOptionRead] = []


class QuizCreate(BaseModel):
    title: str = Field(max_length=256)
    description: Optional[str] = None
    creator_id: Optional[int] = None
    time_limit_min: Optional[int] = None
    shuffle_questions: bool = False


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=256)
    description: Optional[str] = None
    time_limit_min: Optional[int] = None
    shuffle_questions: Optional[bool] = None
    is_active: Optional[bool] = None


class QuizRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str] = None
    creator_id: Optional[int] = None
    time_limit_min: Optional[int] = None
    shuffle_questions: bool = False
    is_active: bool = True
    created_at: datetime
    questions: list[QuizQuestionRead] = []


class QuizAssignmentCreate(BaseModel):
    quiz_id: int
    assigned_by: Optional[int] = None
    group_id: Optional[int] = None
    student_user_id: Optional[int] = None
    deadline: Optional[datetime] = None

    @model_validator(mode="after")
    def exactly_one_target(self) -> "QuizAssignmentCreate":
        if (self.group_id is None) == (self.student_user_id is None):
            raise ValueError("Exactly one of group_id or student_user_id must be set")
        return self


class QuizAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    quiz_id: int
    assigned_by: Optional[int] = None
    group_id: Optional[int] = None
    student_user_id: Optional[int] = None
    deadline: Optional[datetime] = None
    created_at: datetime


class QuizAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    attempt_id: int
    question_id: int
    selected_options: list[int] = []
    text_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    points_earned: float = 0.0


class QuizAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    quiz_id: int
    student_user_id: int
    assignment_id: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    score: float = 0.0
    max_score: float = 0.0
    status: str
    answers: list[QuizAnswerRead] = []


class QuizAnswerCreate(BaseModel):
    question_id: int
    selected_options: list[int] = []
    text_answer: Optional[str] = None


# --- Analytics ---

class MonthlyRevenue(BaseModel):
    month: str
    revenue: float
    count: int


class DebtorInfo(BaseModel):
    user_id: int
    full_name: Optional[str] = None
    group_names: list[str] = []
    last_payment_at: Optional[str] = None


class FinancialStats(BaseModel):
    period_days: int
    total_confirmed: float = 0.0
    total_pending: float = 0.0
    total_rejected: float = 0.0
    confirmed_count: int = 0
    pending_count: int = 0
    rejected_count: int = 0
    debtors_count: int = 0
    debtors_total_estimate: float = 0.0
    monthly_revenue: list[MonthlyRevenue] = []
    debtors: list[DebtorInfo] = []


class GroupAttendanceStat(BaseModel):
    group_id: int
    group_name: str
    total_lessons: int
    student_count: int
    present_count: int
    possible_count: int
    percent: int


class StudentAttendanceStat(BaseModel):
    user_id: int
    full_name: Optional[str] = None
    group_name: Optional[str] = None
    total: int
    present: int
    late: int
    absent: int
    excused: int
    percent: int


class AttendanceStats(BaseModel):
    period_days: int
    group_id: Optional[int] = None
    by_group: list[GroupAttendanceStat] = []
    by_student: list[StudentAttendanceStat] = []


class HomeworkOverall(BaseModel):
    assigned_count: int = 0
    submitted_count: int = 0
    completion_rate: int = 0


class QuizOverall(BaseModel):
    attempts_count: int = 0
    completed_count: int = 0
    avg_score_pct: int = 0


class StudentRanking(BaseModel):
    user_id: int
    full_name: Optional[str] = None
    group_name: Optional[str] = None
    hw_completion_pct: int = 0
    quiz_avg_pct: int = 0
    combined_score: float = 0.0


class PerformanceStats(BaseModel):
    period_days: int
    group_id: Optional[int] = None
    homework: HomeworkOverall = HomeworkOverall()
    quizzes: QuizOverall = QuizOverall()
    student_ranking: list[StudentRanking] = []
