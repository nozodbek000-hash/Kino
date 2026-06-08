# handlers/user.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.bot import Bot
from config import PER_PAGE, CHANNEL_ID
from database import (
    save_user, get_user_lang, set_user_lang,
    search_movies, get_movies_by_category, count_by_category,
    get_movie, get_new_movies, count_movies, get_category,
)
from keyboards import (
    main_menu, lang_kb, categories_kb,
    movies_list_kb, movie_detail_kb, subscribe_kb,
)
from utils import movie_text

class SearchState(StatesGroup):
    waiting = State()

async def is_subscribed(user_id: int) -> bool:
    from aiogram import Bot
    bot = Bot.get_current()
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ("left", "kicked")
    except Exception:
        return True

# ── /start ────────────────────────────────────────────────
async def cmd_start(message: types.Message):
    user = message.from_user
    save_user(user.id, user.username, user.full_name)
    lang = get_user_lang(user.id)

    args = message.get_args()
    if args and args.isdigit():
        if not await is_subscribed(user.id):
            await message.answer(
                "⚠️ Botdan foydalanish uchun kanalga obuna bo'ling!" if lang == "uz" else "⚠️ Подпишитесь на канал!",
                reply_markup=subscribe_kb(CHANNEL_ID)
            )
            return
        await send_movie_by_id(message, int(args), lang)
        return

    txt = (
        f"👋 Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
        "🎬 Kino qidirish uchun tugmalardan foydalaning."
        if lang == "uz" else
        f"👋 Добро пожаловать, <b>{user.first_name}</b>!\n\n"
        "🎬 Используйте кнопки для поиска фильмов."
    )
    await message.answer(txt, parse_mode="HTML", reply_markup=main_menu(lang))

# ── Til ───────────────────────────────────────────────────
async def show_lang(message: types.Message):
    await message.answer("🌐 Tilni tanlang / Выберите язык:", reply_markup=lang_kb())

async def set_lang(cb: types.CallbackQuery):
    lang = cb.data.split("_")[1]
    set_user_lang(cb.from_user.id, lang)
    txt = "✅ Til o'zgartirildi!" if lang == "uz" else "✅ Язык изменён!"
    await cb.message.answer(txt, reply_markup=main_menu(lang))
    await cb.answer()

# ── Obuna callback ────────────────────────────────────────
async def check_sub_cb(cb: types.CallbackQuery):
    if await is_subscribed(cb.from_user.id):
        lang = get_user_lang(cb.from_user.id)
        await cb.message.answer(
            "✅ Obuna tasdiqlandi!" if lang == "uz" else "✅ Подписка подтверждена!",
            reply_markup=main_menu(lang)
        )
    else:
        lang = get_user_lang(cb.from_user.id)
        await cb.answer(
            "❌ Hali obuna bo'lmadingiz!" if lang == "uz" else "❌ Вы ещё не подписались!",
            show_alert=True
        )

# ── Kino qidirish ─────────────────────────────────────────
async def search_start(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        lang = get_user_lang(message.from_user.id)
        await message.answer(
            "⚠️ Avval kanalga obuna bo'ling!" if lang == "uz" else "⚠️ Сначала подпишитесь!",
            reply_markup=subscribe_kb(CHANNEL_ID)
        )
        return
    lang = get_user_lang(message.from_user.id)
    await message.answer("🔍 Kino nomini kiriting:" if lang == "uz" else "🔍 Введите название фильма:")
    await SearchState.waiting.set()

async def search_process(message: types.Message, state: FSMContext):
    lang = get_user_lang(message.from_user.id)
    query = message.text.strip()
    movies = search_movies(query)
    await state.finish()

    if not movies:
        await message.answer(
            "❌ Kino topilmadi." if lang == "uz" else "❌ Фильм не найден.",
            reply_markup=main_menu(lang)
        )
        return

    header = f"🔍 <b>{len(movies)}</b> ta natija:" if lang == "uz" else f"🔍 Найдено <b>{len(movies)}</b>:"
    page_movies = movies[:PER_PAGE]
    kb = movies_list_kb(page_movies, 0, len(movies), PER_PAGE, "srch", lang)
    await message.answer(header, parse_mode="HTML", reply_markup=kb)

# ── Kategoriyalar ─────────────────────────────────────────
async def show_categories(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        lang = get_user_lang(message.from_user.id)
        await message.answer(
            "⚠️ Avval kanalga obuna bo'ling!" if lang == "uz" else "⚠️ Сначала подпишитесь!",
            reply_markup=subscribe_kb(CHANNEL_ID)
        )
        return
    lang = get_user_lang(message.from_user.id)
    await message.answer(
        "📂 Kategoriyani tanlang:" if lang == "uz" else "📂 Выберите категорию:",
        reply_markup=categories_kb(lang)
    )

async def cat_movies_cb(cb: types.CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    _, cat_id_str, page_str = cb.data.split("_")
    cat_id = int(cat_id_str)
    page   = int(page_str)
    offset = page * PER_PAGE

    total  = count_by_category(cat_id)
    movies = get_movies_by_category(cat_id, limit=PER_PAGE, offset=offset)

    if not movies:
        await cb.answer(
            "❌ Bu kategoriyada kino yo'q." if lang == "uz" else "❌ В этой категории нет фильмов.",
            show_alert=True
        )
        return

    cat = get_category(cat_id)
    cat_name = cat["name_uz"] if lang == "uz" else cat["name_ru"]
    header = f"📂 <b>{cat_name}</b> — {total} ta" if lang == "uz" else f"📂 <b>{cat_name}</b> — {total} фильмов"
    kb = movies_list_kb(movies, page, total, PER_PAGE, f"cat_{cat_id}", lang)

    try:
        await cb.message.edit_text(header, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await cb.message.answer(header, parse_mode="HTML", reply_markup=kb)
    await cb.answer()

# ── Yangi kinolar ─────────────────────────────────────────
async def new_movies(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        lang = get_user_lang(message.from_user.id)
        await message.answer(
            "⚠️ Avval kanalga obuna bo'ling!" if lang == "uz" else "⚠️ Сначала подпишитесь!",
            reply_markup=subscribe_kb(CHANNEL_ID)
        )
        return
    lang   = get_user_lang(message.from_user.id)
    movies = get_new_movies(10)
    if not movies:
        await message.answer("❌ Hozircha kino yo'q." if lang == "uz" else "❌ Пока нет фильмов.")
        return
    header = "🆕 <b>Yangi kinolar:</b>" if lang == "uz" else "🆕 <b>Новые фильмы:</b>"
    kb = movies_list_kb(movies, 0, len(movies), PER_PAGE, "new", lang)
    await message.answer(header, parse_mode="HTML", reply_markup=kb)

# ── Kino detail ───────────────────────────────────────────
async def movie_cb(cb: types.CallbackQuery):
    lang     = get_user_lang(cb.from_user.id)
    movie_id = int(cb.data.split("_")[1])
    movie    = get_movie(movie_id)
    if not movie:
        await cb.answer("❌ Kino topilmadi!", show_alert=True)
        return
    await cb.message.answer(
        movie_text(movie, lang),
        parse_mode="HTML",
        reply_markup=movie_detail_kb(movie_id, lang)
    )
    await cb.answer()

async def send_movie_by_id(message: types.Message, movie_id: int, lang: str):
    movie = get_movie(movie_id)
    if not movie:
        await message.answer("❌ Kino topilmadi!" if lang == "uz" else "❌ Фильм не найден!")
        return
    await message.answer(
        movie_text(movie, lang),
        parse_mode="HTML",
        reply_markup=movie_detail_kb(movie_id, lang)
    )

# ── Yuklab olish ──────────────────────────────────────────
async def download_cb(cb: types.CallbackQuery):
    if not await is_subscribed(cb.from_user.id):
        lang = get_user_lang(cb.from_user.id)
        await cb.answer(
            "⚠️ Avval kanalga obuna bo'ling!" if lang == "uz" else "⚠️ Сначала подпишитесь!",
            show_alert=True
        )
        return

    lang     = get_user_lang(cb.from_user.id)
    movie_id = int(cb.data.split("_")[1])
    movie    = get_movie(movie_id)
    if not movie:
        await cb.answer("❌ Xato!", show_alert=True)
        return

    name    = movie["name_uz"] if lang == "uz" else (movie["name_ru"] or movie["name_uz"])
    caption = f"🎬 <b>{name}</b>"

    await cb.answer("⏳ Yuklanmoqda..." if lang == "uz" else "⏳ Загружается...")

    bot = Bot.get_current()
    try:
        await bot.send_video(cb.from_user.id, movie["file_id"], caption=caption, parse_mode="HTML")
    except Exception:
        try:
            await bot.send_document(cb.from_user.id, movie["file_id"], caption=caption, parse_mode="HTML")
        except Exception as e:
            await cb.message.answer(f"❌ Xatolik: {e}" if lang == "uz" else f"❌ Ошибка: {e}")

# ── Orqaga ────────────────────────────────────────────────
async def back_main_cb(cb: types.CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    await cb.message.answer(
        "🏠 Bosh sahifa" if lang == "uz" else "🏠 Главная",
        reply_markup=main_menu(lang)
    )
    await cb.answer()

async def noop_cb(cb: types.CallbackQuery):
    await cb.answer()

# ── Register ──────────────────────────────────────────────
def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start,      commands=["start"])
    dp.register_message_handler(show_lang,       lambda m: m.text in ["🌐 Til", "🌐 Язык"])
    dp.register_message_handler(search_start,    lambda m: m.text in ["🎬 Kino qidirish", "🎬 Поиск фильма"])
    dp.register_message_handler(show_categories, lambda m: m.text in ["📂 Kategoriyalar", "📂 Категории"])
    dp.register_message_handler(new_movies,      lambda m: m.text in ["🆕 Yangi kinolar", "🆕 Новые фильмы"])
    dp.register_message_handler(search_process,  state=SearchState.waiting)

    dp.register_callback_query_handler(set_lang,      lambda c: c.data.startswith("setlang_"))
    dp.register_callback_query_handler(check_sub_cb,  lambda c: c.data == "check_sub")
    dp.register_callback_query_handler(cat_movies_cb, lambda c: c.data.startswith("cat_"))
    dp.register_callback_query_handler(movie_cb,      lambda c: c.data.startswith("movie_"))
    dp.register_callback_query_handler(download_cb,   lambda c: c.data.startswith("dl_"))
    dp.register_callback_query_handler(back_main_cb,  lambda c: c.data == "back_main")
    dp.register_callback_query_handler(noop_cb,       lambda c: c.data == "noop")
