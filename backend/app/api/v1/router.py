"""Aggregate all v1 endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    attendance, auth, bot, courses, dashboard, groups, logs, me, payments, students, teachers,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(students.router)
api_router.include_router(teachers.router)
api_router.include_router(groups.router)
api_router.include_router(courses.router)
api_router.include_router(attendance.router)
api_router.include_router(payments.router)
api_router.include_router(dashboard.router)
api_router.include_router(logs.router)
api_router.include_router(bot.router)
