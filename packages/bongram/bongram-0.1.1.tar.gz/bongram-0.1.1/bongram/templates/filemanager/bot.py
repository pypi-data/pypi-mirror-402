import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

admin_ids = []

user_files = {}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in user_files:
        user_files[user_id] = []
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Загрузить файл", callback_data="upload_file")],
        [InlineKeyboardButton(text="📋 Мои файлы", callback_data="my_files")]
    ])
    
    await message.answer(
        "📁 Добро пожаловать в файловый менеджер!\n\n"
        f"У вас сохранено файлов: {len(user_files[user_id])}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "upload_file")
async def upload_file(callback: CallbackQuery):
    await callback.message.edit_text("📤 Отправьте файл, который хотите сохранить:")
    await callback.answer()

@dp.message(F.document | F.photo | F.video | F.audio | F.voice)
async def save_file(message: Message):
    user_id = message.from_user.id
    if user_id not in user_files:
        user_files[user_id] = []
    
    file_info = {
        "file_id": None,
        "file_type": None,
        "file_name": None,
        "saved_at": datetime.now()
    }
    
    if message.document:
        file_info["file_id"] = message.document.file_id
        file_info["file_type"] = "document"
        file_info["file_name"] = message.document.file_name or "document"
    elif message.photo:
        file_info["file_id"] = message.photo[-1].file_id
        file_info["file_type"] = "photo"
        file_info["file_name"] = "photo.jpg"
    elif message.video:
        file_info["file_id"] = message.video.file_id
        file_info["file_type"] = "video"
        file_info["file_name"] = message.video.file_name or "video"
    elif message.audio:
        file_info["file_id"] = message.audio.file_id
        file_info["file_type"] = "audio"
        file_info["file_name"] = message.audio.file_name or "audio"
    elif message.voice:
        file_info["file_id"] = message.voice.file_id
        file_info["file_type"] = "voice"
        file_info["file_name"] = "voice.ogg"
    
    user_files[user_id].append(file_info)
    await message.answer(f"✅ Файл '{file_info['file_name']}' сохранен!")

@dp.callback_query(F.data == "my_files")
async def my_files(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_files or not user_files[user_id]:
        await callback.message.edit_text(
            "📋 У вас нет сохраненных файлов.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📤 Загрузить", callback_data="upload_file")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
            ])
        )
        await callback.answer()
        return
    
    files = user_files[user_id]
    buttons = []
    for idx, file_info in enumerate(files[-10:], 1):
        buttons.append([InlineKeyboardButton(
            text=f"📄 {file_info['file_name'][:30]}...",
            callback_data=f"get_file_{len(files) - 10 + idx - 1}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")])
    
    await callback.message.edit_text(
        f"📋 Ваши файлы ({len(files)}):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("get_file_"))
async def get_file(callback: CallbackQuery):
    user_id = callback.from_user.id
    file_idx = int(callback.data.split("_")[2])
    
    if user_id not in user_files or file_idx >= len(user_files[user_id]):
        await callback.answer("❌ Файл не найден!", show_alert=True)
        return
    
    file_info = user_files[user_id][file_idx]
    
    try:
        if file_info["file_type"] == "photo":
            await bot.send_photo(user_id, file_info["file_id"])
        elif file_info["file_type"] == "video":
            await bot.send_video(user_id, file_info["file_id"])
        elif file_info["file_type"] == "audio":
            await bot.send_audio(user_id, file_info["file_id"])
        elif file_info["file_type"] == "voice":
            await bot.send_voice(user_id, file_info["file_id"])
        else:
            await bot.send_document(user_id, file_info["file_id"])
        
        await callback.answer("✅ Файл отправлен!")
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_files:
        user_files[user_id] = []
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Загрузить файл", callback_data="upload_file")],
        [InlineKeyboardButton(text="📋 Мои файлы", callback_data="my_files")]
    ])
    
    await callback.message.edit_text(
        f"📁 У вас сохранено файлов: {len(user_files[user_id])}",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.message(Command("addadmin"))
async def cmd_addadmin(message: Message):
    if admin_ids and message.from_user.id not in admin_ids:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    if message.reply_to_message:
        new_admin_id = message.reply_to_message.from_user.id
    else:
        try:
            new_admin_id = int(message.text.split()[1])
        except (IndexError, ValueError):
            await message.answer("❌ Использование: /addadmin <user_id>")
            return
    
    if new_admin_id not in admin_ids:
        admin_ids.append(new_admin_id)
        await message.answer(f"✅ Пользователь {new_admin_id} добавлен в администраторы.")
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором файлового менеджера!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    print("🚀 Файловый менеджер запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
