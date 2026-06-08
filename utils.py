# utils.py
from aiogram import Bot
from aiogram.types import ChatMember
from config import CHANNEL_ID

async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """Foydalanuvchi kanalga obuna bo'lganmi tekshiradi."""
    try:
        member: ChatMember = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ("left", "kicked")
    except Exception:
        return True  # Kanal topilmasa, bloklamaymiz

def movie_text(movie, lang: str = "uz") -> str:
    """Kino haqida chiroyli matn."""
    name = movie["name_uz"] if lang == "uz" else (movie["name_ru"] or movie["name_uz"])
    cat  = movie["cat_uz"]  if lang == "uz" else (movie["cat_ru"]  or movie["cat_uz"] or "—")
    desc = movie["description_uz"] if lang == "uz" else (movie["description_ru"] or movie["description_uz"] or "")
    year = movie["year"] or "—"

    if lang == "uz":
        text = (
            f"🎬 <b>{name}</b>\n"
            f"📂 Janr: {cat}\n"
            f"📅 Yil: {year}\n"
        )
        if desc:
            text += f"\n📝 {desc}\n"
        text += f"\n🆔 Kino ID: <code>{movie['id']}</code>"
    else:
        text = (
            f"🎬 <b>{name}</b>\n"
            f"📂 Жанр: {cat}\n"
            f"📅 Год: {year}\n"
        )
        if desc:
            text += f"\n📝 {desc}\n"
        text += f"\n🆔 ID фильма: <code>{movie['id']}</code>"
    return text
