import asyncio
from datetime import datetime, timedelta
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

reminders = {}

class ReminderStates(StatesGroup):
    creating_text = State()
    creating_time = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_reminders = [r for r in reminders.values() if r["user_id"] == user_id and r["remind_at"] > datetime.now()]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать напоминание", callback_data="create_reminder")],
        [InlineKeyboardButton(text="📋 Мои напоминания", callback_data="my_reminders")]
    ])
    
    text = "⏰ Добро пожаловать в бота напоминаний!\n\n"
    if user_reminders:
        text += f"У вас {len(user_reminders)} активных напоминаний."
    else:
        text += "У вас нет активных напоминаний."
    
    await message.answer(text, reply_markup=keyboard)

@dp.callback_query(F.data == "create_reminder")
async def create_reminder(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("💬 Напишите текст напоминания:")
    await state.set_state(ReminderStates.creating_text)
    await callback.answer()

@dp.message(ReminderStates.creating_text)
async def process_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text, user_id=message.from_user.id)
    await state.set_state(ReminderStates.creating_time)
    await message.answer("⏰ Через сколько минут напомнить? (Напишите число):")

@dp.message(ReminderStates.creating_time)
async def process_time(message: Message, state: FSMContext):
    try:
        minutes = int(message.text)
        if minutes < 1:
            await message.answer("❌ Количество минут должно быть больше 0!")
            return
        
        data = await state.get_data()
        reminder_id = f"reminder_{len(reminders) + 1}_{message.from_user.id}"
        
        reminders[reminder_id] = {
            "text": data["text"],
            "user_id": data["user_id"],
            "remind_at": datetime.now() + timedelta(minutes=minutes),
            "created_at": datetime.now()
        }
        
        await message.answer(
            f"✅ Напоминание создано!\n\n"
            f"💬 {data['text']}\n"
            f"⏰ Напомню через {minutes} минут"
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "my_reminders")
async def my_reminders(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_reminders = sorted(
        [r for r in reminders.items() if r[1]["user_id"] == user_id and r[1]["remind_at"] > datetime.now()],
        key=lambda x: x[1]["remind_at"]
    )
    
    if not user_reminders:
        await callback.message.edit_text(
            "📋 У вас нет активных напоминаний.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Создать", callback_data="create_reminder")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
            ])
        )
        await callback.answer()
        return
    
    text = "📋 Ваши напоминания:\n\n"
    buttons = []
    for reminder_id, reminder in user_reminders[:10]:
        time_left = reminder["remind_at"] - datetime.now()
        minutes = int(time_left.total_seconds() // 60)
        text += f"⏰ {reminder['text'][:30]}... ({minutes} мин)\n"
        buttons.append([InlineKeyboardButton(
            text=f"🗑️ {reminder['text'][:20]}...",
            callback_data=f"delete_{reminder_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("delete_"))
async def delete_reminder(callback: CallbackQuery):
    reminder_id = callback.data.split("_", 1)[1]
    if reminder_id in reminders:
        if reminders[reminder_id]["user_id"] == callback.from_user.id:
            del reminders[reminder_id]
            await callback.answer("✅ Напоминание удалено!", show_alert=True)
            await my_reminders(callback)
        else:
            await callback.answer("❌ Нет прав!", show_alert=True)
    else:
        await callback.answer("❌ Напоминание не найдено!", show_alert=True)

@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_reminders = [r for r in reminders.values() if r["user_id"] == user_id and r["remind_at"] > datetime.now()]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать напоминание", callback_data="create_reminder")],
        [InlineKeyboardButton(text="📋 Мои напоминания", callback_data="my_reminders")]
    ])
    
    text = "⏰ У вас нет активных напоминаний." if not user_reminders else f"У вас {len(user_reminders)} активных напоминаний."
    
    await callback.message.edit_text(text, reply_markup=keyboard)
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором бота напоминаний!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def check_reminders():
    while True:
        await asyncio.sleep(30)
        now = datetime.now()
        to_remind = [r for r in reminders.items() if r[1]["remind_at"] <= now]
        
        for reminder_id, reminder in to_remind:
            try:
                await bot.send_message(
                    reminder["user_id"],
                    f"⏰ Напоминание:\n\n{reminder['text']}"
                )
                del reminders[reminder_id]
            except:
                del reminders[reminder_id]

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    asyncio.create_task(check_reminders())
    print("🚀 Бот напоминаний запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
