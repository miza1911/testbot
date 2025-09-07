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
    return [
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
        "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429",
    ]

IMAGES = _load_images()
PREVIEW_URL = os.getenv("PREVIEW_URL") or (IMAGES[0] if IMAGES else None)

def username_or_name(user) -> str:
    if user.username:
        return f"@{user.username}"
    name = (user.first_name or "").strip() or "Гость"
    return name

def make_caption(for_user) -> str:
    return f"{for_user} · Твое предсказание дня {random.choice(EMOJIS)}"

# /start /help
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    me = await context.bot.get_me()
    uname = me.username
    msg = (
        "Я приятный бот который умеет делать комплименты.\n\n"
        "• Команда для получения комплимента дня: /komplinos\n"
        f"• Inline в любом чате: напиши @{uname} и выбери карточку."
    )
    await update.message.reply_text(msg)

# /predict — сразу отправляем фото
async def predict_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    caption = make_caption(username_or_name(user))
    photo_url = random.choice(IMAGES)
    await update.message.reply_photo(
        photo=photo_url,
        caption=caption,
        parse_mode=ParseMode.HTML
    )

# INLINE: одна карточка с фиксированным превью, в чат уходит случайная картинка
async def inline_query(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.inline_query.from_user
    print(f"INLINE query from @{user.username or user.id}")

    caption = make_caption(username_or_name(user))
    photo_url = random.choice(IMAGES)
    thumb = PREVIEW_URL if PREVIEW_URL else photo_url

    result_photo = InlineQueryResultPhoto(
        id=str(uuid4()),
        photo_url=photo_url,
        thumbnail_url=thumb,
        caption=caption,
        parse_mode=ParseMode.HTML,
    )

    await update.inline_query.answer([result_photo], cache_time=0, is_personal=True)

def main():
    if

