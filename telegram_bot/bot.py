"""Telegram bot interface for the search agent."""

import html
import logging
import random

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from search_agent.agent import run_agent
from settings import DAILY_QUERY_LIMIT, TELEGRAM_BOT_NAME, TELEGRAM_BOT_TOKEN
from telegram_bot.limiter import RateLimit

logger = logging.getLogger(__name__)

SECONDS_IN_DAY = 86400
LOADING_GIFS = (
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExem01bDlpZWZtOGYzZmQzenExNDdvZXkya2J3bWw1c3d2a3dxeWR6biZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/pY8jLmZw0ElqvVeRH4/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHkwMDduMnlwOGsyMWhyOG1pajAwbG14MXd6bWR2MzFnYXM1aHdtcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/KbdF8DCgaoIVC8BHTK/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHkwMDduMnlwOGsyMWhyOG1pajAwbG14MXd6bWR2MzFnYXM1aHdtcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/shIRdgYzujbZC/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHkwMDduMnlwOGsyMWhyOG1pajAwbG14MXd6bWR2MzFnYXM1aHdtcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/rakaIgs2Przyw/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHkwMDduMnlwOGsyMWhyOG1pajAwbG14MXd6bWR2MzFnYXM1aHdtcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/13eGrcwhTYEADu/giphy.gif",
    # dogs
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjNqbG0zbXR4eDg2dDBic2RzbjY3YjZ2cGkwdHg2MTdxZ3U2dDBvMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/hcZZmrMHsUSNG/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjNqbG0zbXR4eDg2dDBic2RzbjY3YjZ2cGkwdHg2MTdxZ3U2dDBvMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/UKkes2qN2T70s/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjNqbG0zbXR4eDg2dDBic2RzbjY3YjZ2cGkwdHg2MTdxZ3U2dDBvMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/fDdVNus5ztt7O/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjNqbG0zbXR4eDg2dDBic2RzbjY3YjZ2cGkwdHg2MTdxZ3U2dDBvMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/55xOFYyREnNPW/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3bGhnOXJydWg3Zm90Nml4c2wwdm10Nno3YTZmN2RmNGFpdHZuYTRzcCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/XkxfezUB7Rj4k/giphy.gif",    
)
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
    loading = await message.reply_animation(random.choice(LOADING_GIFS), caption="Ищу... Обычно поиск занимает до 1 минуты")
    try:
        result = await run_agent(query)
        question = html.escape(result.response.question)
        answer = result.response.answer
        text = f"<b>Вопрос</b>\n{question}\n\n<b>Ответ</b>\n{answer}\n\n{TELEGRAM_BOT_NAME}"
        await loading.delete()
        await message.reply_html(truncate(text, 4000))
        logger.info(f"Response sent to {user.id}")
    except Exception as error:
        logger.exception(f"Agent error for user {user.id}")
        await loading.delete()
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
