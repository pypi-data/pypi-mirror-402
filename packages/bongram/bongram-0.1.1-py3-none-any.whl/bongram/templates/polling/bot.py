import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Poll
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

admin_ids = []

polls = {}

class PollingStates(StatesGroup):
    creating_question = State()
    creating_options = State()
    creating_anonymous = State()

def build_polls_keyboard():
    active_polls = [pid for pid, p in polls.items() if not p.get("closed", False)]
    buttons = []
    for pid in active_polls[:5]:
        p = polls[pid]
        buttons.append([InlineKeyboardButton(
            text=f"📊 {p['question'][:30]}...",
            callback_data=f"view_poll_{pid}"
        )])
    if admin_ids:
        buttons.append([InlineKeyboardButton(text="➕ Создать опрос", callback_data="create_poll")])
        buttons.append([InlineKeyboardButton(text="📊 Мои опросы", callback_data="my_polls")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "📊 Добро пожаловать в бота опросов!\n\n"
        "Выберите опрос для участия:",
        reply_markup=build_polls_keyboard()
    )

@dp.message(Command("create"))
async def cmd_create(message: Message):
    if admin_ids and message.from_user.id not in admin_ids:
        await message.answer("❌ У вас нет прав для создания опросов.")
        return
    
    await message.answer("📊 Создание нового опроса\n\n💬 Напишите вопрос опроса:")
    await dp.current_state(user=message.from_user.id).set_state(PollingStates.creating_question)

@dp.callback_query(F.data == "create_poll")
async def create_poll(callback: CallbackQuery, state: FSMContext):
    if admin_ids and callback.from_user.id not in admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    await callback.message.edit_text("💬 Напишите вопрос опроса:")
    await state.set_state(PollingStates.creating_question)
    await callback.answer()

@dp.message(PollingStates.creating_question)
async def process_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text, creator_id=message.from_user.id)
    await state.set_state(PollingStates.creating_options)
    await message.answer("📝 Напишите варианты ответов, каждый с новой строки (минимум 2 варианта):")

@dp.message(PollingStates.creating_options)
async def process_options(message: Message, state: FSMContext):
    options = [opt.strip() for opt in message.text.split("\n") if opt.strip()]
    if len(options) < 2:
        await message.answer("❌ Нужно минимум 2 варианта ответа!")
        return
    
    if len(options) > 10:
        await message.answer("❌ Максимум 10 вариантов ответа!")
        return
    
    await state.update_data(options=options)
    await state.set_state(PollingStates.creating_anonymous)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Анонимный", callback_data="anon_yes")],
        [InlineKeyboardButton(text="❌ Публичный", callback_data="anon_no")]
    ])
    await message.answer("🔒 Опрос будет анонимным или публичным?", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("anon_"))
async def process_anonymous(callback: CallbackQuery, state: FSMContext):
    is_anonymous = callback.data == "anon_yes"
    data = await state.get_data()
    
    poll_id = f"poll_{len(polls) + 1}_{callback.from_user.id}"
    polls[poll_id] = {
        "question": data["question"],
        "options": data["options"],
        "anonymous": is_anonymous,
        "creator_id": data["creator_id"],
        "votes": {opt: [] for opt in data["options"]},
        "created_at": datetime.now(),
        "closed": False
    }
    
    await state.clear()
    
    poll_text = f"📊 Опрос создан!\n\n❓ {data['question']}\n\n"
    for idx, opt in enumerate(data["options"], 1):
        poll_text += f"{idx}. {opt}\n"
    
    await callback.message.edit_text(
        poll_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Просмотреть", callback_data=f"view_poll_{poll_id}")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("view_poll_"))
async def view_poll(callback: CallbackQuery):
    poll_id = callback.data.split("_")[2]
    if poll_id not in polls:
        await callback.answer("❌ Опрос не найден!", show_alert=True)
        return
    
    p = polls[poll_id]
    user_id = callback.from_user.id
    user_voted = any(user_id in votes for votes in p["votes"].values())
    
    text = f"📊 {p['question']}\n\n"
    total_votes = sum(len(votes) for votes in p["votes"].values())
    
    for opt, votes in p["votes"].items():
        count = len(votes)
        percentage = (count / total_votes * 100) if total_votes > 0 else 0
        bar = "█" * int(percentage / 5)
        text += f"{opt}: {count} ({percentage:.1f}%)\n{bar}\n\n"
    
    text += f"👥 Всего голосов: {total_votes}\n"
    text += f"🔒 {'Анонимный' if p['anonymous'] else 'Публичный'}"
    
    buttons = []
    if not user_voted and not p["closed"]:
        for idx, opt in enumerate(p["options"]):
            buttons.append([InlineKeyboardButton(
                text=f"✅ {opt}",
                callback_data=f"vote_{poll_id}_{idx}"
            )])
    
    if p["creator_id"] == user_id or user_id in admin_ids:
        buttons.append([InlineKeyboardButton(
            text="🔒 Закрыть опрос" if not p["closed"] else "✅ Опрос закрыт",
            callback_data=f"close_{poll_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_polls")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("vote_"))
async def vote(callback: CallbackQuery):
    parts = callback.data.split("_")
    poll_id = parts[1]
    option_idx = int(parts[2])
    
    if poll_id not in polls:
        await callback.answer("❌ Опрос не найден!", show_alert=True)
        return
    
    p = polls[poll_id]
    user_id = callback.from_user.id
    
    if p["closed"]:
        await callback.answer("❌ Опрос закрыт!", show_alert=True)
        return
    
    for votes in p["votes"].values():
        if user_id in votes:
            votes.remove(user_id)
    
    if option_idx < len(p["options"]):
        p["votes"][p["options"][option_idx]].append(user_id)
        await callback.answer("✅ Ваш голос учтен!", show_alert=True)
        await view_poll(callback)

@dp.callback_query(F.data.startswith("close_"))
async def close_poll(callback: CallbackQuery):
    poll_id = callback.data.split("_")[1]
    if poll_id not in polls:
        await callback.answer("❌ Опрос не найден!", show_alert=True)
        return
    
    p = polls[poll_id]
    if callback.from_user.id != p["creator_id"] and callback.from_user.id not in admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    p["closed"] = not p["closed"]
    await callback.answer(f"{'Закрыт' if p['closed'] else 'Открыт'}!", show_alert=True)
    await view_poll(callback)

@dp.callback_query(F.data == "my_polls")
async def my_polls(callback: CallbackQuery):
    if callback.from_user.id not in admin_ids:
        user_polls = [pid for pid, p in polls.items() if p["creator_id"] == callback.from_user.id]
    else:
        user_polls = list(polls.keys())
    
    if not user_polls:
        await callback.message.edit_text("📊 У вас пока нет опросов.")
        await callback.answer()
        return
    
    buttons = []
    for pid in user_polls[:10]:
        p = polls[pid]
        status = "🔒" if p["closed"] else "✅"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {p['question'][:40]}...",
            callback_data=f"view_poll_{pid}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_polls")])
    
    await callback.message.edit_text(
        "📊 Ваши опросы:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_polls")
async def back_to_polls(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 Выберите опрос:",
        reply_markup=build_polls_keyboard()
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором бота опросов!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    print("🚀 Бот опросов запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
