
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import json
import os

# ======== Хранилище звёзд ========
if os.path.exists("stars.json"):
    with open("stars.json", "r") as f:
        user_stars = json.load(f)
else:
    user_stars = {}

# ======== Функции ========
def save_stars():
    with open("stars.json", "w") as f:
        json.dump(user_stars, f)

def get_user_id(user):
    return str(user.id)

def get_stars(user_id):
    return user_stars.get(user_id, 0)

def add_stars(user_id, amount):
    user_stars[user_id] = get_stars(user_id) + amount
    save_stars()

def deduct_stars(user_id, amount):
    if get_stars(user_id) >= amount:
        user_stars[user_id] -= amount
        save_stars()
        return True
    return False

# ======== Команды ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = get_user_id(update.effective_user)
    if user_id not in user_stars:
        add_stars(user_id, 20)  # стартовые звёзды
    await update.message.reply_text(f"Привет! У тебя {get_stars(user_id)} ⭐")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = get_user_id(update.effective_user)
    await update.message.reply_text(f"У тебя {get_stars(user_id)} ⭐")

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id in [admin.user.id async for admin in await update.effective_chat.get_administrators()]:
        await update.message.reply_text("Только админ может выдавать звёзды.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Используй: /give @username 50")
        return

    try:
        username = context.args[0].replace("@", "")
        amount = int(context.args[1])
        members = await update.effective_chat.get_members()
        for member in members:
            if member.user.username == username:
                user_id = get_user_id(member.user)
                add_stars(user_id, amount)
                await update.message.reply_text(f"Выдано {amount} ⭐ пользователю @{username}")
                return
        await update.message.reply_text("Пользователь не найден в чате.")
    except:
        await update.message.reply_text("Ошибка. Проверь формат.")

# ======== Обработка сообщений ========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = get_user_id(update.effective_user)

    if deduct_stars(user_id, 10):
        await update.message.reply_text(f"−10 ⭐. Осталось {get_stars(user_id)}.")
    else:
        await update.message.delete()
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="У тебя недостаточно звёзд, чтобы отправить сообщение. Нужно 10 ⭐."
            )
        except:
            pass

# ======== Запуск ========
app = ApplicationBuilder().token("ВАШ_ТОКЕН_БОТА").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("give", give))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

app.run_polling()
