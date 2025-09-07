import os
import random
from uuid import uuid4
from dotenv import load_dotenv

from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InputMediaPhoto,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    ChosenInlineResultHandler,
)

# .env только локально; на Fly используем Secrets
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
EMOJIS = ["✨", "🌟", "🍀", "🌈", "💫", "🧿", "🪄", "🎉", "☀️", "🌸"]

def _load_images():
    env = (os.getenv("IMAGES") or "").strip()
    if env:
        return [u.strip() for u in env.split(",") if u.strip()]
    # запасные картинки, если IMAGES не задан
    return [
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
        "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429",
    ]

IMAGES = _load_images()
PREVIEW_URL = os.getenv("PREVIEW_URL") or IMAGES[0]  # фиксированное превью в инлайн-окне

def username_or_name(user) -> str:
    if user.username:
        return f"@{user.username}"
    name = (user.first_name or "").strip() or "Гость"
    return name

def make_caption(for_user) -> str:
    return f"{for_user} · Твое предсказание дня {random.choice(EMOJIS)}"

def pick_random_photo() -> str:
    return random.choice(IMAGES)

# /start /help
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    me = await context.bot.get_me()
    uname = me.username
    msg = (
        f"Я отправляю картинку-предсказание с твоим именем.\n\n"
        f"• Команда: /predict\n"
        f"• Inline в любом чате: напиши @{uname} и выбери карточку."
    )
    await update.message.reply_text(msg)

# /predict — сразу присылаем фото
async def predict_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    caption = make_caption(username_or_name(user))
    photo_url = pick_random_photo()
    await update.message.reply_photo(photo=photo_url, caption=caption, parse_mode=ParseMode.HTML)

# --- Inline ---
ARTICLE_ID = "predict_inline"

# 1) показываем одну плитку с твоим превью (PREVIEW_URL)
async def inline_query(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.inline_query.from_user
    print(f"INLINE query from @{user.username or user.id}")

    result = InlineQueryResultArticle(
        id=ARTICLE_ID,
        title="Получить предсказание",
        description="Нажми — и придет твое предсказание дня!",
        input_message_content=InputTextMessageContent("⏳ Получаю предсказание…"),
        thumbnail_url=PREVIEW_URL,  # ВСЕГДА одно превью из секрета
    )

    await update.inline_query.answer([result], cache_time=0, is_personal=True)

# 2) по нажатию заменяем текст на фото (эффект «как команда /predict»)
async def on_chosen_inline(update, context: ContextTypes.DEFAULT_TYPE):
    chosen = update.chosen_inline_result
    if not chosen or chosen.result_id != ARTICLE_ID:
        return
    if not chosen.inline_message_id:
        # редкий случай — id нет, тогда ничего не делаем
        print("chosen_inline_result: no inline_message_id; skip edit")
        return

    user = chosen.from_user
    caption = make_caption(username_or_name(user))
    photo_url = pick_random_photo()

    try:
        await context.bot.edit_message_media(
            inline_message_id=chosen.inline_message_id,
            media=InputMediaPhoto(media=photo_url, caption=caption, parse_mode=ParseMode.HTML),
        )
    except Exception as e:
        print(f"edit_message_media failed: {e}")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден. Добавь его в Secrets на Fly")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("predict", predict_cmd))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(ChosenInlineResultHandler(on_chosen_inline))  # <-- обязателен

    print("Prediction bot is running…")
    app.run_polling(allowed_updates=["message", "inline_query", "chosen_inline_result"])

if __name__ == "__main__":
    main()
