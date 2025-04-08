import logging
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

# === Конфигурация ===
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
COST_PER_MESSAGE = 10

# Простая база: user_id -> звёзды
user_stars = {}

# === Логгирование ===
logging.basicConfig(level=logging.INFO)

# === Инициализация ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# === Команда /start ===
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_stars.setdefault(user_id, 30)  # Начальные звезды
    await message.answer(f"Привет! У тебя {user_stars[user_id]}⭐. Отправка сообщений в группу стоит {COST_PER_MESSAGE}⭐.")

# === Команда /help ===
@dp.message_handler(commands=["help"])
async def help_handler(message: types.Message):
    help_text = """
Команды:
/start — начать и узнать баланс
/help — помощь
/addstars ID КОЛ-ВО — (только админ)
"""
    await message.answer(help_text)

# === Пополнение звёзд (только для админа) ===
@dp.message_handler(commands=["addstars"])
async def add_stars_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Только для администратора.")

    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = int(amount)
        user_stars[uid] = user_stars.get(uid, 0) + amount
        await message.answer(f"✅ Пользователю {uid} добавлено {amount}⭐. Сейчас: {user_stars[uid]}⭐")
    except Exception:
        await message.reply("⚠️ Используй: /addstars [ID] [кол-во]")

# === Пользователь хочет отправить сообщение в группу ===
@dp.message_handler(lambda m: not m.text.startswith("/"))
async def send_to_group_handler(message: types.Message):
    user_id = message.from_user.id
    stars = user_stars.get(user_id, 0)

    if stars < COST_PER_MESSAGE:
        return await message.reply(f"❌ Недостаточно звёзд! У тебя {stars}⭐, нужно {COST_PER_MESSAGE}⭐.")

    # Успешно списываем
    user_stars[user_id] -= COST_PER_MESSAGE

    # Пример — пересылаем сообщение в группу
    GROUP_ID = int(os.getenv("GROUP_ID"))
    await bot.send_message(GROUP_ID, f"Сообщение от @{message.from_user.username} (⭐ осталось: {user_stars[user_id]}):\n{message.text}")
    await message.reply(f"✅ Сообщение отправлено! У тебя осталось {user_stars[user_id]}⭐.")

# === Запуск ===
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
