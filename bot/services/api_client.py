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

    async def get_user_student_profile(self, user_id: int) -> dict:
        async with self._session.get(
            f"{self.base_url}/users/{user_id}/student-profile"
        ) as resp:
            if resp.status == 404:
                return {}
            resp.raise_for_status()
            return await resp.json()

    async def generate_invite_code(self, created_by: int, role: str = "teacher") -> dict:
        async with self._session.post(
            f"{self.base_url}/invite-codes",
            json={"created_by": created_by, "role": role},
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

    async def get_groups(self, teacher_id: int | None = None) -> list[dict]:
        params = {}
        if teacher_id is not None:
            params["teacher_id"] = teacher_id
        async with self._session.get(f"{self.base_url}/groups", params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_group(self, group_id: int) -> dict:
        async with self._session.get(
            f"{self.base_url}/groups/{group_id}"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_group(
        self,
        name: str,
        level: str | None,
        description: str | None,
        teacher_id: int | None = None,
    ) -> dict:
        async with self._session.post(
            f"{self.base_url}/groups",
            json={"name": name, "level": level, "description": description, "teacher_id": teacher_id},
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

    async def get_group_students(self, group_id: int, limit: int = 50) -> list[dict]:
        return await self.get_students(group_id=group_id, status="active", limit=limit)

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

    async def update_schedule(self, schedule_id: int, **kwargs) -> dict:
        async with self._session.patch(
            f"{self.base_url}/schedules/{schedule_id}",
            json=kwargs,
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
        student_user_id: Optional[int] = None,
        from_dt: Optional[str] = None,
        to_dt: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        params = {}
        if group_id is not None:
            params["group_id"] = group_id
        if student_user_id is not None:
            params["student_user_id"] = student_user_id
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
        scheduled_at: str,
        duration_min: int = 60,
        zoom_link: Optional[str] = None,
        group_id: Optional[int] = None,
        student_user_id: Optional[int] = None,
    ) -> dict:
        body: dict = {"scheduled_at": scheduled_at, "duration_min": duration_min}
        if group_id is not None:
            body["group_id"] = group_id
        if student_user_id is not None:
            body["student_user_id"] = student_user_id
        if zoom_link is not None:
            body["zoom_link"] = zoom_link
        async with self._session.post(
            f"{self.base_url}/lessons", json=body,
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
            if resp.status == 404:
                return {}
            resp.raise_for_status()
            return await resp.json()

    # --- Broadcasts ---

    async def save_broadcast(
        self,
        target_type: str,
        message_type: str,
        recipient_count: int,
        sender_id: Optional[int] = None,
        target_id: Optional[int] = None,
        text: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> dict:
        async with self._session.post(
            f"{self.base_url}/broadcasts",
            json={
                "sender_id": sender_id,
                "target_type": target_type,
                "target_id": target_id,
                "message_type": message_type,
                "text": text,
                "file_id": file_id,
                "recipient_count": recipient_count,
            },
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_broadcasts(
        self,
        sender_id: Optional[int] = None,
        limit: int = 20,
    ) -> list[dict]:
        params: dict = {"limit": limit}
        if sender_id is not None:
            params["sender_id"] = sender_id
        async with self._session.get(
            f"{self.base_url}/broadcasts", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    # --- Content ---

    async def get_content(self, key: str) -> dict:
        async with self._session.get(f"{self.base_url}/bot-content/{key}") as resp:
            if resp.status == 404:
                return {"key": key, "value": "Інформація ще не додана."}
            resp.raise_for_status()
            return await resp.json()

    async def set_content(
        self, key: str, value: str, updated_by: Optional[int] = None
    ) -> dict:
        async with self._session.put(
            f"{self.base_url}/bot-content/{key}",
            json={"value": value, "updated_by": updated_by},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_teacher_profiles(self) -> list[dict]:
        async with self._session.get(f"{self.base_url}/teacher-profiles") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_users(
        self,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        params: dict = {}
        if role:
            params["role"] = role
        if status:
            params["status"] = status
        async with self._session.get(
            f"{self.base_url}/users", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    # --- Statistics ---

    async def get_stats_overview(self) -> dict:
        async with self._session.get(f"{self.base_url}/stats/overview") as resp:
            resp.raise_for_status()
            return await resp.json()

    # --- Payments ---

    async def save_payment(
        self,
        user_id: int,
        amount: str,
        period_start: str,
        period_end: str,
        payment_type: str,
        months_paid: int = 1,
        confirmed_by: Optional[int] = None,
        comment: Optional[str] = None,
        status: str = "created",
    ) -> dict:
        async with self._session.post(
            f"{self.base_url}/payments",
            json={
                "user_id": user_id,
                "amount": amount,
                "period_start": period_start,
                "period_end": period_end,
                "payment_type": payment_type,
                "months_paid": months_paid,
                "confirmed_by": confirmed_by,
                "comment": comment,
                "status": status,
            },
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_payments(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        params: dict = {"limit": limit}
        if user_id is not None:
            params["user_id"] = user_id
        if status is not None:
            params["status"] = status
        async with self._session.get(
            f"{self.base_url}/payments", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def patch_payment_fields(self, payment_id: int, **kwargs) -> dict:
        async with self._session.patch(
            f"{self.base_url}/payments/{payment_id}/fields",
            json={k: v for k, v in kwargs.items() if v is not None},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def update_payment_status(
        self, payment_id: int, status: str, months_paid: Optional[int] = None
    ) -> dict:
        body: dict = {"status": status}
        if months_paid is not None:
            body["months_paid"] = months_paid
        async with self._session.patch(
            f"{self.base_url}/payments/{payment_id}/status",
            json=body,
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def delete_payment(self, payment_id: int) -> bool:
        async with self._session.delete(
            f"{self.base_url}/payments/{payment_id}"
        ) as resp:
            return resp.status == 204

    async def get_debtors(self) -> list[dict]:
        async with self._session.get(f"{self.base_url}/payments/debtors") as resp:
            resp.raise_for_status()
            return await resp.json()

    # ---- Quizzes ----

    async def create_quiz(
        self,
        title: str,
        creator_id: Optional[int] = None,
        description: Optional[str] = None,
        time_limit_min: Optional[int] = None,
        shuffle_questions: bool = False,
    ) -> dict:
        body: dict = {"title": title, "shuffle_questions": shuffle_questions}
        if creator_id is not None:
            body["creator_id"] = creator_id
        if description is not None:
            body["description"] = description
        if time_limit_min is not None:
            body["time_limit_min"] = time_limit_min
        async with self._session.post(f"{self.base_url}/quizzes", json=body) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_quiz(self, quiz_id: int) -> dict:
        async with self._session.get(f"{self.base_url}/quizzes/{quiz_id}") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def list_quizzes(self, creator_id: Optional[int] = None) -> list[dict]:
        params = {}
        if creator_id is not None:
            params["creator_id"] = creator_id
        async with self._session.get(f"{self.base_url}/quizzes", params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def delete_quiz(self, quiz_id: int) -> bool:
        async with self._session.delete(f"{self.base_url}/quizzes/{quiz_id}") as resp:
            return resp.status == 204

    async def add_quiz_question(
        self,
        quiz_id: int,
        order_idx: int,
        question_type: str,
        text: str,
        options: list[dict],
        file_id: Optional[str] = None,
    ) -> dict:
        body: dict = {
            "order_idx": order_idx,
            "question_type": question_type,
            "text": text,
            "options": options,
        }
        if file_id:
            body["file_id"] = file_id
        async with self._session.post(
            f"{self.base_url}/quizzes/{quiz_id}/questions", json=body
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def delete_quiz_question(self, question_id: int) -> bool:
        async with self._session.delete(
            f"{self.base_url}/quizzes/questions/{question_id}"
        ) as resp:
            return resp.status == 204

    async def create_quiz_assignment(
        self,
        quiz_id: int,
        assigned_by: Optional[int],
        group_id: Optional[int] = None,
        student_user_id: Optional[int] = None,
        deadline: Optional[str] = None,
    ) -> dict:
        body: dict = {"quiz_id": quiz_id, "assigned_by": assigned_by}
        if group_id is not None:
            body["group_id"] = group_id
        if student_user_id is not None:
            body["student_user_id"] = student_user_id
        if deadline is not None:
            body["deadline"] = deadline
        async with self._session.post(
            f"{self.base_url}/quiz-assignments", json=body
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def list_quiz_assignments(
        self,
        quiz_id: Optional[int] = None,
        student_user_id: Optional[int] = None,
        group_id: Optional[int] = None,
    ) -> list[dict]:
        params: dict = {}
        if quiz_id is not None:
            params["quiz_id"] = quiz_id
        if student_user_id is not None:
            params["student_user_id"] = student_user_id
        if group_id is not None:
            params["group_id"] = group_id
        async with self._session.get(
            f"{self.base_url}/quiz-assignments", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def list_quiz_assignments_for_student(self, user_id: int) -> list[dict]:
        async with self._session.get(
            f"{self.base_url}/quiz-assignments/for-student/{user_id}"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def delete_quiz_assignment(self, assignment_id: int) -> bool:
        async with self._session.delete(
            f"{self.base_url}/quiz-assignments/{assignment_id}"
        ) as resp:
            return resp.status == 204

    async def start_quiz_attempt(
        self,
        quiz_id: int,
        student_user_id: int,
        assignment_id: Optional[int] = None,
    ) -> dict:
        body: dict = {"quiz_id": quiz_id, "student_user_id": student_user_id}
        if assignment_id is not None:
            body["assignment_id"] = assignment_id
        async with self._session.post(
            f"{self.base_url}/quiz-attempts", json=body
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_quiz_attempt(self, attempt_id: int) -> dict:
        async with self._session.get(
            f"{self.base_url}/quiz-attempts/{attempt_id}"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def list_quiz_attempts(
        self,
        quiz_id: Optional[int] = None,
        student_user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        params: dict = {}
        if quiz_id is not None:
            params["quiz_id"] = quiz_id
        if student_user_id is not None:
            params["student_user_id"] = student_user_id
        if status is not None:
            params["status"] = status
        async with self._session.get(
            f"{self.base_url}/quiz-attempts", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def save_quiz_answer(
        self,
        attempt_id: int,
        question_id: int,
        selected_options: list[int],
        text_answer: Optional[str] = None,
    ) -> dict:
        body: dict = {"question_id": question_id, "selected_options": selected_options}
        if text_answer is not None:
            body["text_answer"] = text_answer
        async with self._session.post(
            f"{self.base_url}/quiz-attempts/{attempt_id}/answer", json=body
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def finish_quiz_attempt(self, attempt_id: int) -> dict:
        async with self._session.post(
            f"{self.base_url}/quiz-attempts/{attempt_id}/finish"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def list_quiz_results(self, quiz_id: int) -> list[dict]:
        async with self._session.get(
            f"{self.base_url}/quizzes/{quiz_id}/results"
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    # ---- Analytics ----

    async def get_financial_stats(self, days: int = 30) -> dict:
        async with self._session.get(
            f"{self.base_url}/stats/financial", params={"days": days}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_attendance_stats(
        self, days: int = 30, group_id: Optional[int] = None
    ) -> dict:
        params: dict = {"days": days}
        if group_id is not None:
            params["group_id"] = group_id
        async with self._session.get(
            f"{self.base_url}/stats/attendance", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_performance_stats(
        self, days: int = 30, group_id: Optional[int] = None
    ) -> dict:
        params: dict = {"days": days}
        if group_id is not None:
            params["group_id"] = group_id
        async with self._session.get(
            f"{self.base_url}/stats/performance", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()
