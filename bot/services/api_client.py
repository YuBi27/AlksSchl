from typing import Optional
import aiohttp


class APIClient:
    def __init__(self, base_url: str, secret: str):
        self.base_url = base_url.rstrip("/")
        self._headers = {"X-Bot-Secret": secret, "Content-Type": "application/json"}
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self) -> None:
        self._session = aiohttp.ClientSession(headers=self._headers)

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    async def get_or_create_user(self, telegram_id: int, username: Optional[str]) -> dict:
        async with self._session.post(
            f"{self.base_url}/auth/start",
            json={"telegram_id": telegram_id, "username": username},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def update_language(self, telegram_id: int, language: str) -> dict:
        async with self._session.patch(
            f"{self.base_url}/users/{telegram_id}/language",
            json={"language": language},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def update_status(self, user_id: int, status: str) -> dict:
        async with self._session.patch(
            f"{self.base_url}/users/{user_id}/status",
            json={"status": status},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_user(self, user_id: int) -> dict:
        async with self._session.get(f"{self.base_url}/users/{user_id}") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def validate_invite_code(self, code: str) -> dict:
        async with self._session.get(f"{self.base_url}/invite-codes/{code}") as resp:
            if resp.status == 404:
                return {"valid": False}
            if resp.status == 410:
                return {"valid": False}
            resp.raise_for_status()
            data = await resp.json()
            data["valid"] = True
            return data

    async def use_invite_code(self, code: str, user_id: int) -> dict:
        async with self._session.post(
            f"{self.base_url}/invite-codes/{code}/use",
            json={"user_id": user_id},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_student_profile(self, user_id: int, data: dict) -> dict:
        async with self._session.post(
            f"{self.base_url}/users/{user_id}/student-profile",
            json=data,
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_teacher_profile(self, user_id: int, data: dict) -> dict:
        async with self._session.post(
            f"{self.base_url}/users/{user_id}/teacher-profile",
            json=data,
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def record_agreement(self, user_id: int, telegram_id: int, agreement_type: str) -> dict:
        async with self._session.post(
            f"{self.base_url}/agreements",
            json={"user_id": user_id, "telegram_id": telegram_id, "type": agreement_type},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_pending_applications(self) -> list[dict]:
        async with self._session.get(f"{self.base_url}/users?status=pending") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def log_admin_action(
        self,
        admin_id: int,
        action: str,
        target_user_id: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> None:
        async with self._session.post(
            f"{self.base_url}/admin/log",
            json={
                "admin_id": admin_id,
                "action": action,
                "target_user_id": target_user_id,
                "details": details,
            },
        ) as resp:
            resp.raise_for_status()

    async def get_students(
        self,
        search: str | None = None,
        group_id: int | None = None,
        level: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        params = {"offset": offset, "limit": limit}
        if search:
            params["search"] = search
        if group_id:
            params["group_id"] = group_id
        if level:
            params["level"] = level
        if status:
            params["status"] = status
        async with self._session.get(
            f"{self.base_url}/students", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_student(self, user_id: int) -> dict:
        async with self._session.get(
            f"{self.base_url}/students/{user_id}"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def set_student_level(self, user_id: int, level: str) -> None:
        async with self._session.patch(
            f"{self.base_url}/students/{user_id}/level",
            json={"level": level},
        ) as resp:
            resp.raise_for_status()

    async def set_student_groups(self, user_id: int, group_ids: list[int]) -> None:
        async with self._session.post(
            f"{self.base_url}/students/{user_id}/groups",
            json={"group_ids": group_ids},
        ) as resp:
            resp.raise_for_status()

    async def remove_student_from_group(self, user_id: int, group_id: int) -> None:
        async with self._session.delete(
            f"{self.base_url}/students/{user_id}/groups/{group_id}"
        ) as resp:
            resp.raise_for_status()

    async def delete_student(self, user_id: int) -> None:
        async with self._session.delete(
            f"{self.base_url}/students/{user_id}"
        ) as resp:
            resp.raise_for_status()

    async def import_students(self, rows: list[dict]) -> dict:
        async with self._session.post(
            f"{self.base_url}/students/import", json=rows
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_groups(self) -> list[dict]:
        async with self._session.get(f"{self.base_url}/groups") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_group(self, group_id: int) -> dict:
        async with self._session.get(
            f"{self.base_url}/groups/{group_id}"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_group(self, name: str, level: str | None, description: str | None) -> dict:
        async with self._session.post(
            f"{self.base_url}/groups",
            json={"name": name, "level": level, "description": description},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def update_group(self, group_id: int, **kwargs) -> dict:
        async with self._session.patch(
            f"{self.base_url}/groups/{group_id}", json=kwargs
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def delete_group(self, group_id: int) -> None:
        async with self._session.delete(
            f"{self.base_url}/groups/{group_id}"
        ) as resp:
            resp.raise_for_status()

    async def get_group_students(self, group_id: int) -> list[dict]:
        return await self.get_students(group_id=group_id, status="active")

    # --- Schedules ---

    async def get_schedules(self, group_id: int) -> list[dict]:
        async with self._session.get(
            f"{self.base_url}/schedules", params={"group_id": group_id}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_schedule(
        self,
        group_id: int,
        day_of_week: int,
        start_time: str,
        duration_min: int = 60,
    ) -> dict:
        async with self._session.post(
            f"{self.base_url}/schedules",
            json={"group_id": group_id, "day_of_week": day_of_week,
                  "start_time": start_time, "duration_min": duration_min},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def delete_schedule(self, schedule_id: int) -> None:
        async with self._session.delete(
            f"{self.base_url}/schedules/{schedule_id}"
        ) as resp:
            resp.raise_for_status()

    async def generate_upcoming_lessons(self) -> dict:
        async with self._session.post(
            f"{self.base_url}/schedules/generate-upcoming"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    # --- Lessons ---

    async def get_lessons(
        self,
        group_id: Optional[int] = None,
        from_dt: Optional[str] = None,
        to_dt: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        params = {}
        if group_id is not None:
            params["group_id"] = group_id
        if from_dt is not None:
            params["from_dt"] = from_dt
        if to_dt is not None:
            params["to_dt"] = to_dt
        if status is not None:
            params["status"] = status
        async with self._session.get(
            f"{self.base_url}/lessons", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_lesson(self, lesson_id: int) -> dict:
        async with self._session.get(
            f"{self.base_url}/lessons/{lesson_id}"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_lesson(
        self,
        group_id: int,
        scheduled_at: str,
        duration_min: int = 60,
        zoom_link: Optional[str] = None,
    ) -> dict:
        async with self._session.post(
            f"{self.base_url}/lessons",
            json={"group_id": group_id, "scheduled_at": scheduled_at,
                  "duration_min": duration_min, "zoom_link": zoom_link},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def update_lesson(self, lesson_id: int, **kwargs) -> dict:
        async with self._session.patch(
            f"{self.base_url}/lessons/{lesson_id}", json=kwargs
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def cancel_lesson(self, lesson_id: int) -> None:
        async with self._session.delete(
            f"{self.base_url}/lessons/{lesson_id}"
        ) as resp:
            resp.raise_for_status()

    async def get_due_reminders(self) -> list[dict]:
        async with self._session.get(
            f"{self.base_url}/lessons/due-reminders"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def mark_reminder_sent(self, lesson_id: int, reminder_type: str) -> None:
        """reminder_type: '24h' | '2h' | '30min'"""
        field_map = {
            "24h": "reminder_24h_sent",
            "2h": "reminder_2h_sent",
            "30min": "reminder_30m_sent",
        }
        field = field_map[reminder_type]
        async with self._session.patch(
            f"{self.base_url}/lessons/{lesson_id}/reminders",
            json={field: True},
        ) as resp:
            resp.raise_for_status()

    async def get_users_by_role(self, role: str) -> list[dict]:
        async with self._session.get(
            f"{self.base_url}/users", params={"role": role}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def upsert_attendance(self, lesson_id: int, student_user_id: int, status: str) -> dict:
        async with self._session.post(
            f"{self.base_url}/attendances",
            json={"lesson_id": lesson_id, "student_user_id": student_user_id, "status": status},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_attendances(
        self,
        lesson_id: int | None = None,
        student_user_id: int | None = None,
    ) -> list[dict]:
        params = {}
        if lesson_id is not None:
            params["lesson_id"] = lesson_id
        if student_user_id is not None:
            params["student_user_id"] = student_user_id
        async with self._session.get(f"{self.base_url}/attendances", params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_homeworks(
        self,
        teacher_id: int | None = None,
        group_id: int | None = None,
        student_user_id: int | None = None,
    ) -> list[dict]:
        params = {}
        if teacher_id is not None:
            params["teacher_id"] = teacher_id
        if group_id is not None:
            params["group_id"] = group_id
        if student_user_id is not None:
            params["student_user_id"] = student_user_id
        async with self._session.get(f"{self.base_url}/homeworks", params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_homework(self, data: dict) -> dict:
        async with self._session.post(f"{self.base_url}/homeworks", json=data) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_homework(self, homework_id: int) -> dict:
        async with self._session.get(f"{self.base_url}/homeworks/{homework_id}") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_homework_grades(self, homework_id: int) -> list[dict]:
        async with self._session.get(f"{self.base_url}/homeworks/{homework_id}/grades") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def upsert_grade(self, homework_id: int, data: dict) -> dict:
        async with self._session.post(
            f"{self.base_url}/homeworks/{homework_id}/grades", json=data
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_teacher_notes(
        self,
        student_user_id: int | None = None,
        lesson_id: int | None = None,
    ) -> list[dict]:
        params = {}
        if student_user_id is not None:
            params["student_user_id"] = student_user_id
        if lesson_id is not None:
            params["lesson_id"] = lesson_id
        async with self._session.get(f"{self.base_url}/teacher-notes", params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_teacher_note(self, data: dict) -> dict:
        async with self._session.post(f"{self.base_url}/teacher-notes", json=data) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def delete_teacher_note(self, note_id: int) -> None:
        async with self._session.delete(f"{self.base_url}/teacher-notes/{note_id}") as resp:
            resp.raise_for_status()

    async def get_teacher_profile(self, user_id: int) -> dict:
        async with self._session.get(f"{self.base_url}/users/{user_id}/teacher-profile") as resp:
            resp.raise_for_status()
            return await resp.json()
