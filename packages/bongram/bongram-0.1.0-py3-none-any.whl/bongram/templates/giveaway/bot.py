import asyncio
import random
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

giveaways = {}

class GiveawayStates(StatesGroup):
    creating_title = State()
    creating_description = State()
    creating_winners_count = State()
    creating_end_date = State()

def build_giveaway_keyboard(giveaway_id: str, user_id: int):
    giveaway = giveaways[giveaway_id]
    is_participant = user_id in giveaway["participants"]
    is_ended = datetime.now() > giveaway["end_date"]
    
    buttons = []
    if not is_ended:
        if is_participant:
            buttons.append([InlineKeyboardButton(
                text="✅ Вы участвуете",
                callback_data=f"already_participant_{giveaway_id}"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="🎁 Участвовать",
                callback_data=f"participate_{giveaway_id}"
            )])
    
    buttons.append([InlineKeyboardButton(
        text=f"👥 Участников: {len(giveaway['participants'])}",
        callback_data=f"participants_{giveaway_id}"
    )])
    
    if giveaway["creator_id"] == user_id or user_id in admin_ids:
        buttons.append([InlineKeyboardButton(
            text="🔧 Управление",
            callback_data=f"manage_{giveaway_id}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    active_giveaways = [gid for gid, g in giveaways.items() if datetime.now() < g["end_date"]]
    
    if not active_giveaways:
        text = "🎁 Добро пожаловать в бота розыгрышей!\n\n"
        text += "Сейчас нет активных розыгрышей."
        if message.from_user.id in admin_ids or not admin_ids:
            text += "\n\nИспользуйте /create для создания нового розыгрыша."
        await message.answer(text)
        return
    
    buttons = []
    for gid in active_giveaways[:5]:
        g = giveaways[gid]
        buttons.append([InlineKeyboardButton(
            text=f"🎁 {g['title']}",
            callback_data=f"view_{gid}"
        )])
    
    if message.from_user.id in admin_ids or not admin_ids:
        buttons.append([InlineKeyboardButton(text="➕ Создать розыгрыш", callback_data="create_giveaway")])
    
    await message.answer(
        "🎁 Активные розыгрыши:\n\nВыберите розыгрыш для участия:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.message(Command("create"))
async def cmd_create(message: Message):
    if admin_ids and message.from_user.id not in admin_ids:
        await message.answer("❌ У вас нет прав для создания розыгрышей.")
        return
    
    await message.answer("🎁 Создание нового розыгрыша\n\n📝 Напишите название розыгрыша:")
    await dp.current_state(user=message.from_user.id).set_state(GiveawayStates.creating_title)

@dp.callback_query(F.data == "create_giveaway")
async def create_giveaway(callback: CallbackQuery, state: FSMContext):
    if admin_ids and callback.from_user.id not in admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    await callback.message.edit_text("📝 Напишите название розыгрыша:")
    await state.set_state(GiveawayStates.creating_title)
    await callback.answer()

@dp.message(GiveawayStates.creating_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text, creator_id=message.from_user.id)
    await state.set_state(GiveawayStates.creating_description)
    await message.answer("📄 Напишите описание розыгрыша:")

@dp.message(GiveawayStates.creating_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(GiveawayStates.creating_winners_count)
    await message.answer("🏆 Сколько будет победителей? (Напишите число):")

@dp.message(GiveawayStates.creating_winners_count)
async def process_winners_count(message: Message, state: FSMContext):
    try:
        winners_count = int(message.text)
        if winners_count < 1:
            await message.answer("❌ Количество победителей должно быть больше 0!")
            return
        await state.update_data(winners_count=winners_count)
        await state.set_state(GiveawayStates.creating_end_date)
        await message.answer("⏰ Через сколько часов завершится розыгрыш? (Напишите число):")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(GiveawayStates.creating_end_date)
async def process_end_date(message: Message, state: FSMContext):
    try:
        hours = int(message.text)
        if hours < 1:
            await message.answer("❌ Количество часов должно быть больше 0!")
            return
        
        data = await state.get_data()
        giveaway_id = f"giveaway_{len(giveaways) + 1}_{message.from_user.id}"
        
        giveaways[giveaway_id] = {
            "title": data["title"],
            "description": data["description"],
            "winners_count": data["winners_count"],
            "end_date": datetime.now() + timedelta(hours=hours),
            "participants": [],
            "winners": [],
            "creator_id": data["creator_id"],
            "created_at": datetime.now()
        }
        
        await state.clear()
        
        text = f"🎁 Розыгрыш создан!\n\n"
        text += f"📝 {data['title']}\n"
        text += f"📄 {data['description']}\n"
        text += f"🏆 Победителей: {data['winners_count']}\n"
        text += f"⏰ Завершится через {hours} часов"
        
        await message.answer(
            text,
            reply_markup=build_giveaway_keyboard(giveaway_id, message.from_user.id)
        )

@dp.callback_query(F.data.startswith("view_"))
async def view_giveaway(callback: CallbackQuery):
    giveaway_id = callback.data.split("_")[1]
    if giveaway_id not in giveaways:
        await callback.answer("❌ Розыгрыш не найден!", show_alert=True)
        return
    
    g = giveaways[giveaway_id]
    is_ended = datetime.now() > g["end_date"]
    
    text = f"🎁 {g['title']}\n\n"
    text += f"📄 {g['description']}\n\n"
    text += f"🏆 Победителей: {g['winners_count']}\n"
    text += f"👥 Участников: {len(g['participants'])}\n"
    
    if is_ended:
        if g["winners"]:
            text += f"\n🏅 Победители:\n"
            for idx, winner_id in enumerate(g["winners"], 1):
                try:
                    user = await bot.get_chat(winner_id)
                    username = user.username or f"ID: {winner_id}"
                    text += f"{idx}. @{username}\n"
                except:
                    text += f"{idx}. ID: {winner_id}\n"
        else:
            text += "\n⏰ Розыгрыш завершен, но победители еще не определены."
    else:
        time_left = g["end_date"] - datetime.now()
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        text += f"⏰ Осталось: {hours}ч {minutes}м"
    
    await callback.message.edit_text(
        text,
        reply_markup=build_giveaway_keyboard(giveaway_id, callback.from_user.id)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("participate_"))
async def participate(callback: CallbackQuery):
    giveaway_id = callback.data.split("_")[1]
    if giveaway_id not in giveaways:
        await callback.answer("❌ Розыгрыш не найден!", show_alert=True)
        return
    
    g = giveaways[giveaway_id]
    
    if datetime.now() > g["end_date"]:
        await callback.answer("❌ Розыгрыш уже завершен!", show_alert=True)
        return
    
    if callback.from_user.id in g["participants"]:
        await callback.answer("✅ Вы уже участвуете!", show_alert=True)
        return
    
    g["participants"].append(callback.from_user.id)
    await callback.answer("🎉 Вы успешно зарегистрированы на розыгрыш!", show_alert=True)
    
    text = f"🎁 {g['title']}\n\n"
    text += f"📄 {g['description']}\n\n"
    text += f"🏆 Победителей: {g['winners_count']}\n"
    text += f"👥 Участников: {len(g['participants'])}\n"
    time_left = g["end_date"] - datetime.now()
    hours = int(time_left.total_seconds() // 3600)
    minutes = int((time_left.total_seconds() % 3600) // 60)
    text += f"⏰ Осталось: {hours}ч {minutes}м"
    
    await callback.message.edit_text(
        text,
        reply_markup=build_giveaway_keyboard(giveaway_id, callback.from_user.id)
    )

@dp.callback_query(F.data.startswith("manage_"))
async def manage_giveaway(callback: CallbackQuery):
    giveaway_id = callback.data.split("_")[1]
    if giveaway_id not in giveaways:
        await callback.answer("❌ Розыгрыш не найден!", show_alert=True)
        return
    
    g = giveaways[giveaway_id]
    if callback.from_user.id != g["creator_id"] and callback.from_user.id not in admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    is_ended = datetime.now() > g["end_date"]
    
    buttons = []
    if is_ended and not g["winners"]:
        buttons.append([InlineKeyboardButton(
            text="🎲 Определить победителей",
            callback_data=f"pick_winners_{giveaway_id}"
        )])
    buttons.append([InlineKeyboardButton(
        text="📊 Статистика",
        callback_data=f"stats_{giveaway_id}"
    )])
    buttons.append([InlineKeyboardButton(
        text="🗑️ Удалить розыгрыш",
        callback_data=f"delete_{giveaway_id}"
    )])
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data=f"view_{giveaway_id}"
    )])
    
    await callback.message.edit_text(
        "🔧 Управление розыгрышем:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("pick_winners_"))
async def pick_winners(callback: CallbackQuery):
    giveaway_id = callback.data.split("_")[2]
    if giveaway_id not in giveaways:
        await callback.answer("❌ Розыгрыш не найден!", show_alert=True)
        return
    
    g = giveaways[giveaway_id]
    if callback.from_user.id != g["creator_id"] and callback.from_user.id not in admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    if datetime.now() <= g["end_date"]:
        await callback.answer("❌ Розыгрыш еще не завершен!", show_alert=True)
        return
    
    if g["winners"]:
        await callback.answer("✅ Победители уже определены!", show_alert=True)
        return
    
    if len(g["participants"]) < g["winners_count"]:
        g["winners"] = g["participants"].copy()
    else:
        g["winners"] = random.sample(g["participants"], g["winners_count"])
    
    winners_text = "🏅 Победители розыгрыша:\n\n"
    for idx, winner_id in enumerate(g["winners"], 1):
        try:
            user = await bot.get_chat(winner_id)
            username = user.username or f"ID: {winner_id}"
            winners_text += f"{idx}. @{username}\n"
            await bot.send_message(winner_id, f"🎉 Поздравляем! Вы победили в розыгрыше '{g['title']}'!")
        except:
            winners_text += f"{idx}. ID: {winner_id}\n"
    
    await callback.message.edit_text(winners_text)
    await callback.answer("✅ Победители определены!", show_alert=True)

@dp.callback_query(F.data.startswith("stats_"))
async def show_stats(callback: CallbackQuery):
    giveaway_id = callback.data.split("_")[1]
    if giveaway_id not in giveaways:
        await callback.answer("❌ Розыгрыш не найден!", show_alert=True)
        return
    
    g = giveaways[giveaway_id]
    text = f"📊 Статистика розыгрыша\n\n"
    text += f"📝 {g['title']}\n"
    text += f"👥 Участников: {len(g['participants'])}\n"
    text += f"🏆 Победителей: {len(g['winners'])}\n"
    text += f"📅 Создан: {g['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
    text += f"⏰ Завершится: {g['end_date'].strftime('%d.%m.%Y %H:%M')}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"manage_{giveaway_id}")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("delete_"))
async def delete_giveaway(callback: CallbackQuery):
    giveaway_id = callback.data.split("_")[1]
    if giveaway_id not in giveaways:
        await callback.answer("❌ Розыгрыш не найден!", show_alert=True)
        return
    
    g = giveaways[giveaway_id]
    if callback.from_user.id != g["creator_id"] and callback.from_user.id not in admin_ids:
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    del giveaways[giveaway_id]
    await callback.message.edit_text("✅ Розыгрыш удален!")
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором бота розыгрышей!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    print("🚀 Бот розыгрышей запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
