"""Telegram bot interface for the search agent."""

import html
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from search_agent.agent import run_agent
from settings import DAILY_QUERY_LIMIT, TELEGRAM_BOT_NAME, TELEGRAM_BOT_TOKEN
from telegram_bot.limiter import RateLimit

logger = logging.getLogger(__name__)

SECONDS_IN_DAY = 86400
limit = RateLimit(maximum=DAILY_QUERY_LIMIT, window=SECONDS_IN_DAY)


def truncate(text: str, maximum: int) -> str:
    """
    Truncate text to maximum length with ellipsis.

    >>> truncate("Hello world", 5)
    'He...'
    """
    if len(text) <= maximum:
        return text
    return text[: maximum - 3] + "..."


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming text messages.

    Checks rate limit, runs search agent, sends formatted response.
    """
    message = update.message
    if message is None:
        return
    user = update.effective_user
    if user is None:
        return
    query = message.text
    if query is None:
        return
    logger.info(f"Query from {user.id}: {query[:50]}")
    if not limit.consume(user.id):
        await message.reply_text("Лимит запросов исчерпан, попробуйте завтра")
        logger.info(f"Rate limited user {user.id}")
        return
    await message.reply_text("Ищу... Обычно поиск занимает до 1 минуты, мы пришлем вам ответ в ближайшее время")
    try:
        result = await run_agent(query)
        question = html.escape(result.response.question)
        answer = html.escape(result.response.answer)
        text = f"<b>Вопрос</b>\n{question}\n\n<b>Ответ</b>\n{answer}\n\n{TELEGRAM_BOT_NAME}"
        await message.reply_html(truncate(text, 4000))
        logger.info(f"Response sent to {user.id}")
    except Exception as error:
        logger.exception(f"Agent error for user {user.id}")
        await message.reply_text(f"Ошибка поиска: {error}")


def main() -> None:
    """Start the Telegram bot with polling."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    logger.info("Starting Telegram bot")
    app.run_polling()


if __name__ == "__main__":
    main()
