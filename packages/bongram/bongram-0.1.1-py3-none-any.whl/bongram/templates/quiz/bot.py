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

quizzes = {}
user_scores = {}
leaderboard = {}

class QuizStates(StatesGroup):
    creating_title = State()
    creating_question = State()
    creating_options = State()
    creating_correct = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    active_quizzes = [qid for qid, q in quizzes.items() if not q.get("closed", False)]
    
    if not active_quizzes:
        await message.answer("🎯 Добро пожаловать в бота викторин!\n\nСейчас нет активных викторин.")
        return
    
    buttons = []
    for qid in active_quizzes[:5]:
        q = quizzes[qid]
        buttons.append([InlineKeyboardButton(
            text=f"🎯 {q['title']}",
            callback_data=f"start_quiz_{qid}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🏆 Рейтинг", callback_data="leaderboard")])
    
    await message.answer(
        "🎯 Выберите викторину:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.message(Command("create"))
async def cmd_create(message: Message):
    if admin_ids and message.from_user.id not in admin_ids:
        await message.answer("❌ У вас нет прав для создания викторин.")
        return
    
    await message.answer("🎯 Создание викторины\n\n📝 Напишите название викторины:")
    await dp.current_state(user=message.from_user.id).set_state(QuizStates.creating_title)

@dp.message(QuizStates.creating_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text, questions=[], creator_id=message.from_user.id)
    await state.set_state(QuizStates.creating_question)
    await message.answer("💬 Напишите первый вопрос:")

@dp.message(QuizStates.creating_question)
async def process_question(message: Message, state: FSMContext):
    await state.update_data(current_question=message.text)
    await state.set_state(QuizStates.creating_options)
    await message.answer("📝 Напишите варианты ответов, каждый с новой строки (минимум 2):")

@dp.message(QuizStates.creating_options)
async def process_options(message: Message, state: FSMContext):
    options = [opt.strip() for opt in message.text.split("\n") if opt.strip()]
    if len(options) < 2:
        await message.answer("❌ Нужно минимум 2 варианта!")
        return
    
    data = await state.get_data()
    questions = data.get("questions", [])
    questions.append({
        "question": data.get("current_question"),
        "options": options
    })
    await state.update_data(questions=questions)
    
    buttons = []
    for idx, opt in enumerate(options, 1):
        buttons.append([InlineKeyboardButton(
            text=f"{idx}. {opt}",
            callback_data=f"set_correct_{len(questions)-1}_{idx-1}"
        )])
    
    await message.answer(
        "✅ Выберите правильный ответ:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data.startswith("set_correct_"))
async def set_correct(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    q_idx = int(parts[2])
    opt_idx = int(parts[3])
    
    data = await state.get_data()
    questions = data.get("questions", [])
    questions[q_idx]["correct"] = opt_idx
    
    await state.update_data(questions=questions)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вопрос", callback_data="add_question")],
        [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_quiz")]
    ])
    
    await callback.message.edit_text(
        "✅ Правильный ответ установлен!\n\nДобавить еще вопрос или завершить?",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "add_question")
async def add_question(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QuizStates.creating_question)
    await callback.message.edit_text("💬 Напишите следующий вопрос:")
    await callback.answer()

@dp.callback_query(F.data == "finish_quiz")
async def finish_quiz(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_id = f"quiz_{len(quizzes) + 1}_{callback.from_user.id}"
    
    quizzes[quiz_id] = {
        "title": data["title"],
        "questions": data["questions"],
        "creator_id": data["creator_id"],
        "closed": False
    }
    
    await state.clear()
    await callback.message.edit_text(f"✅ Викторина '{data['title']}' создана!")
    await callback.answer()

@dp.callback_query(F.data.startswith("start_quiz_"))
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    quiz_id = callback.data.split("_")[2]
    if quiz_id not in quizzes:
        await callback.answer("❌ Викторина не найдена!", show_alert=True)
        return
    
    quiz = quizzes[quiz_id]
    user_id = callback.from_user.id
    
    if f"{quiz_id}_{user_id}" in user_scores:
        await callback.answer("ℹ️ Вы уже проходили эту викторину!", show_alert=True)
        return
    
    await state.update_data(quiz_id=quiz_id, current_q=0, score=0, user_id=user_id)
    await show_question(callback, state)

async def show_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_id = data["quiz_id"]
    current_q = data["current_q"]
    quiz = quizzes[quiz_id]
    
    if current_q >= len(quiz["questions"]):
        score = data["score"]
        total = len(quiz["questions"])
        percentage = (score / total * 100) if total > 0 else 0
        
        user_id = data["user_id"]
        user_scores[f"{quiz_id}_{user_id}"] = score
        
        if user_id not in leaderboard:
            leaderboard[user_id] = 0
        leaderboard[user_id] += score
        
        await callback.message.edit_text(
            f"🎯 Викторина завершена!\n\n"
            f"🏆 Ваш результат: {score}/{total} ({percentage:.1f}%)\n\n"
            f"Отличная работа!" if percentage >= 80 else "Хорошая попытка!" if percentage >= 50 else "Попробуйте еще раз!"
        )
        await state.clear()
        await callback.answer()
        return
    
    question = quiz["questions"][current_q]
    buttons = []
    for idx, opt in enumerate(question["options"]):
        buttons.append([InlineKeyboardButton(
            text=f"{opt}",
            callback_data=f"answer_{idx}"
        )])
    
    await callback.message.edit_text(
        f"❓ Вопрос {current_q + 1}/{len(quiz['questions'])}\n\n{question['question']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    answer_idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    quiz_id = data["quiz_id"]
    current_q = data["current_q"]
    quiz = quizzes[quiz_id]
    
    question = quiz["questions"][current_q]
    is_correct = answer_idx == question.get("correct")
    
    if is_correct:
        await state.update_data(score=data["score"] + 1)
        await callback.answer("✅ Правильно!", show_alert=True)
    else:
        await callback.answer("❌ Неправильно!", show_alert=True)
    
    await state.update_data(current_q=current_q + 1)
    await asyncio.sleep(1)
    await show_question(callback, state)

@dp.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    
    text = "🏆 Рейтинг игроков:\n\n"
    for idx, (user_id, score) in enumerate(sorted_leaderboard[:10], 1):
        try:
            user = await bot.get_chat(user_id)
            username = user.username or f"ID: {user_id}"
            text += f"{idx}. @{username} - {score} очков\n"
        except:
            text += f"{idx}. ID: {user_id} - {score} очков\n"
    
    if not sorted_leaderboard:
        text = "🏆 Рейтинг пуст. Пройдите викторины, чтобы попасть в рейтинг!"
    
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором бота викторин!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    print("🚀 Бот викторин запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
