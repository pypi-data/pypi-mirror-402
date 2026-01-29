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

faq_data = {
    "general": [
        {"question": "Что это за бот?", "answer": "Это бот с часто задаваемыми вопросами. Здесь вы найдете ответы на популярные вопросы."},
        {"question": "Как начать работу?", "answer": "Используйте команду /start или выберите категорию из меню."},
    ],
    "payment": [
        {"question": "Какие способы оплаты?", "answer": "Мы принимаем карты, электронные кошельки и криптовалюту."},
        {"question": "Как вернуть деньги?", "answer": "Возврат возможен в течение 14 дней с момента покупки."},
    ],
    "technical": [
        {"question": "Не работает функция", "answer": "Попробуйте перезапустить бота командой /start. Если проблема сохраняется, обратитесь в поддержку."},
        {"question": "Как обновить бота?", "answer": "Бот обновляется автоматически. Просто перезапустите его командой /start."},
    ]
}

class FAQStates(StatesGroup):
    adding_category = State()
    adding_question = State()
    adding_answer = State()
    editing_question = State()
    editing_answer = State()
    deleting_question = State()

def build_categories_keyboard():
    buttons = []
    for category in faq_data.keys():
        buttons.append([InlineKeyboardButton(
            text=f"📁 {category.capitalize()}",
            callback_data=f"category_{category}"
        )])
    if admin_ids:
        buttons.append([InlineKeyboardButton(text="➕ Добавить вопрос", callback_data="add_question")])
        buttons.append([InlineKeyboardButton(text="🔧 Админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def build_category_questions_keyboard(category: str):
    buttons = []
    for idx, item in enumerate(faq_data[category]):
        buttons.append([InlineKeyboardButton(
            text=f"❓ {item['question']}",
            callback_data=f"question_{category}_{idx}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "📚 Добро пожаловать в базу знаний!\n\n"
        "Выберите категорию, чтобы найти ответ на ваш вопрос:",
        reply_markup=build_categories_keyboard()
    )

@dp.message(Command("search"))
async def cmd_search(message: Message):
    query = message.text.replace("/search", "").strip().lower()
    if not query:
        await message.answer("🔍 Использование: /search <ваш вопрос>")
        return
    
    results = []
    for category, items in faq_data.items():
        for item in items:
            if query in item['question'].lower() or query in item['answer'].lower():
                results.append(f"📁 {category.capitalize()}\n❓ {item['question']}\n💡 {item['answer']}\n")
    
    if results:
        await message.answer("🔍 Результаты поиска:\n\n" + "\n".join(results[:5]))
    else:
        await message.answer("❌ Ничего не найдено. Попробуйте другой запрос.")

@dp.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "📚 Выберите категорию:",
        reply_markup=build_categories_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("category_"))
async def show_category(callback: CallbackQuery):
    category = callback.data.split("_")[1]
    if category not in faq_data:
        await callback.answer("❌ Категория не найдена!", show_alert=True)
        return
    
    if not faq_data[category]:
        await callback.message.edit_text(
            f"📁 {category.capitalize()}\n\n❌ В этой категории пока нет вопросов.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_categories")]
            ])
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"📁 {category.capitalize()}\n\nВыберите вопрос:",
        reply_markup=build_category_questions_keyboard(category)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("question_"))
async def show_answer(callback: CallbackQuery):
    parts = callback.data.split("_")
    category = parts[1]
    idx = int(parts[2])
    
    if category not in faq_data or idx >= len(faq_data[category]):
        await callback.answer("❌ Вопрос не найден!", show_alert=True)
        return
    
    item = faq_data[category][idx]
    keyboard_buttons = [
        [InlineKeyboardButton(text="◀️ Назад к категории", callback_data=f"category_{category}")]
    ]
    
    if callback.from_user.id in admin_ids:
        keyboard_buttons.append([
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{category}_{idx}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{category}_{idx}")
        ])
    
    await callback.message.edit_text(
        f"❓ {item['question']}\n\n💡 {item['answer']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ У вас нет прав администратора!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вопрос", callback_data="add_question")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="add_admin")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_categories")]
    ])
    await callback.message.edit_text("🔧 Админ-панель:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "add_question")
async def add_question_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ У вас нет прав!", show_alert=True)
        return
    
    buttons = []
    for category in faq_data.keys():
        buttons.append([InlineKeyboardButton(
            text=f"📁 {category.capitalize()}",
            callback_data=f"add_to_{category}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ Новая категория", callback_data="new_category")])
    buttons.append([InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_categories")])
    
    await callback.message.edit_text(
        "➕ Выберите категорию для нового вопроса:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("add_to_"))
async def add_question_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[2]
    await state.update_data(category=category)
    await state.set_state(FAQStates.adding_question)
    await callback.message.edit_text("💬 Напишите вопрос:")
    await callback.answer()

@dp.callback_query(F.data == "new_category")
async def new_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FAQStates.adding_category)
    await callback.message.edit_text("📁 Напишите название новой категории (на английском, без пробелов):")
    await callback.answer()

@dp.message(FAQStates.adding_category)
async def process_category(message: Message, state: FSMContext):
    category = message.text.strip().lower().replace(" ", "_")
    if category in faq_data:
        await message.answer("❌ Эта категория уже существует!")
        return
    
    faq_data[category] = []
    await state.update_data(category=category)
    await state.set_state(FAQStates.adding_question)
    await message.answer("✅ Категория создана! Теперь напишите вопрос:")

@dp.message(FAQStates.adding_question)
async def process_question(message: Message, state: FSMContext):
    question = message.text
    await state.update_data(question=question)
    await state.set_state(FAQStates.adding_answer)
    await message.answer("💡 Теперь напишите ответ на вопрос:")

@dp.message(FAQStates.adding_answer)
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    question = data.get("question")
    answer = message.text
    
    faq_data[category].append({"question": question, "answer": answer})
    await message.answer(f"✅ Вопрос добавлен в категорию '{category}'!")
    await state.clear()

@dp.callback_query(F.data.startswith("edit_"))
async def edit_question(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    category = parts[1]
    idx = int(parts[2])
    await state.update_data(category=category, idx=idx, editing=True)
    await state.set_state(FAQStates.editing_question)
    await callback.message.edit_text("✏️ Напишите новый текст вопроса:")
    await callback.answer()

@dp.message(FAQStates.editing_question)
async def process_edit_question(message: Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    idx = data.get("idx")
    faq_data[category][idx]["question"] = message.text
    await state.set_state(FAQStates.editing_answer)
    await message.answer("💡 Теперь напишите новый ответ:")

@dp.message(FAQStates.editing_answer)
async def process_edit_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    idx = data.get("idx")
    faq_data[category][idx]["answer"] = message.text
    await message.answer("✅ Вопрос обновлен!")
    await state.clear()

@dp.callback_query(F.data.startswith("delete_"))
async def delete_question(callback: CallbackQuery):
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    category = parts[1]
    idx = int(parts[2])
    
    if category in faq_data and idx < len(faq_data[category]):
        del faq_data[category][idx]
        await callback.answer("✅ Вопрос удален!", show_alert=True)
        await callback.message.edit_text(
            "✅ Вопрос удален!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data=f"category_{category}")]
            ])
        )
    else:
        await callback.answer("❌ Ошибка!", show_alert=True)

@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    total_questions = sum(len(items) for items in faq_data.values())
    stats_text = f"📊 Статистика:\n\n"
    stats_text += f"📁 Категорий: {len(faq_data)}\n"
    stats_text += f"❓ Всего вопросов: {total_questions}\n\n"
    
    for category, items in faq_data.items():
        stats_text += f"📁 {category.capitalize()}: {len(items)} вопросов\n"
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
        ])
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором FAQ бота!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    print("🚀 FAQ бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
