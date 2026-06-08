# config.py
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8671506465:AAEczqpZYdRF-pzPvivG7567UaFZCehRYq8")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "5874554565").split(",")))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@kinolar_to")
DB_NAME = os.getenv("DB_NAME", "movies.db")
PER_PAGE = 8
