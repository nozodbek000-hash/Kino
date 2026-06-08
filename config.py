# config.py
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8671506465:AAEczqpZYdRF-pzPvivG7567UaFZCehRYq8")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "5874554565").split(",")))

# === O'ZGARTIRISH KERAK ===
CHANNEL_ID = None   # Majburiy kanalni o'chirish uchun None qo'ydik
# CHANNEL_ID = os.getenv("CHANNEL_ID", "@kinolar_to")  # eski kodni izohga oling

DB_NAME = os.getenv("DB_NAME", "movies.db")
PER_PAGE = 8
STORAGE_CHANNEL = os.getenv("STORAGE_CHANNEL", "@kinolar_to")