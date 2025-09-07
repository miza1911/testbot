import os
import random
from uuid import uuid4
from dotenv import load_dotenv

# --- импорты (убрал дубли) ---
from telegram import InlineQueryResultArticle, InputTextMessageContent, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    ChosenInlineResultHandler,
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

# /start /help
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    me = await context.bot.get_me()
    uname = me.username
    msg = (
        "Я приятный бот который умеет делать комплименты.\n\n"
        "• Команда для получения комплимента дня: /komplinos\n"
        
    )
    await update.message.reply_text(msg)

# общая функция отправки картинки-предсказания
async def _send_prediction(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    caption = make_caption(username_or_name(user))
    photo_url = random.choice(IMAGES)
    await update.message.reply_photo(photo=photo_url, caption=caption, parse_mode=ParseMode.HTML)

# /predict — оставил для совместимости (если ты её уже пробовал)
async def predict_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await _send_prediction(update, context)

# /komplinos — команда из твоего описания
async def komplinos_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await _send_prediction(update, context)

# INLINE: одна текстовая плитка с постоянной миниатюрой (превью), при клике — рандомное фото
ARTICLE_ID = "predict_inline"

async def inline_query(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.inline_query.from_user
    print(f"INLINE query from @{user.username or user.id}")

    result_article = InlineQueryResultArticle(
        id=ARTICLE_ID,
        title="Получить предсказание",
        description="Нажми — и получишь комплимент дня!",
        input_message_content=InputTextMessageContent("⏳ Получаю предсказание…"),
        thumbnail_url=PREVIEW_URL if PREVIEW_URL else None,  # одна и та же картинка во всплывашке
    )

    await update.inline_query.answer([result_article], cache_time=0, is_personal=True)

# Когда пользователь выбрал плитку — заменяем текст на случайное фото
async def on_chosen_inline(update, context: ContextTypes.DEFAULT_TYPE):
    chosen = update.chosen_inline_result
    if not chosen or chosen.result_id != ARTICLE_ID:
        return

    inline_msg_id = chosen.inline_message_id
    user = chosen.from_user
    caption = make_caption(username_or_name(user))
    photo_url = random.choice(IMAGES)

    try:
        await context.bot.edit_message_media(
            inline_message_id=inline_msg_id,
            media=InputMediaPhoto(media=photo_url, caption=caption, parse_mode=ParseMode.HTML),
        )
        print(f"INLINE converted to random photo for @{user.username or user.id}")
    except Exception as e:
        print(f"edit_message_media failed: {e}")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден. Добавь его в Secrets на Fly")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("predict", predict_cmd))     # совместимость
    app.add_handler(CommandHandler("komplinos", komplinos_cmd)) # твоя команда из описания
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(ChosenInlineResultHandler(on_chosen_inline))

    print("Prediction bot is running…")
    app.run_polling(allowed_updates=["message", "inline_query", "chosen_inline_result"])

if __name__ == "__main__":
    main()
