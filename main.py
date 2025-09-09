import os
import random
from dotenv import load_dotenv

from telegram import (
    InlineQueryResultPhoto,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)

# .env — только для локали; на Fly используем Secrets
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
EMOJIS = ["✨", "🌟", "🍀", "🌈", "💫", "🧿", "🪄", "🎉", "☀️", "🌸"]

def _load_images():
    env = (os.getenv("IMAGES") or "").strip()
    if env:
        return [u.strip() for u in env.split(",") if u.strip()]
    # Желательно давать прямые ссылки на изображения. Unsplash работает, но можно добавить параметры.
    return [
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
        "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429",
    ]

IMAGES = _load_images()
PREVIEW_URL = os.getenv("PREVIEW_URL") or IMAGES[0]

def username_or_name(user) -> str:
    if user.username:
        return f"@{user.username}"
    name = (user.first_name or "").strip() or "Гость"
    return name

def make_caption(for_user) -> str:
    import random
    return f"{for_user} · Твой комплимент дня! {random.choice(EMOJIS)}"

def pick_random_photo() -> str:
    import random
    last = getattr(pick_random_photo, "_last", None)
    pool = [u for u in IMAGES if u != last] or IMAGES
    url = random.choice(pool)
    pick_random_photo._last = url
    return url

# /start /help
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "Привет, салам, бонжур! Я умею делать комплименты. Счастья, здоровья!🌸 \n\n"
        "• Для получения комплимента: /nos\n"
    )
    await update.message.reply_text(msg)

# /predict — сразу отправляем фото
async def predict_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    caption = make_caption(username_or_name(user))
    photo_url = pick_random_photo()
    await update.message.reply_photo(photo=photo_url, caption=caption, parse_mode=ParseMode.HTML)

# ---------- INLINE ----------
ARTICLE_ID = "predict_inline_photo"

async def inline_query(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.inline_query.from_user
    print(f"INLINE query from @{user.username or user.id}")

    photo_url = pick_random_photo()
    caption = make_caption(username_or_name(user))

    # Сразу отдаём фото — без «получаю…» и без кнопок
    result = InlineQueryResultPhoto(
        id=ARTICLE_ID,
        photo_url=photo_url,
        thumbnail_url=PREVIEW_URL,
        caption=caption,
        parse_mode=ParseMode.HTML,
        title="Получить комплимент дня! 🎉",  # заголовок карточки в списке
        description="Нажми — и сразу придёт комплимент",
    )
    await update.inline_query.answer([result], cache_time=0, is_personal=True)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден. Добавь его в Secrets на Fly")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler(["nos", "predict"], predict_cmd))
    app.add_handler(InlineQueryHandler(inline_query))

    print("Prediction bot is running…")
    app.run_polling(allowed_updates=["message", "inline_query"])

if __name__ == "__main__":
    main()

