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

    async def get_group_students(
        self, group_id: int, offset: int = 0, limit: int = 10
    ) -> list[dict]:
        async with self._session.get(
            f"{self.base_url}/groups/{group_id}/students",
            params={"offset": offset, "limit": limit},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()
