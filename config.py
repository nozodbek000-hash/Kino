import os

BOT_TOKEN = os.getenv("8671506465:AAEczqpZYdRF-pzPvivG7567UaFZCehRYq8")

ADMIN_IDS = list(map(int, os.getenv("5874554565", "").split(","))) if os.getenv("5874554565") else []

CHANNEL_ID = os.getenv("@kinolar_to")
STORAGE_CHANNEL = os.getenv("STORAGE_CHANNEL")

DB_NAME = os.getenv("DB_NAME", "movies.db")
PER_PAGE = 8