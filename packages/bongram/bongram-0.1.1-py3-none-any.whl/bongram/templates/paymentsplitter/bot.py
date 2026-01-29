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

bills = {}

class PaymentStates(StatesGroup):
    creating_amount = State()
    adding_participants = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Создать счет", callback_data="create_bill")],
        [InlineKeyboardButton(text="📋 Мои счета", callback_data="my_bills")]
    ])
    
    await message.answer(
        "💰 Добро пожаловать в разделитель счетов!\n\n"
        "Создавайте счета и делите их между участниками.",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "create_bill")
async def create_bill(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("💰 Напишите сумму счета:")
    await state.set_state(PaymentStates.creating_amount)
    await callback.answer()

@dp.message(PaymentStates.creating_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0!")
            return
        
        await state.update_data(amount=amount, creator_id=message.from_user.id, participants=[])
        await state.set_state(PaymentStates.adding_participants)
        await message.answer(
            "👥 Отправьте user_id участников, каждый с новой строки.\n"
            "Или отправьте /done для завершения."
        )
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(PaymentStates.adding_participants)
async def process_participants(message: Message, state: FSMContext):
    if message.text == "/done":
        data = await state.get_data()
        participants = data.get("participants", [])
        
        if not participants:
            await message.answer("❌ Добавьте хотя бы одного участника!")
            return
        
        bill_id = f"bill_{len(bills) + 1}_{message.from_user.id}"
        amount = data["amount"]
        per_person = amount / len(participants)
        
        bills[bill_id] = {
            "amount": amount,
            "per_person": per_person,
            "participants": participants,
            "creator_id": data["creator_id"],
            "created_at": datetime.now(),
            "paid": {pid: False for pid in participants}
        }
        
        text = f"✅ Счет создан!\n\n"
        text += f"💰 Сумма: {amount} руб.\n"
        text += f"👥 Участников: {len(participants)}\n"
        text += f"💵 С каждого: {per_person:.2f} руб.\n\n"
        text += "Участники:\n"
        for idx, pid in enumerate(participants, 1):
            text += f"{idx}. ID: {pid}\n"
        
        await message.answer(text)
        
        for pid in participants:
            try:
                await bot.send_message(
                    pid,
                    f"💰 Вам пришел счет на {per_person:.2f} руб.\n"
                    f"Используйте /pay {bill_id} для оплаты"
                )
            except:
                pass
        
        await state.clear()
    else:
        try:
            user_ids = [int(uid.strip()) for uid in message.text.split("\n") if uid.strip()]
            data = await state.get_data()
            participants = data.get("participants", [])
            participants.extend(user_ids)
            await state.update_data(participants=participants)
            await message.answer(f"✅ Добавлено {len(user_ids)} участников. Всего: {len(participants)}\nОтправьте /done для завершения.")
        except ValueError:
            await message.answer("❌ Введите user_id (числа), каждый с новой строки!")

@dp.callback_query(F.data == "my_bills")
async def my_bills(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_bills = []
    
    for bill_id, bill in bills.items():
        if bill["creator_id"] == user_id or user_id in bill["participants"]:
            user_bills.append((bill_id, bill))
    
    if not user_bills:
        await callback.message.edit_text(
            "📋 У вас нет счетов.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 Создать", callback_data="create_bill")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")]
            ])
        )
        await callback.answer()
        return
    
    buttons = []
    for bill_id, bill in user_bills[:10]:
        status = "✅" if all(bill["paid"].values()) else "⏳"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {bill['amount']} руб. ({len(bill['participants'])} чел.)",
            callback_data=f"view_bill_{bill_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")])
    
    await callback.message.edit_text(
        "📋 Ваши счета:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("view_bill_"))
async def view_bill(callback: CallbackQuery):
    bill_id = callback.data.split("_")[2]
    if bill_id not in bills:
        await callback.answer("❌ Счет не найден!", show_alert=True)
        return
    
    bill = bills[bill_id]
    text = f"💰 Счет\n\n"
    text += f"Сумма: {bill['amount']} руб.\n"
    text += f"С каждого: {bill['per_person']:.2f} руб.\n\n"
    text += "Участники:\n"
    
    for pid in bill["participants"]:
        status = "✅" if bill["paid"][pid] else "❌"
        text += f"{status} ID: {pid}\n"
    
    if all(bill["paid"].values()):
        text += "\n✅ Все оплатили!"
    
    await callback.message.edit_text(text)
    await callback.answer()

@dp.message(Command("pay"))
async def cmd_pay(message: Message):
    try:
        bill_id = message.text.split()[1]
    except IndexError:
        await message.answer("❌ Использование: /pay <bill_id>")
        return
    
    if bill_id not in bills:
        await message.answer("❌ Счет не найден!")
        return
    
    bill = bills[bill_id]
    user_id = message.from_user.id
    
    if user_id not in bill["participants"]:
        await message.answer("❌ Вы не участник этого счета!")
        return
    
    if bill["paid"][user_id]:
        await message.answer("ℹ️ Вы уже оплатили этот счет!")
        return
    
    bill["paid"][user_id] = True
    await message.answer(f"✅ Вы оплатили {bill['per_person']:.2f} руб.!")
    
    if all(bill["paid"].values()):
        await bot.send_message(
            bill["creator_id"],
            "✅ Все участники оплатили счет!"
        )

@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Создать счет", callback_data="create_bill")],
        [InlineKeyboardButton(text="📋 Мои счета", callback_data="my_bills")]
    ])
    
    await callback.message.edit_text(
        "💰 Выберите действие:",
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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором разделителя счетов!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    print("🚀 Разделитель счетов запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
