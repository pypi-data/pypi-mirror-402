import asyncio
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

class SupportStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Задать вопрос", callback_data="ask_question")]
    ])
    await message.answer(
        "👋 Добро пожаловать в службу поддержки!\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in admin_ids:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список вопросов", callback_data="list_questions")],
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="add_admin")]
    ])
    await message.answer("🔧 Админ-панель:", reply_markup=keyboard)

@dp.callback_query(F.data == "ask_question")
async def ask_question(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("💬 Напишите ваш вопрос:")
    await state.set_state(SupportStates.waiting_for_question)
    await callback.answer()

@dp.message(SupportStates.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    question_text = message.text or "Вопрос без текста"
    user_id = message.from_user.id
    username = message.from_user.username or f"ID: {user_id}"
    
    await state.update_data(question=question_text, user_id=user_id, username=username)
    
    if admin_ids:
        for admin_id in admin_ids:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Ответить", callback_data=f"answer_{user_id}")]
            ])
            await bot.send_message(
                admin_id,
                f"❓ Новый вопрос от {username}:\n\n{question_text}",
                reply_markup=keyboard
            )
    
    await message.answer("✅ Ваш вопрос отправлен! Ожидайте ответа от администратора.")
    await state.clear()

@dp.callback_query(F.data.startswith("answer_"))
async def answer_question(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ У вас нет прав администратора!", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[1])
    await state.update_data(target_user_id=user_id)
    await callback.message.edit_text("💬 Напишите ответ на вопрос:")
    await state.set_state(SupportStates.waiting_for_answer)
    await callback.answer()

@dp.message(SupportStates.waiting_for_answer)
async def process_answer(message: Message, state: FSMContext):
    if message.from_user.id not in admin_ids:
        await state.clear()
        return
    
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    answer_text = message.text or "Ответ без текста"
    
    if target_user_id:
        await bot.send_message(
            target_user_id,
            f"📩 Ответ от администратора:\n\n{answer_text}"
        )
        await message.answer("✅ Ответ отправлен пользователю!")
    
    await state.clear()

@dp.callback_query(F.data == "add_admin")
async def add_admin_handler(callback: CallbackQuery):
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ У вас нет прав!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ Чтобы добавить администратора, используйте команду:\n"
        "/addadmin <user_id>\n\n"
        "Или отправьте /addadmin в ответ на сообщение пользователя."
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
            await message.answer("❌ Использование: /addadmin <user_id> или ответьте на сообщение пользователя")
            return
    
    if new_admin_id not in admin_ids:
        admin_ids.append(new_admin_id)
        await message.answer(f"✅ Пользователь {new_admin_id} добавлен в администраторы.")
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором бота поддержки!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

@dp.callback_query(F.data == "list_questions")
async def list_questions(callback: CallbackQuery):
    await callback.message.edit_text("📋 Функция списка вопросов будет доступна в следующих версиях.")
    await callback.answer()

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
        print("   или добавьте ID в переменную admin_ids в коде.")
    
    print("🚀 Бот поддержки запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
