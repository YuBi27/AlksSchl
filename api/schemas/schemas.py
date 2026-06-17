from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


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
    level: str


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
