import os
import random
from uuid import uuid4
from dotenv import load_dotenv

from telegram import InlineQueryResultPhoto
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)

# Для локалки читаем .env; на Fly используем Secrets
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
EMOJIS = ["✨", "🌟", "🍀", "🌈", "💫", "🧿", "🪄", "🎉", "☀️", "🌸"]

def _load_images():
    env = (os.getenv("IMAGES") or "").strip()
    if env:
        return [u.strip() for u in env.split(",") if u.strip()]
    # запасные, лучше задать свои через IMAGES
    return [
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
        "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429",
    ]

IMAGES = _load_images()

# Превью для всплывающего окна: можно задать секретом PREVIEW_URL,
# иначе возьмём первую картинку из IMAGES.
PREVIEW_URL = os.getenv("PREVIEW_URL") or (IMAGES[0] if IMAGES else None)

def username_or_name(user) -> str:
    if user.username:
        return f"@{user.username}"
    name = (user.first_name or "").strip() or "Гость"
    return name

def make_caption(for_user) -> str:
    return f"{for_user} · Твое предсказание дня {random.choice(EMOJIS)}"

# /start /help  — оставил твой текст как есть, только убрал незавершённую f-строку
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    me = await context.bot.get_me()
    uname = me.username  # можешь использовать в будущем, если захочешь дописать строку про inline
    msg = (
        "Я приятный бот который умеет делать комплименты.\n\n"
        "• Команда для получения комплимента дня: /komplinos\n"
    )
    await update.message.reply_text(msg)

# Общая отправка картинки с подписью
async def _send_prediction(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    caption = make_caption(username_or_name(user))
    photo_url = random.choice(IMAGES)
    await update.message.reply_photo(photo=photo_url, caption=caption, parse_mode=ParseMode.HTML)

# /predict — на всякий случай оставим
async def predict_cmd(update, context: ContextTypes.DEFAULT_TY
