import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_IDS
import database as db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ========== STATES ==========

class AddMovie(StatesGroup):
    code = State()
    title = State()
    link = State()
    description = State()

class DeleteMovie(StatesGroup):
    code = State()

class SearchMovie(StatesGroup):
    query = State()


# ========== HELPERS ==========

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def subscribe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])


def main_keyboard(is_admin_user=False):
    buttons = [
        [InlineKeyboardButton(text="🔍 Kino qidirish", callback_data="search")],
        [InlineKeyboardButton(text="🎬 Kod orqali olish", callback_data="by_code")],
    ]
    if is_admin_user:
        buttons.append([InlineKeyboardButton(text="⚙️ Admin panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="add_movie")],
        [InlineKeyboardButton(text="❌ Kino o'chirish", callback_data="del_movie")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")]
    ])


def back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")]
    ])


def movie_text(movie: dict) -> str:
    text = f"🎬 <b>{movie['title']}</b>\n"
    text += f"🔑 Kod: <code>{movie['code']}</code>\n"
    if movie.get("description"):
        text += f"📝 {movie['description']}\n"
    text += f"\n🔗 <a href='{movie['link']}'>Kinoni ko'rish</a>"
    return text


# ========== START ==========

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    subscribed = await check_subscription(user_id)

    if not subscribed:
        await message.answer(
            "👋 Xush kelibsiz!\n\n"
            "🎬 Kinolardan foydalanish uchun avval kanalimizga obuna bo'ling:",
            reply_markup=subscribe_keyboard()
        )
        return

    await message.answer(
        f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n"
        "🎬 Kino botga xush kelibsiz!\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=main_keyboard(is_admin(user_id)),
        parse_mode="HTML"
    )


# ========== SUBSCRIPTION CHECK ==========

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    subscribed = await check_subscription(user_id)

    if not subscribed:
        await callback.answer("❌ Siz hali obuna bo'lmagansiz!", show_alert=True)
        return

    await callback.message.edit_text(
        f"✅ Rahmat! Obuna tasdiqlandi.\n\n"
        f"🎬 Kino botga xush kelibsiz, <b>{callback.from_user.first_name}</b>!",
        reply_markup=main_keyboard(is_admin(user_id)),
        parse_mode="HTML"
    )


# ========== BACK ==========

@dp.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    await callback.message.edit_text(
        "🎬 Asosiy menyu:",
        reply_markup=main_keyboard(is_admin(user_id))
    )


# ========== SEARCH BY NAME ==========

@dp.callback_query(F.data == "search")
async def search_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchMovie.query)
    await callback.message.edit_text(
        "🔍 Kino nomini kiriting:",
        reply_markup=back_keyboard()
    )


@dp.message(SearchMovie.query)
async def search_result(message: Message, state: FSMContext):
    await state.clear()
    query = message.text.strip()
    results = db.search_movie_by_name(query)

    if not results:
        await message.answer(
            f"❌ '<b>{query}</b>' bo'yicha kino topilmadi.\n\n"
            "Boshqa nom bilan qidiring yoki kodni kiriting:",
            reply_markup=main_keyboard(is_admin(message.from_user.id)),
            parse_mode="HTML"
        )
        return

    for movie in results[:5]:  # Max 5 ta natija
        await message.answer(
            movie_text(movie),
            parse_mode="HTML",
            disable_web_page_preview=False
        )

    if len(results) > 5:
        await message.answer(f"... va yana {len(results)-5} ta natija bor. Aniqroq nom kiriting.")

    await message.answer("🎬 Asosiy menyu:", reply_markup=main_keyboard(is_admin(message.from_user.id)))


# ========== SEARCH BY CODE ==========

@dp.callback_query(F.data == "by_code")
async def by_code_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchMovie.query)
    await callback.message.edit_text(
        "🔑 Kino kodini kiriting (masalan: <code>K001</code>):",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )


@dp.message(F.text)
async def handle_text(message: Message, state: FSMContext):
    # Agar state yo'q bo'lsa, kodni tekshiramiz
    current_state = await state.get_state()
    if current_state is not None:
        return

    text = message.text.strip()
    movie = db.get_movie_by_code(text)

    if movie:
        subscribed = await check_subscription(message.from_user.id)
        if not subscribed:
            await message.answer(
                "⚠️ Kinoni ko'rish uchun kanalga obuna bo'ling:",
                reply_markup=subscribe_keyboard()
            )
            return
        await message.answer(
            movie_text(movie),
            parse_mode="HTML",
            disable_web_page_preview=False
        )
    else:
        await message.answer(
            "❓ Kino topilmadi. /start orqali menuga qayting."
        )


# ========== ADMIN PANEL ==========

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await callback.message.edit_text("⚙️ Admin panel:", reply_markup=admin_keyboard())


@dp.callback_query(F.data == "stats")
async def stats_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    count = db.get_stats()
    await callback.answer(f"📊 Jami kinolar: {count} ta", show_alert=True)


# -------- ADD MOVIE --------

@dp.callback_query(F.data == "add_movie")
async def add_movie_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await state.set_state(AddMovie.code)
    await callback.message.edit_text(
        "➕ Yangi kino qo'shish\n\n"
        "1️⃣ Kino kodini kiriting (masalan: <code>K001</code>):",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )


@dp.message(AddMovie.code)
async def add_movie_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    existing = db.get_movie_by_code(code)
    if existing:
        await message.answer(f"⚠️ '{code}' kodi allaqachon mavjud! Boshqa kod kiriting:")
        return
    await state.update_data(code=code)
    await state.set_state(AddMovie.title)
    await message.answer("2️⃣ Kino nomini kiriting:")


@dp.message(AddMovie.title)
async def add_movie_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovie.link)
    await message.answer("3️⃣ Kino linkini kiriting (Telegram post linki yoki boshqa):")


@dp.message(AddMovie.link)
async def add_movie_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text.strip())
    await state.set_state(AddMovie.description)
    await message.answer("4️⃣ Qisqacha tavsif kiriting (yoki /skip yuboring):")


@dp.message(AddMovie.description)
async def add_movie_desc(message: Message, state: FSMContext):
    desc = "" if message.text.strip() == "/skip" else message.text.strip()
    data = await state.get_data()
    await state.clear()

    db.add_movie(data["code"], data["title"], data["link"], desc)

    await message.answer(
        f"✅ Kino muvaffaqiyatli qo'shildi!\n\n"
        f"🔑 Kod: <code>{data['code']}</code>\n"
        f"🎬 Nomi: {data['title']}",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# -------- DELETE MOVIE --------

@dp.callback_query(F.data == "del_movie")
async def del_movie_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await state.set_state(DeleteMovie.code)
    await callback.message.edit_text(
        "❌ O'chirish uchun kino kodini kiriting:",
        reply_markup=back_keyboard()
    )


@dp.message(DeleteMovie.code)
async def del_movie_confirm(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.clear()
    result = db.delete_movie(code)

    if result:
        await message.answer(
            f"✅ <code>{code}</code> kodi o'chirildi!",
            parse_mode="HTML",
            reply_markup=admin_keyboard()
        )
    else:
        await message.answer(
            f"❌ <code>{code}</code> kodi topilmadi!",
            parse_mode="HTML",
            reply_markup=admin_keyboard()
        )


# ========== RUN ==========

async def main():
    print("🤖 Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
