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

slots = {}
bookings = {}

class BookingStates(StatesGroup):
    creating_slot = State()
    selecting_date = State()
    selecting_time = State()

def generate_slots(date_obj):
    times = []
    for hour in range(9, 18):
        for minute in [0, 30]:
            slot_time = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if slot_time > datetime.now():
                slot_id = slot_time.strftime("%Y%m%d_%H%M")
                if slot_id not in bookings:
                    times.append((slot_id, slot_time.strftime("%H:%M")))
    return times

@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Забронировать", callback_data="book_slot")],
        [InlineKeyboardButton(text="📋 Мои бронирования", callback_data="my_bookings")]
    ])
    
    if message.from_user.id in admin_ids or not admin_ids:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔧 Управление", callback_data="admin_panel")])
    
    await message.answer(
        "📅 Добро пожаловать в систему бронирования!\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "book_slot")
async def book_slot(callback: CallbackQuery, state: FSMContext):
    today = datetime.now().date()
    buttons = []
    for i in range(7):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.strftime("%d.%m")
        weekday = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][date_obj.weekday()]
        buttons.append([InlineKeyboardButton(
            text=f"{date_str} ({weekday})",
            callback_data=f"select_date_{date_obj.strftime('%Y%m%d')}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")])
    
    await callback.message.edit_text(
        "📅 Выберите дату:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("select_date_"))
async def select_date(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split("_")[2]
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    available_slots = generate_slots(date_obj)
    
    if not available_slots:
        await callback.answer("❌ Нет доступных слотов на эту дату!", show_alert=True)
        return
    
    buttons = []
    for slot_id, time_str in available_slots[:10]:
        buttons.append([InlineKeyboardButton(
            text=f"🕐 {time_str}",
            callback_data=f"select_time_{slot_id}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="book_slot")])
    
    await callback.message.edit_text(
        f"🕐 Выберите время на {date_obj.strftime('%d.%m.%Y')}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("select_time_"))
async def select_time(callback: CallbackQuery):
    slot_id = callback.data.split("_")[2]
    user_id = callback.from_user.id
    
    if slot_id in bookings:
        await callback.answer("❌ Этот слот уже занят!", show_alert=True)
        return
    
    slot_time = datetime.strptime(slot_id, "%Y%m%d_%H%M")
    bookings[slot_id] = {
        "user_id": user_id,
        "username": callback.from_user.username or f"ID: {user_id}",
        "slot_time": slot_time,
        "created_at": datetime.now()
    }
    
    await callback.answer("✅ Бронирование создано!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Бронирование подтверждено!\n\n"
        f"📅 Дата: {slot_time.strftime('%d.%m.%Y')}\n"
        f"🕐 Время: {slot_time.strftime('%H:%M')}\n\n"
        f"Мы напомним вам за час до бронирования."
    )
    
    if admin_ids:
        for admin_id in admin_ids:
            await bot.send_message(
                admin_id,
                f"📅 Новое бронирование от {callback.from_user.username or f'ID: {user_id}'}\n"
                f"Дата: {slot_time.strftime('%d.%m.%Y %H:%M')}"
            )

@dp.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_bookings = [b for b in bookings.values() if b["user_id"] == user_id]
    
    if not user_bookings:
        await callback.message.edit_text(
            "📋 У вас нет активных бронирований.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
            ])
        )
        await callback.answer()
        return
    
    text = "📋 Ваши бронирования:\n\n"
    for idx, booking in enumerate(sorted(user_bookings, key=lambda x: x["slot_time"]), 1):
        if booking["slot_time"] > datetime.now():
            text += f"{idx}. {booking['slot_time'].strftime('%d.%m.%Y %H:%M')}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id not in admin_ids and admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    all_bookings = sorted(bookings.values(), key=lambda x: x["slot_time"])
    upcoming = [b for b in all_bookings if b["slot_time"] > datetime.now()]
    
    text = f"🔧 Админ-панель\n\n"
    text += f"📅 Активных бронирований: {len(upcoming)}\n\n"
    
    for booking in upcoming[:5]:
        text += f"📅 {booking['slot_time'].strftime('%d.%m %H:%M')} - {booking['username']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Все бронирования", callback_data="all_bookings")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "all_bookings")
async def all_bookings(callback: CallbackQuery):
    if callback.from_user.id not in admin_ids and admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    all_bookings = sorted(bookings.values(), key=lambda x: x["slot_time"])
    text = "📊 Все бронирования:\n\n"
    
    for booking in all_bookings:
        status = "✅" if booking["slot_time"] > datetime.now() else "❌"
        text += f"{status} {booking['slot_time'].strftime('%d.%m %H:%M')} - {booking['username']}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Забронировать", callback_data="book_slot")],
        [InlineKeyboardButton(text="📋 Мои бронирования", callback_data="my_bookings")]
    ])
    
    if callback.from_user.id in admin_ids or not admin_ids:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔧 Управление", callback_data="admin_panel")])
    
    await callback.message.edit_text(
        "📅 Выберите действие:",
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором бота бронирований!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def send_reminders():
    while True:
        await asyncio.sleep(300)
        now = datetime.now()
        for slot_id, booking in bookings.items():
            time_diff = booking["slot_time"] - now
            if timedelta(hours=0, minutes=55) < time_diff < timedelta(hours=1, minutes=5):
                try:
                    await bot.send_message(
                        booking["user_id"],
                        f"⏰ Напоминание: у вас бронирование через час!\n"
                        f"📅 {booking['slot_time'].strftime('%d.%m.%Y %H:%M')}"
                    )
                except:
                    pass

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    asyncio.create_task(send_reminders())
    print("🚀 Бот бронирований запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
