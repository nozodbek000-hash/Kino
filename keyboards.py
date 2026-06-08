# keyboards.py
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from database import get_categories

# ── Reply menus ───────────────────────────────────────────
def main_menu(lang: str = "uz") -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "uz":
        kb.row(KeyboardButton("🎬 Kino qidirish"), KeyboardButton("📂 Kategoriyalar"))
        kb.row(KeyboardButton("🆕 Yangi kinolar"), KeyboardButton("🌐 Til"))
    else:
        kb.row(KeyboardButton("🎬 Поиск фильма"), KeyboardButton("📂 Категории"))
        kb.row(KeyboardButton("🆕 Новые фильмы"), KeyboardButton("🌐 Язык"))
    return kb

def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("➕ Kino qo'shish"), KeyboardButton("🗑 Kino o'chirish"))
    kb.row(KeyboardButton("📊 Statistika"),    KeyboardButton("🔙 Bosh sahifa"))
    return kb

def cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("❌ Bekor qilish"))
    return kb

# ── Inline keyboards ──────────────────────────────────────
def lang_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="setlang_uz"),
        InlineKeyboardButton("🇷🇺 Русский",   callback_data="setlang_ru"),
    )
    return kb

def categories_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    cats = get_categories()
    kb = InlineKeyboardMarkup(row_width=2)
    btns = [
        InlineKeyboardButton(
            f"🎭 {cat['name_uz'] if lang == 'uz' else cat['name_ru']}",
            callback_data=f"cat_{cat['id']}_0"
        )
        for cat in cats
    ]
    kb.add(*btns)
    return kb

def movies_list_kb(
    movies: list,
    page: int,
    total: int,
    per_page: int,
    prefix: str,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for m in movies:
        name = m["name_uz"] if lang == "uz" else (m["name_ru"] or m["name_uz"])
        year = f" ({m['year']})" if m["year"] else ""
        kb.add(InlineKeyboardButton(f"🎬 {name}{year}", callback_data=f"movie_{m['id']}"))
    # Pagination row
    total_pages = max(1, (total + per_page - 1) // per_page)
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}_{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if (page + 1) * per_page < total:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}_{page + 1}"))
    if len(nav) > 1:
        kb.row(*nav)
    return kb

def movie_detail_kb(movie_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    label = "⬇️ Yuklab olish" if lang == "uz" else "⬇️ Скачать"
    kb.add(InlineKeyboardButton(label, callback_data=f"dl_{movie_id}"))
    back  = "🔙 Orqaga"      if lang == "uz" else "🔙 Назад"
    kb.add(InlineKeyboardButton(back,  callback_data="back_main"))
    return kb

def confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Bekor",      callback_data="confirm_no"),
    )
    return kb

def subscribe_kb(channel: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📢 Kanalga obuna bo'lish",
                                url=f"https://t.me/{channel.lstrip('@')}"))
    kb.add(InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub"))
    return kb
