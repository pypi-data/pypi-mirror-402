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

subscribers = []
scheduled_posts = []
tags = {}

class NewsletterStates(StatesGroup):
    creating_message = State()
    scheduling_time = State()
    adding_tag = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id not in subscribers:
        subscribers.append(message.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Подписаться", callback_data="subscribe")],
        [InlineKeyboardButton(text="❌ Отписаться", callback_data="unsubscribe")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ])
    
    await message.answer(
        "📬 Добро пожаловать в бота рассылок!\n\n"
        f"Статус: {'✅ Подписан' if message.from_user.id in subscribers else '❌ Не подписан'}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "subscribe")
async def subscribe(callback: CallbackQuery):
    if callback.from_user.id not in subscribers:
        subscribers.append(callback.from_user.id)
        await callback.answer("✅ Вы подписались на рассылку!", show_alert=True)
    else:
        await callback.answer("ℹ️ Вы уже подписаны!", show_alert=True)
    
    await callback.message.edit_text(
        "📬 Статус: ✅ Подписан",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отписаться", callback_data="unsubscribe")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
        ])
    )

@dp.callback_query(F.data == "unsubscribe")
async def unsubscribe(callback: CallbackQuery):
    if callback.from_user.id in subscribers:
        subscribers.remove(callback.from_user.id)
        await callback.answer("❌ Вы отписались от рассылки!", show_alert=True)
    else:
        await callback.answer("ℹ️ Вы не подписаны!", show_alert=True)
    
    await callback.message.edit_text(
        "📬 Статус: ❌ Не подписан",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Подписаться", callback_data="subscribe")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
        ])
    )

@dp.message(Command("send"))
async def cmd_send(message: Message):
    if admin_ids and message.from_user.id not in admin_ids:
        await message.answer("❌ У вас нет прав для отправки рассылок.")
        return
    
    await message.answer("📬 Создание рассылки\n\n💬 Напишите сообщение для рассылки:")
    await dp.current_state(user=message.from_user.id).set_state(NewsletterStates.creating_message)

@dp.message(NewsletterStates.creating_message)
async def process_message(message: Message, state: FSMContext):
    text = message.text or message.caption or "Рассылка без текста"
    await state.update_data(message_text=text, message_obj=message)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Отправить сейчас", callback_data="send_now")],
        [InlineKeyboardButton(text="⏰ Запланировать", callback_data="schedule")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_send")]
    ])
    
    await message.answer(
        f"📬 Предпросмотр сообщения:\n\n{text}\n\n"
        f"Получателей: {len(subscribers)}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "send_now")
async def send_now(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_text = data.get("message_text")
    message_obj = data.get("message_obj")
    
    sent = 0
    failed = 0
    
    for user_id in subscribers:
        try:
            if message_obj.photo:
                await bot.send_photo(user_id, message_obj.photo[-1].file_id, caption=message_text)
            elif message_obj.document:
                await bot.send_document(user_id, message_obj.document.file_id, caption=message_text)
            else:
                await bot.send_message(user_id, message_text)
            sent += 1
        except:
            failed += 1
    
    await callback.message.edit_text(
        f"✅ Рассылка завершена!\n\n"
        f"✅ Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}"
    )
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "schedule")
async def schedule(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("⏰ Через сколько часов отправить? (Напишите число):")
    await state.set_state(NewsletterStates.scheduling_time)
    await callback.answer()

@dp.message(NewsletterStates.scheduling_time)
async def process_schedule(message: Message, state: FSMContext):
    try:
        hours = int(message.text)
        if hours < 0:
            await message.answer("❌ Количество часов должно быть положительным!")
            return
        
        data = await state.get_data()
        scheduled_posts.append({
            "message_text": data.get("message_text"),
            "message_obj": data.get("message_obj"),
            "send_at": datetime.now() + timedelta(hours=hours),
            "creator_id": message.from_user.id
        })
        
        await message.answer(f"✅ Рассылка запланирована на {hours} часов вперед!")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ У вас нет доступа к статистике!", show_alert=True)
        return
    
    text = f"📊 Статистика рассылок\n\n"
    text += f"👥 Подписчиков: {len(subscribers)}\n"
    text += f"📅 Запланировано: {len(scheduled_posts)}\n"
    
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором бота рассылок!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def check_scheduled_posts():
    while True:
        await asyncio.sleep(60)
        now = datetime.now()
        to_send = [p for p in scheduled_posts if p["send_at"] <= now]
        
        for post in to_send:
            sent = 0
            for user_id in subscribers:
                try:
                    if post["message_obj"].photo:
                        await bot.send_photo(user_id, post["message_obj"].photo[-1].file_id, caption=post["message_text"])
                    elif post["message_obj"].document:
                        await bot.send_document(user_id, post["message_obj"].document.file_id, caption=post["message_text"])
                    else:
                        await bot.send_message(user_id, post["message_text"])
                    sent += 1
                except:
                    pass
            
            scheduled_posts.remove(post)

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    asyncio.create_task(check_scheduled_posts())
    print("🚀 Бот рассылок запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
