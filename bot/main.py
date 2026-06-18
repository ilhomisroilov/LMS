"""EduCore Telegram bot entrypoint (aiogram 3)."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers import parent, start, student, teacher

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    # auth/start first, then role-specific routers
    dp.include_router(start.router)
    dp.include_router(student.router)
    dp.include_router(teacher.router)
    dp.include_router(parent.router)
    logging.info("EduCore bot starting (polling)...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
