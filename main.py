import os
import random
from dotenv import load_dotenv
from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)
from uuid import uuid4

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

HELP_TEXT = (
    "Я кидаю число от 1 до 5.\n"
    "• Команда: /roll\n"
    "• Inline: напишите @%s в любом чате и нажмите карточку."
)

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = (await context.bot.get_me()).username
    await update.message.reply_text(
        HELP_TEXT % bot_username,
        parse_mode=ParseMode.HTML
    )

def roll_once() -> int:
    return random.randint(1, 5)

async def roll_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    """Отвечает числом 1..5 на команду /roll."""
    n = roll_once()
    await update.message.reply_text(str(n))

async def inline_query(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Inline-режим: пользователь пишет @botname в любом чате.
    Показываем карточку-описание; по нажатию отправляем число (1..5).
    """
    query = update.inline_query.query  # не используем, но можно расширять логику
    n = roll_once()

    # Карточка, которая будет видна во всплывающем списке
    title = f"Кинуть число 1–5 → {n}"
    description = "Нажмите, чтобы отправить случайное число как при /roll"

    result = InlineQueryResultArticle(
        id=str(uuid4()),
        title=title,
        description=description,
        input_message_content=InputTextMessageContent(str(n)),
    )

    # cache_time=0 — чтобы при каждом вызове был новый рандом
    await update.inline_query.answer([result], cache_time=0, is_personal=True)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден. Укажите его в .env или переменных окружения.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("roll", roll_cmd))
    app.add_handler(InlineQueryHandler(inline_query))

    # Простая long-polling версия
    print("Bot is running… Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=["message", "inline_query"])

if __name__ == "__main__":
    main()
