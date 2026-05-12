import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
    tone = result.get("tone", "")

    tone_map = {
        "cold": "❄️ холодно",
        "neutral": "😐 нейтрально",
        "warm": "🤝 тепло",
        "tense": "⚡ напряжение",
        "flirty": "😏 флирт",
    }
    tone_label = tone_map.get(tone, tone)

    preview = incoming_message[:80] + ("..." if len(incoming_message) > 80 else "")
    text = f"💬 <b>Новое сообщение:</b>\n<i>«{preview}»</i>"

    if tone_label:
        text += f"\n\n🏷 {tone_label}"

    if analysis:
        text += f"\n\n📌 {analysis}"

    if variants:
        text += "\n\n<b>Варианты ответа:</b>"
        for i, v in enumerate(variants[:3], 1):
            text += f"\n{i}. {v}"

    # Build inline keyboard — one button per variant to copy
    buttons = []
    for i, v in enumerate(variants[:3], 1):
        buttons.append([
            InlineKeyboardButton(
                text=f"📋 Скопировать вариант {i}",
                callback_data=f"copy:{i}:{telegram_id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

    try:
        await _bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to send suggestion to {telegram_id}: {e}")


# Store last variants per user for copy callbacks
_last_variants: dict[int, list[str]] = {}


def store_variants(telegram_id: int, variants: list[str]):
    _last_variants[telegram_id] = variants


def get_variants(telegram_id: int) -> list[str]:
    return _last_variants.get(telegram_id, [])
