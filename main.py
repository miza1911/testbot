import os
import random
from uuid import uuid4
from dotenv import load_dotenv

from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    ChosenInlineResultHandler,
    CallbackQueryHandler,
)

# .env — только для локали; на Fly используем Secrets
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
EMOJIS = ["✨", "🌟", "🍀", "🌈", "💫", "🧿", "🪄", "🎉", "☀️", "🌸"]

PIN_USER  = (os.getenv("PIN_USER") or "").strip().lstrip("@").lower()
PIN_MEDIA = (os.getenv("PIN_MEDIA") or "").strip()
OWNER_ID  = int(os.getenv("OWNER_ID", "0"))

PIN_MEDIA_ID: str | None = None  # сюда положим file_id после прогрева (если PIN_MEDIA был URL)

def _load_images():
    env = (os.getenv("IMAGES") or "").strip()
    if env:
        return [u.strip() for u in env.split(",") if u.strip()]
    return [
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
        "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429",
    ]

IMAGES = _load_images()
PREVIEW_URL = os.getenv("PREVIEW_URL") or IMAGES[0]

# >>> added: helpers for inline pin
async def warmup_cache(app: Application):
    """Если PIN_MEDIA это URL — один раз шлём его себе/в служебный канал и сохраняем file_id."""
    global PIN_MEDIA_ID
    if OWNER_ID and PIN_MEDIA and PIN_MEDIA.startswith("http"):
        try:
            msg = await app.bot.send_photo(
                chat_id=OWNER_ID,
                photo=PIN_MEDIA,
                disable_notification=True,
                protect_content=True,
            )
            PIN_MEDIA_ID = msg.photo[-1].file_id
            print("Pinned image warmed -> file_id saved")
        except Exception as e:
            print(f"warmup pinned failed: {e}")

def _is_pinned_username(uname: str | None) -> bool:
    return bool(PIN_USER) and (uname or "").strip().lstrip("@").lower() == PIN_USER

def _pinned_media() -> str | None:
    # отдаём быстрый file_id, если прогрели; иначе то, что есть
    return PIN_MEDIA_ID or (PIN_MEDIA or None)
# <<< added

def username_or_name(user) -> str:
    if user.username:
        return f"@{user.username}"
    name = (user.first_name or "").strip() or "Гость"
    return name

def make_caption(for_user) -> str:
    return f"{for_user} · Твой комплимент дня! {random.choice(EMOJIS)}"

def pick_random_photo() -> str:
    # лёгкий анти-повтор: не возвращаем один и тот же URL дважды подряд
    last = getattr(pick_random_photo, "_last", None)
    pool = [u for u in IMAGES if u != last] or IMAGES
    url = random.choice(pool)
    pick_random_photo._last = url
    return url

# /start /help
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    me = await context.bot.get_me()
    uname = me.username
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
ARTICLE_ID = "predict_inline"
BTN_PAYLOAD = "go_predict"

# 1) Во всплывающем окне показываем ОДНУ карточку с фиксированным превью
async def inline_query(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.inline_query.from_user
    print(f"INLINE query from @{user.username or user.id}")

    # >>> added: персонализируем превью для закреплённого пользователя (если PIN_MEDIA — URL)
    thumb = PREVIEW_URL
    if _is_pinned_username(getattr(user, "username", None)):
        pm = _pinned_media()
        if pm and isinstance(pm, str) and pm.startswith("http"):
            thumb = pm
    # <<< added

    result = InlineQueryResultArticle(
        id=ARTICLE_ID,
        title="Получить комплимент дня!🎉",
        description="Нажми — и придет твой комплимент!",
        input_message_content=InputTextMessageContent("⏳ Получаю комплимент…"),
        thumbnail_url=thumb,  # фиксированное/персональное превью
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Получить сейчас", callback_data=BTN_PAYLOAD)]]
        ),
    )
    await update.inline_query.answer([result], cache_time=0, is_personal=True)

# 2А) Нормальный путь: Telegram прислал chosen_inline_result → заменяем текст на фото (1 тап)
async def on_chosen_inline(update, context: ContextTypes.DEFAULT_TYPE):
    chosen = update.chosen_inline_result
    if not chosen or chosen.result_id != ARTICLE_ID:
        return
    if not chosen.inline_message_id:
        print("chosen_inline_result: no inline_message_id; skip edit")
        return

    user = chosen.from_user
    caption = make_caption(username_or_name(user))
    photo_url = pick_random_photo()

    # >>> added: если это закреплённый пользователь — подменяем на PIN_MEDIA
    if _is_pinned_username(getattr(user, "username", None)):
        pm = _pinned_media()
        if pm:
            photo_url = pm
    # <<< added

    try:
        await context.bot.edit_message_media(
            inline_message_id=chosen.inline_message_id,
            media=InputMediaPhoto(media=photo_url, caption=caption, parse_mode=ParseMode.HTML),
            reply_markup=None,  # уберём кнопку, если была
        )
    except Exception as e:
        print(f"edit_message_media (chosen) failed: {e}")

# 2Б) Запасной путь: если chosen_inline_result не пришёл — жмём кнопку «Получить сейчас»
async def on_callback(update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or q.data != BTN_PAYLOAD:
        return

    user = q.from_user
    caption = make_caption(username_or_name(user))
    photo_url = pick_random_photo()

    # >>> added: пин только для инлайна — кнопка тоже относится к инлайн-сообщению
    if _is_pinned_username(getattr(user, "username", None)):
        pm = _pinned_media()
        if pm:
            photo_url = pm
    # <<< added

    try:
        await q.edit_message_media(
            media=InputMediaPhoto(media=photo_url, caption=caption, parse_mode=ParseMode.HTML)
        )
    except Exception as e:
        print(f"edit_message_media (callback) failed: {e}")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден. Добавь его в Secrets на Fly")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler(["nos", "predict"], predict_cmd))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(ChosenInlineResultHandler(on_chosen_inline))     # 1-тап сценарий
    app.add_handler(CallbackQueryHandler(on_callback))               # запасной сценарий

    # >>> added: прогрев pinned-URL до file_id (если задан OWNER_ID)
    async def _startup(app_: Application):
        await warmup_cache(app_)
        print("Startup warmup done")
    app.post_init = _startup
    # <<< added

    print("Prediction bot is running…")
    app.run_polling(allowed_updates=["message", "inline_query", "chosen_inline_result", "callback_query"])

if __name__ == "__main__":
    main()
