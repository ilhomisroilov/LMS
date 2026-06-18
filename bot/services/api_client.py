"""Async HTTP client for the EduCore backend bot API."""
from typing import Any

import aiohttp

from config import settings


class ApiClient:
    def __init__(self) -> None:
        self.base = settings.BOT_API_BASE_URL.rstrip("/")
        self.headers = {"X-Bot-Token": settings.BOT_API_TOKEN}

    async def _request(self, method: str, path: str, **kwargs) -> tuple[int, Any]:
        url = f"{self.base}{path}"
        async with aiohttp.ClientSession(headers=self.headers) as s:
            async with s.request(method, url, **kwargs) as r:
                try:
                    data = await r.json()
                except Exception:
                    data = None
                return r.status, data

    async def link(self, phone: str, telegram_id: int) -> tuple[int, Any]:
        return await self._request("POST", "/bot/link",
                                   json={"phone": phone, "telegram_id": telegram_id})

    async def me(self, telegram_id: int) -> tuple[int, Any]:
        return await self._request("GET", "/bot/me", params={"telegram_id": telegram_id})

    async def set_language(self, telegram_id: int, lang: str) -> tuple[int, Any]:
        return await self._request("POST", "/bot/language",
                                   params={"telegram_id": telegram_id, "lang": lang})

    # student
    async def student_groups(self, tid): return await self._get("/bot/student/groups", tid)
    async def student_attendance(self, tid): return await self._get("/bot/student/attendance", tid)
    async def student_payments(self, tid): return await self._get("/bot/student/payments", tid)
    async def student_lessons(self, tid): return await self._get("/bot/student/lessons", tid)

    # teacher
    async def teacher_groups(self, tid): return await self._get("/bot/teacher/groups", tid)

    async def teacher_group_students(self, group_id: int, tid: int):
        return await self._request("GET", f"/bot/teacher/group/{group_id}/students",
                                   params={"telegram_id": tid})

    async def teacher_mark_attendance(self, tid, group_id, lesson_date, records):
        return await self._request("POST", "/bot/teacher/attendance", json={
            "telegram_id": tid, "group_id": group_id,
            "lesson_date": lesson_date, "records": records,
        })

    # parent
    async def parent_children(self, tid): return await self._get("/bot/parent/children", tid)

    async def parent_child_attendance(self, student_id: int, tid: int):
        return await self._request("GET", f"/bot/parent/child/{student_id}/attendance",
                                   params={"telegram_id": tid})

    async def parent_child_payments(self, student_id: int, tid: int):
        return await self._request("GET", f"/bot/parent/child/{student_id}/payments",
                                   params={"telegram_id": tid})

    async def _get(self, path: str, telegram_id: int):
        return await self._request("GET", path, params={"telegram_id": telegram_id})


api = ApiClient()
