import asyncio
import hashlib
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

admin_ids = []

referrals = {}
user_stats = {}

def generate_ref_link(user_id: int):
    return hashlib.md5(f"ref_{user_id}".encode()).hexdigest()[:8]

@dp.message(Command("start"))
async def cmd_start(message: Message):
    args = message.text.split()
    user_id = message.from_user.id
    
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1].replace("ref_", "")
        referrer_id = None
        for uid, stats in user_stats.items():
            if stats.get("ref_code") == ref_code:
                referrer_id = uid
                break
        
        if referrer_id and referrer_id != user_id:
            if user_id not in referrals:
                referrals[user_id] = referrer_id
                if referrer_id not in user_stats:
                    user_stats[referrer_id] = {"ref_code": generate_ref_link(referrer_id), "referrals": 0, "bonus": 0}
                user_stats[referrer_id]["referrals"] += 1
                user_stats[referrer_id]["bonus"] += 10
                
                await bot.send_message(
                    referrer_id,
                    f"🎉 Новый реферал! Вы получили 10 бонусов!\n"
                    f"Всего рефералов: {user_stats[referrer_id]['referrals']}"
                )
    
    if user_id not in user_stats:
        user_stats[user_id] = {
            "ref_code": generate_ref_link(user_id),
            "referrals": 0,
            "bonus": 0
        }
    
    stats = user_stats[user_id]
    ref_link = f"https://t.me/{await bot.get_me().username}?start=ref_{stats['ref_code']}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться ссылкой", url=f"https://t.me/share/url?url={ref_link}&text=Присоединяйся!")],
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats")],
        [InlineKeyboardButton(text="🏆 Топ рефералов", callback_data="top_refs")]
    ])
    
    await message.answer(
        f"👋 Добро пожаловать в реферальную программу!\n\n"
        f"📊 Ваша статистика:\n"
        f"👥 Рефералов: {stats['referrals']}\n"
        f"💰 Бонусов: {stats['bonus']}\n\n"
        f"🔗 Ваша реферальная ссылка:\n{ref_link}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "my_stats")
async def my_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_stats:
        user_stats[user_id] = {
            "ref_code": generate_ref_link(user_id),
            "referrals": 0,
            "bonus": 0
        }
    
    stats = user_stats[user_id]
    ref_link = f"https://t.me/{await bot.get_me().username}?start=ref_{stats['ref_code']}"
    
    text = f"📊 Ваша статистика\n\n"
    text += f"👥 Рефералов: {stats['referrals']}\n"
    text += f"💰 Бонусов: {stats['bonus']}\n\n"
    text += f"🔗 Ваша ссылка:\n{ref_link}"
    
    await callback.message.edit_text(text)
    await callback.answer()

@dp.callback_query(F.data == "top_refs")
async def top_refs(callback: CallbackQuery):
    sorted_stats = sorted(user_stats.items(), key=lambda x: x[1]["referrals"], reverse=True)
    
    text = "🏆 Топ рефералов:\n\n"
    for idx, (user_id, stats) in enumerate(sorted_stats[:10], 1):
        try:
            user = await bot.get_chat(user_id)
            username = user.username or f"ID: {user_id}"
            text += f"{idx}. @{username} - {stats['referrals']} рефералов\n"
        except:
            text += f"{idx}. ID: {user_id} - {stats['referrals']} рефералов\n"
    
    if not sorted_stats:
        text = "🏆 Рейтинг пуст."
    
    await callback.message.edit_text(text)
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором реферальной программы!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    print("🚀 Бот реферальной программы запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
