import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

admin_ids = []

feedbacks = []

class FeedbackStates(StatesGroup):
    writing_feedback = State()
    rating = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Оставить отзыв", callback_data="leave_feedback")],
        [InlineKeyboardButton(text="⭐ Оценить", callback_data="rate")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ])
    
    await message.answer(
        "💬 Добро пожаловать в систему обратной связи!\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "leave_feedback")
async def leave_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("💬 Напишите ваш отзыв:")
    await state.set_state(FeedbackStates.writing_feedback)
    await callback.answer()

@dp.message(FeedbackStates.writing_feedback)
async def process_feedback(message: Message, state: FSMContext):
    feedback_text = message.text
    user_id = message.from_user.id
    username = message.from_user.username or f"ID: {user_id}"
    
    feedbacks.append({
        "text": feedback_text,
        "user_id": user_id,
        "username": username,
        "rating": None,
        "created_at": datetime.now()
    })
    
    await message.answer("✅ Спасибо за ваш отзыв!")
    
    if admin_ids:
        for admin_id in admin_ids:
            await bot.send_message(
                admin_id,
                f"💬 Новый отзыв от {username}:\n\n{feedback_text}"
            )
    
    await state.clear()

@dp.callback_query(F.data == "rate")
async def rate(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐", callback_data="rate_1"),
         InlineKeyboardButton(text="⭐⭐", callback_data="rate_2"),
         InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5")]
    ])
    
    await callback.message.edit_text(
        "⭐ Оцените наш сервис:",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("rate_"))
async def process_rating(callback: CallbackQuery):
    rating = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    username = callback.from_user.username or f"ID: {user_id}"
    
    feedbacks.append({
        "text": None,
        "user_id": user_id,
        "username": username,
        "rating": rating,
        "created_at": datetime.now()
    })
    
    await callback.message.edit_text(f"✅ Спасибо за оценку {rating} ⭐!")
    
    if admin_ids:
        for admin_id in admin_ids:
            await bot.send_message(
                admin_id,
                f"⭐ Новая оценка от {username}: {rating}/5"
            )
    
    await callback.answer()

@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    if callback.from_user.id not in admin_ids and admin_ids:
        await callback.answer("❌ У вас нет доступа к статистике!", show_alert=True)
        return
    
    total_feedbacks = len(feedbacks)
    ratings = [f["rating"] for f in feedbacks if f["rating"]]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    text = f"📊 Статистика отзывов\n\n"
    text += f"💬 Всего отзывов: {total_feedbacks}\n"
    text += f"⭐ Средняя оценка: {avg_rating:.1f}/5\n"
    text += f"📝 Текстовых отзывов: {len([f for f in feedbacks if f['text']])}\n"
    
    rating_dist = {}
    for f in feedbacks:
        if f["rating"]:
            rating_dist[f["rating"]] = rating_dist.get(f["rating"], 0) + 1
    
    if rating_dist:
        text += "\n📊 Распределение оценок:\n"
        for rating in sorted(rating_dist.keys(), reverse=True):
            text += f"{rating}⭐: {rating_dist[rating]}\n"
    
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором бота отзывов!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    print("🚀 Бот отзывов запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
