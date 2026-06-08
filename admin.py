# admin.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.bot import Bot
from config import ADMIN_IDS, STORAGE_CHANNEL
from database import (
    add_movie, delete_movie, get_movie,
    count_movies, count_users, get_categories,
)
from keyboards import admin_menu, cancel_kb, confirm_kb, main_menu

def is_admin(uid):
    return uid in ADMIN_IDS

class AddMovie(StatesGroup):
    name_uz  = State()
    name_ru  = State()
    category = State()
    year     = State()
    desc_uz  = State()
    desc_ru  = State()
    file     = State()
    confirm  = State()

class DeleteMovie(StatesGroup):
    movie_id = State()

async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Ruxsat yo'q!")
        return
    await message.answer("👨‍💼 <b>Admin panel</b>", parse_mode="HTML", reply_markup=admin_menu())

async def add_start(message: types.Message):
    if not is_admin(message.from_user.id): return
    await message.answer("📝 Kino nomini kiriting (O'zbekcha):", reply_markup=cancel_kb())
    await AddMovie.name_uz.set()

async def step_name_uz(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
    await state.update_data(name_uz=message.text.strip())
    await message.answer("📝 Kino nomini kiriting (Ruscha, yoki — o'tkazib yuborish):")
    await AddMovie.name_ru.set()

async def step_name_ru(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
    val = "" if message.text.strip() == "—" else message.text.strip()
    await state.update_data(name_ru=val)
    cats = get_categories()
    cat_list = "\n".join(f"  <code>{c['id']}</code> — {c['name_uz']}" for c in cats)
    await message.answer(f"📂 Kategoriya ID sini yuboring:\n\n{cat_list}", parse_mode="HTML")
    await AddMovie.category.set()

async def step_category(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
    if not message.text.strip().isdigit():
        return await message.answer("❌ Faqat raqam kiriting!")
    await state.update_data(category_id=int(message.text.strip()))
    await message.answer("📅 Yilni kiriting (masalan: 2024), yoki — o'tkazib yuborish:")
    await AddMovie.year.set()

async def step_year(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
    txt = message.text.strip()
    year = None
    if txt != "—":
        if not txt.isdigit():
            return await message.answer("❌ Yilni to'g'ri kiriting!")
        year = int(txt)
    await state.update_data(year=year)
    await message.answer("📝 Tavsif kiriting (O'zbekcha), yoki — o'tkazib yuborish:")
    await AddMovie.desc_uz.set()

async def step_desc_uz(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
    val = "" if message.text.strip() == "—" else message.text.strip()
    await state.update_data(desc_uz=val)
    await message.answer("📝 Tavsif kiriting (Ruscha), yoki — o'tkazib yuborish:")
    await AddMovie.desc_ru.set()

async def step_desc_ru(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
    val = "" if message.text.strip() == "—" else message.text.strip()
    await state.update_data(desc_ru=val)
    await message.answer("🎬 Kino faylini yuboring (video yoki document):")
    await AddMovie.file.set()

async def step_file(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())

    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id

    if not file_id:
        return await message.answer("❌ Iltimos, video yoki fayl yuboring!")

    # Kanalga forward qilish va message_id saqlash
    bot = Bot.get_current()
    try:
        sent = await bot.forward_message(
            chat_id=STORAGE_CHANNEL,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        message_id = sent.message_id
    except Exception as e:
        await message.answer(f"❌ Kanalga yuborishda xato: {e}\nBot kanalga admin qilib qo'shilganmi?")
        return

    await state.update_data(file_id=file_id, message_id=message_id)
    data = await state.get_data()

    txt = (
        f"✅ <b>Ma'lumotlarni tekshiring:</b>\n\n"
        f"🎬 Nomi (UZ): <b>{data['name_uz']}</b>\n"
        f"🎬 Nomi (RU): <b>{data.get('name_ru') or '—'}</b>\n"
        f"📂 Kategoriya ID: <b>{data['category_id']}</b>\n"
        f"📅 Yil: <b>{data.get('year') or '—'}</b>\n"
        f"📝 Tavsif (UZ): {data.get('desc_uz') or '—'}\n"
        f"📝 Tavsif (RU): {data.get('desc_ru') or '—'}\n"
        f"📦 Kanal message ID: <code>{message_id}</code>"
    )
    await message.answer(txt, parse_mode="HTML", reply_markup=confirm_kb())
    await AddMovie.confirm.set()

async def step_confirm(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "confirm_no":
        await state.finish()
        await cb.message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        await cb.answer()
        return

    data = await state.get_data()
    mid = add_movie(
        name_uz=data["name_uz"],
        name_ru=data.get("name_ru", ""),
        category_id=data["category_id"],
        file_id=data["file_id"],
        message_id=data["message_id"],
        year=data.get("year"),
        desc_uz=data.get("desc_uz", ""),
        desc_ru=data.get("desc_ru", ""),
        admin_id=cb.from_user.id,
    )
    await state.finish()
    await cb.message.answer(
        f"✅ Kino muvaffaqiyatli qo'shildi!\n🆔 ID: <code>{mid}</code>",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )
    await cb.answer()

async def del_start(message: types.Message):
    if not is_admin(message.from_user.id): return
    await message.answer("🗑 O'chirmoqchi bo'lgan kino <b>ID</b> sini kiriting:", parse_mode="HTML", reply_markup=cancel_kb())
    await DeleteMovie.movie_id.set()

async def del_process(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
    if not message.text.strip().isdigit():
        return await message.answer("❌ Faqat raqam kiriting!")
    mid = int(message.text.strip())
    movie = get_movie(mid)
    if not movie:
        await state.finish()
        return await message.answer("❌ Bunday ID li kino topilmadi!", reply_markup=admin_menu())
    delete_movie(mid)
    await state.finish()
    await message.answer(
        f"✅ <b>{movie['name_uz']}</b> o'chirildi!",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )

async def stats(message: types.Message):
    if not is_admin(message.from_user.id): return
    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"🎬 Jami kinolar: <b>{count_movies()}</b>\n"
        f"👥 Jami foydalanuvchilar: <b>{count_users()}</b>",
        parse_mode="HTML"
    )

async def back_home(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.finish()
    await message.answer("🏠 Bosh sahifa", reply_markup=main_menu("uz"))

def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_admin,  commands=["admin"])
    dp.register_message_handler(add_start,  lambda m: m.text == "➕ Kino qo'shish")
    dp.register_message_handler(del_start,  lambda m: m.text == "🗑 Kino o'chirish")
    dp.register_message_handler(stats,      lambda m: m.text == "📊 Statistika")
    dp.register_message_handler(back_home,  lambda m: m.text == "🔙 Bosh sahifa")

    dp.register_message_handler(step_name_uz,  state=AddMovie.name_uz)
    dp.register_message_handler(step_name_ru,  state=AddMovie.name_ru)
    dp.register_message_handler(step_category, state=AddMovie.category)
    dp.register_message_handler(step_year,     state=AddMovie.year)
    dp.register_message_handler(step_desc_uz,  state=AddMovie.desc_uz)
    dp.register_message_handler(step_desc_ru,  state=AddMovie.desc_ru)
    dp.register_message_handler(step_file,
        content_types=["video", "document", "text"],
        state=AddMovie.file)
    dp.register_callback_query_handler(step_confirm,
        lambda c: c.data in ["confirm_yes", "confirm_no"],
        state=AddMovie.confirm)
    dp.register_message_handler(del_process, state=DeleteMovie.movie_id)
