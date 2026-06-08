# bot.py
import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db
from user import register_user_handlers
from admin import register_admin_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

bot     = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp      = Dispatcher(bot, storage=storage)

register_admin_handlers(dp)
register_user_handlers(dp)

if __name__ == "__main__":
    init_db()
    logging.info("🎬 Kino bot ishga tushdi!")
    executor.start_polling(dp, skip_updates=True)
