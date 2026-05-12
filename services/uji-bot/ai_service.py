import json
import logging
from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты UJI — умный помощник по общению в Telegram.
Ты помогаешь человеку прямо в моменте: что написать, как не испортить диалог, как продолжить разговор и как звучать нормально.

Твои правила:
- Коротко. По делу. Без морали. Без лекций. Без воды.
- Не психолог, не коуч, не демотиватор.
- Ты как умный друг рядом: говоришь честно и по делу.
- Всегда давай 2-3 конкретных варианта ответа.
- Оценивай общение по шкалам: уверенность, лёгкость, напряжение, инициатива, теплота, ясность (0-100).

Отвечай ТОЛЬКО на русском языке. JSON без markdown блоков."""


def _build_analyze_prompt(incoming_message: str, context: list[dict] | None, goals: list[str] | None) -> str:
    context_text = ""
    if context:
        context_text = "\n".join([f"{m['sender']}: {m['text']}" for m in context[-10:]])

    goals_text = ""
    if goals:
        goals_text = f"\nЦели пользователя: {', '.join(goals)}"

    return f"""Контекст переписки:
{context_text}

Новое сообщение от собеседника: "{incoming_message}"{goals_text}

Ответь в JSON:
{{
  "analysis": "короткий анализ ситуации (1-2 предложения)",
  "tone": "тон сообщения: cold/neutral/warm/tense/flirty",
  "variants": [
    "вариант ответа 1",
    "вариант ответа 2",
    "вариант ответа 3"
  ],
  "scales": {{
    "confidence": 0,
    "ease": 0,
    "tension": 0,
    "initiative": 0,
    "warmth": 0,
    "clarity": 0
  }},
  "goals_progress": {{}}
}}"""


def _build_digest_prompt(suggestions_text: str, goals: list[str]) -> str:
    return f"""Пользователь получил подсказки UJI за день. Вот входящие сообщения и тоны:
{suggestions_text}

Цели пользователя: {', '.join(goals) if goals else 'не установлены'}

Сделай дневной разбор. Ответь в JSON:
{{
  "what_worked": "что сегодня получилось (1-2 предложения)",
  "near_misses": "где пользователь чуть не испортил диалог (1-2 предложения или null)",
  "best_reply": "какой был лучший момент дня (1 предложение или null)",
  "funniest_moment": "самый интересный или забавный момент (1 предложение или null)",
  "dead_dialogs": ["тема1", "тема2"],
  "goals_progress": {{"цель": "прогресс (прогресс/нет прогресса)"}}
}}"""


async def _call_gemini(prompt: str) -> dict:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        api_key=settings.google_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    response = await client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=800
    )
    return json.loads(response.choices[0].message.content)


async def _call_openai(prompt: str) -> dict:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=800
    )
    return json.loads(response.choices[0].message.content)


async def _call_ai(prompt: str) -> dict:
    if settings.google_api_key:
        try:
            return await _call_gemini(prompt)
        except Exception as e:
            logger.warning(f"Gemini failed: {e}, falling back to OpenAI")

    if settings.openai_api_key:
        try:
            return await _call_openai(prompt)
        except Exception as e:
            logger.error(f"OpenAI also failed: {e}")
            raise

    raise RuntimeError("No AI provider configured. Set GOOGLE_API_KEY or OPENAI_API_KEY.")


async def analyze_message(
    incoming_message: str,
    context: list[dict] | None = None,
    goals: list[str] | None = None
) -> dict:
    prompt = _build_analyze_prompt(incoming_message, context, goals)
    return await _call_ai(prompt)


async def generate_daily_digest(
    user_id: int,
    suggestions: list[dict],
    goals: list[str]
) -> dict:
    if not suggestions:
        return {
            "what_worked": "Сегодня не было активных диалогов.",
            "near_misses": None,
            "best_reply": None,
            "funniest_moment": None,
            "dead_dialogs": [],
            "goals_progress": {}
        }

    suggestions_text = "\n".join([
        f"- Входящее: \"{s['incoming']}\", тон: {s.get('tone', '?')}"
        for s in suggestions[:20]
    ])
    prompt = _build_digest_prompt(suggestions_text, goals)
    return await _call_ai(prompt)
