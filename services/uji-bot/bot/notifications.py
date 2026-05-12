import logging
from aiogram import Bot

logger = logging.getLogger(__name__)
_bot: Bot | None = None


def set_bot(bot: Bot):
    global _bot
    _bot = bot


async def send_suggestion_to_user(telegram_id: int, incoming_message: str, result: dict):
    if not _bot:
        return

    analysis = result.get("analysis", "")
    variants = result.get("variants", [])

    text = f"💬 <b>UJI заметил:</b>\n<i>{incoming_message[:80]}{'...' if len(incoming_message) > 80 else ''}</i>\n\n"

    if analysis:
        text += f"📌 {analysis}\n\n"

    if variants:
        text += "<b>Варианты:</b>\n"
        for i, v in enumerate(variants[:3], 1):
            text += f"{i}. {v}\n"

    try:
        await _bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send suggestion to {telegram_id}: {e}")
