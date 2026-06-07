import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_IDS
import database as db

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class AddMovie(StatesGroup):
    code = State()
    title = State()
    link = State()
    description = State()

class DeleteMovie(StatesGroup):
    code = State()


async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_kb(admin=False):
    buttons = [
        [InlineKeyboardButton(text="🔍 Kino qidirish", callback_data="search")],
        [InlineKeyboardButton(text="🎬 Kod orqali olish", callback_data="by_code")],
    ]
    if admin:
        buttons.append([InlineKeyboardButton(text="⚙️ Admin panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="add_movie")],
        [InlineKeyboardButton(text="❌ Kino o'chirish", callback_data="del_movie")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back")],
    ])

def sub_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")],
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back")]
    ])

def movie_text(m):
    t = f"🎬 <b>{m['title']}</b>\n🔑 Kod: <code>{m['code']}</code>\n"
    if m.get("description"):
        t += f"📝 {m['description']}\n"
    t += f"\n🔗 <a href='{m['link']}'>Kinoni ko'rish</a>"
    return t


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    if not await check_subscription(uid):
        await message.answer("👋 Xush kelibsiz!\n\nKinolardan foydalanish uchun kanalga obuna bo'ling:", reply_markup=sub_kb())
        return
    await message.answer(f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n🎬 Kino botga xush kelibsiz!", reply_markup=main_kb(is_admin(uid)), parse_mode="HTML")


@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    if not await check_subscription(call.from_user.id):
        await call.answer("❌ Hali obuna bo'lmagansiz!", show_alert=True)
        return
    await call.message.edit_text(f"✅ Obuna tasdiqlandi!\n\n👋 Xush kelibsiz, <b>{call.from_user.first_name}</b>!", reply_markup=main_kb(is_admin(call.from_user.id)), parse_mode="HTML")


@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🎬 Asosiy menyu:", reply_markup=main_kb(is_admin(call.from_user.id)))


@dp.callback_query(F.data == "search")
async def search_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovie.code)
    await state.update_data(mode="search")
    await call.message.edit_text("🔍 Kino nomini kiriting:", reply_markup=back_kb())


@dp.callback_query(F.data == "by_code")
async def by_code_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovie.code)
    await state.update_data(mode="code")
    await call.message.edit_text("🔑 Kino kodini kiriting (masalan: K001):", reply_markup=back_kb())


@dp.callback_query(F.data == "admin")
async def admin_panel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await call.message.edit_text("⚙️ Admin panel:", reply_markup=admin_kb())


@dp.callback_query(F.data == "stats")
async def stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await call.answer(f"📊 Jami kinolar: {db.get_stats()} ta", show_alert=True)


@dp.callback_query(F.data == "add_movie")
async def add_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await state.set_state(AddMovie.code)
    await state.update_data(mode="add")
    await call.message.edit_text("➕ Kino qo'shish\n\n1️⃣ Kino kodini kiriting (masalan: K001):", reply_markup=back_kb())


@dp.callback_query(F.data == "del_movie")
async def del_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await state.set_state(DeleteMovie.code)
    await call.message.edit_text("❌ O'chirish uchun kino kodini kiriting:", reply_markup=back_kb())


@dp.message(DeleteMovie.code)
async def del_movie(message: Message, state: FSMContext):
    await state.clear()
    code = message.text.strip().upper()
    if db.delete_movie(code):
        await message.answer(f"✅ <code>{code}</code> o'chirildi!", parse_mode="HTML", reply_markup=admin_kb())
    else:
        await message.answer(f"❌ <code>{code}</code> topilmadi!", parse_mode="HTML", reply_markup=admin_kb())


@dp.message(AddMovie.code)
async def handle_code(message: Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("mode")
    text = message.text.strip()

    if mode == "add":
        code = text.upper()
        if db.get_movie_by_code(code):
            await message.answer(f"⚠️ '{code}' kodi allaqachon mavjud! Boshqa kod kiriting:")
            return
        await state.update_data(code=code)
        await state.set_state(AddMovie.title)
        await message.answer("2️⃣ Kino nomini kiriting:")

    elif mode == "code":
        movie = db.get_movie_by_code(text)
        await state.clear()
        if movie:
            await message.answer(movie_text(movie), parse_mode="HTML", reply_markup=main_kb(is_admin(message.from_user.id)))
        else:
            await message.answer("❌ Bunday kodli kino topilmadi!", reply_markup=main_kb(is_admin(message.from_user.id)))

    elif mode == "search":
        results = db.search_movie_by_name(text)
        await state.clear()
        if not results:
            await message.answer(f"❌ '{text}' bo'yicha kino topilmadi!", reply_markup=main_kb(is_admin(message.from_user.id)))
            return
        for m in results[:5]:
            await message.answer(movie_text(m), parse_mode="HTML")
        await message.answer("🎬 Asosiy menyu:", reply_markup=main_kb(is_admin(message.from_user.id)))


@dp.message(AddMovie.title)
async def handle_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovie.link)
    await message.answer("3️⃣ Kino linkini kiriting:")


@dp.message(AddMovie.link)
async def handle_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text.strip())
    await state.set_state(AddMovie.description)
    await message.answer("4️⃣ Tavsif kiriting (yoki /skip):")


@dp.message(AddMovie.description)
async def handle_desc(message: Message, state: FSMContext):
    desc = "" if message.text.strip() == "/skip" else message.text.strip()
    data = await state.get_data()
    await state.clear()
    db.add_movie(data["code"], data["title"], data["link"], desc)
    await message.answer(
        f"✅ Kino qo'shildi!\n\n🔑 Kod: <code>{data['code']}</code>\n🎬 {data['title']}",
        parse_mode="HTML", reply_markup=admin_kb()
    )


@dp.message(F.text)
async def handle_any(message: Message):
    movie = db.get_movie_by_code(message.text.strip())
    if movie:
        if not await check_subscription(message.from_user.id):
            await message.answer("⚠️ Kino olish uchun kanalga obuna bo'ling:", reply_markup=sub_kb())
            return
        await message.answer(movie_text(movie), parse_mode="HTML")
    else:
        await message.answer("❓ /start bosing")


async def main():
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
