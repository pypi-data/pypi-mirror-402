import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

admin_ids = []
banned_words = []
muted_users = {}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "🛡️ Бот модератор для групп и каналов!\n\n"
            "Добавьте бота в группу и дайте права администратора.\n"
            "Используйте /help для списка команд."
        )
    else:
        await message.answer("🛡️ Бот модератор активирован!")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    if message.from_user.id not in admin_ids and admin_ids:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    help_text = "🛡️ Команды модератора:\n\n"
    help_text += "/ban <user_id> - Забанить пользователя\n"
    help_text += "/unban <user_id> - Разбанить пользователя\n"
    help_text += "/mute <user_id> <минуты> - Заглушить пользователя\n"
    help_text += "/unmute <user_id> - Снять заглушку\n"
    help_text += "/addword <слово> - Добавить запрещенное слово\n"
    help_text += "/delword <слово> - Удалить запрещенное слово\n"
    help_text += "/stats - Статистика модерации"
    
    await message.answer(help_text)

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    if message.from_user.id not in admin_ids and admin_ids:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = int(message.text.split()[1])
        except (IndexError, ValueError):
            await message.answer("❌ Использование: /ban <user_id> или ответьте на сообщение")
            return
    
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.answer(f"✅ Пользователь {user_id} забанен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command("unban"))
async def cmd_unban(message: Message):
    if message.from_user.id not in admin_ids and admin_ids:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    try:
        user_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /unban <user_id>")
        return
    
    try:
        await bot.unban_chat_member(message.chat.id, user_id)
        await message.answer(f"✅ Пользователь {user_id} разбанен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command("mute"))
async def cmd_mute(message: Message):
    if message.from_user.id not in admin_ids and admin_ids:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    try:
        parts = message.text.split()
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            minutes = int(parts[1]) if len(parts) > 1 else 60
        else:
            user_id = int(parts[1])
            minutes = int(parts[2]) if len(parts) > 2 else 60
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /mute <user_id> <минуты>")
        return
    
    from datetime import datetime, timedelta
    muted_users[user_id] = datetime.now() + timedelta(minutes=minutes)
    
    try:
        await bot.restrict_chat_member(
            message.chat.id,
            user_id,
            can_send_messages=False
        )
        await message.answer(f"✅ Пользователь {user_id} заглушен на {minutes} минут!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command("unmute"))
async def cmd_unmute(message: Message):
    if message.from_user.id not in admin_ids and admin_ids:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    try:
        user_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /unmute <user_id>")
        return
    
    if user_id in muted_users:
        del muted_users[user_id]
    
    try:
        await bot.restrict_chat_member(
            message.chat.id,
            user_id,
            can_send_messages=True
        )
        await message.answer(f"✅ Заглушка снята с пользователя {user_id}!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command("addword"))
async def cmd_addword(message: Message):
    if message.from_user.id not in admin_ids and admin_ids:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    try:
        word = message.text.split(maxsplit=1)[1].lower()
        if word not in banned_words:
            banned_words.append(word)
            await message.answer(f"✅ Слово '{word}' добавлено в список запрещенных!")
        else:
            await message.answer("ℹ️ Это слово уже в списке!")
    except IndexError:
        await message.answer("❌ Использование: /addword <слово>")

@dp.message(Command("delword"))
async def cmd_delword(message: Message):
    if message.from_user.id not in admin_ids and admin_ids:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    try:
        word = message.text.split(maxsplit=1)[1].lower()
        if word in banned_words:
            banned_words.remove(word)
            await message.answer(f"✅ Слово '{word}' удалено из списка!")
        else:
            await message.answer("❌ Слово не найдено в списке!")
    except IndexError:
        await message.answer("❌ Использование: /delword <слово>")

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id not in admin_ids and admin_ids:
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    text = f"📊 Статистика модерации\n\n"
    text += f"🚫 Запрещенных слов: {len(banned_words)}\n"
    text += f"🔇 Заглушенных пользователей: {len(muted_users)}\n"
    
    await message.answer(text)

@dp.message(F.text)
async def check_banned_words(message: Message):
    if message.chat.type == "private":
        return
    
    if message.from_user.id in admin_ids:
        return
    
    text_lower = message.text.lower() if message.text else ""
    for word in banned_words:
        if word in text_lower:
            try:
                await message.delete()
                await message.answer(f"⚠️ Сообщение удалено: использование запрещенного слова")
            except:
                pass
            break

async def check_muted_users():
    from datetime import datetime
    while True:
        await asyncio.sleep(60)
        now = datetime.now()
        expired = [uid for uid, mute_time in muted_users.items() if mute_time <= now]
        for uid in expired:
            del muted_users[uid]

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
        await bot.send_message(new_admin_id, "🎉 Вы стали администратором бота модератора!")
    else:
        await message.answer("ℹ️ Этот пользователь уже является администратором.")

async def main():
    if not admin_ids:
        print("⚠️  Внимание: Не указаны администраторы!")
        print("   Используйте команду /addadmin <user_id> после запуска бота")
    
    asyncio.create_task(check_muted_users())
    print("🚀 Бот модератор запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
