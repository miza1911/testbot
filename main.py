import os
import random
from uuid import uuid4
from dotenv import load_dotenv

from telegram import (
    InlineQueryResultPhoto,
    InputTextMessageContent,
    InlineQueryResultArticle,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)

# Загружаем .env локально, на Fly используем Secrets
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

def username_or_name(user) -> str:
    if user.username:
        return f"@{user.username}"
    name = (user.first_name or "").strip() or "Гость"
    return name

def make_caption(for_user) -> str:
    return f"{for_user} · Твое предсказание дня {random.choice(EMOJIS)}"

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    me = await context.bot.get_me()
    uname = me.username
    msg = (
        "Я отправляю картинку-предсказание с твоим именем.\n\n"
        "• Команда: /predict\n"
        f"• Inline: напиши @{uname} в любом чате."
    )
    await update.message.reply_text(msg)

async def predict_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    caption = make_caption(username_or_name(user))
    photo_url = random.choice(IMAGES)
    await update.message.reply_photo(photo=photo_url, caption=caption, parse_mode=ParseMode.HTML)

async def inline_query(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.inline_query.from_user
    caption = make_caption(username_or_name(user))
    photo_url = random.choice(IMAGES)

    result_photo = InlineQueryResultPhoto(
        id=str(uuid4()),
        photo_url=photo_url,
        thumb_url=photo_url,
        caption=caption,
        parse_mode=ParseMode.HTML,
    )

    result_article = InlineQueryResultArticle(
        id=str(uuid4()),
        title="Предсказание (текст)",
        description="Отправить подпись без картинки",
        input_message_content=InputTextMessageContent(caption),
    )

    await update.inline_query.answer([result_photo, result_article], cache_time=0, is_personal=True)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден. Укажи его через Secrets (или .env локально)")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("predict", predict_cmd))
    app.add_handler(InlineQueryHandler(inline_query))

    print("Prediction bot is running… Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=["message", "inline_query"])

if __name__ == "__main__":
    main()
