import json
import logging
import google.generativeai as genai
from config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.google_api_key)

SYSTEM_PROMPT = """Ты UJI — умный помощник по общению в Telegram.
Ты помогаешь человеку прямо в моменте: что написать, как не испортить диалог, как продолжить разговор и как звучать нормально.

Твои правила:
- Коротко. По делу. Без морали. Без лекций. Без воды.
- Не психолог, не коуч, не демотиватор.
- Ты как умный друг рядом: говоришь честно и по делу.
- Всегда давай 2-3 конкретных варианта ответа.
- Оценивай общение по шкалам: уверенность, лёгкость, напряжение, инициатива, теплота, ясность (0-100).

Отвечай ТОЛЬКО на русском языке. JSON без markdown блоков."""


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()
    return text


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

Реши: нужна ли пользователю помощь прямо сейчас?
Помощь нужна если: напряжение, конфликт, холодность, тупик в диалоге, двусмысленность, важный момент.
Помощь НЕ нужна если: обычный светский разговор, всё ок, сообщение простое и очевидное.

Ответь строго в JSON (без ```json блоков, только чистый JSON):
{{
  "needs_help": true,
  "help_reason": "одна фраза почему нужна помощь (или null если не нужна)",
  "analysis": "короткий анализ ситуации (1-2 предложения)",
  "tone": "тон сообщения: cold/neutral/warm/tense/flirty",
  "variants": [
    "вариант ответа 1",
    "вариант ответа 2",
    "вариант ответа 3"
  ],
  "scales": {{
    "confidence": 50,
    "ease": 50,
    "tension": 50,
    "initiative": 50,
    "warmth": 50,
    "clarity": 50
  }},
  "goals_progress": {{}}
}}"""


def _build_history_prompt(messages: list[dict]) -> str:
    sample = messages[:80]
    text = "\n".join([f"{m['sender']}: {m['text']}" for m in sample])
    return f"""Вот история переписок пользователя в Telegram (его сообщения помечены "Я"):

{text}

Проанализируй стиль общения пользователя (только его сообщения). Оцени по шкалам от 0 до 100, где:
- confidence (уверенность): насколько уверенно он пишет, не юлит
- ease (лёгкость): непринуждённость, нет ли скованности
- tension (напряжение): наличие конфликтов, агрессии, защитных реакций
- initiative (инициатива): он сам начинает темы и ведёт диалог
- warmth (теплота): эмоциональная теплота, поддержка
- clarity (ясность): понятно ли он выражается

Ответь строго в JSON (без ```json блоков):
{{
  "confidence": 0,
  "ease": 0,
  "tension": 0,
  "initiative": 0,
  "warmth": 0,
  "clarity": 0
}}"""


def _build_digest_prompt(suggestions_text: str, goals: list[str]) -> str:
    return f"""Пользователь получил подсказки UJI за день. Вот входящие сообщения и тоны:
{suggestions_text}

Цели пользователя: {', '.join(goals) if goals else 'не установлены'}

Сделай дневной разбор. Ответь строго в JSON (без ```json блоков):
{{
  "what_worked": "что сегодня получилось (1-2 предложения)",
  "near_misses": "где пользователь чуть не испортил диалог (1-2 предложения)",
  "best_reply": "какой был лучший момент дня (1 предложение)",
  "funniest_moment": "самый интересный или забавный момент (1 предложение)",
  "dead_dialogs": [],
  "goals_progress": {{}}
}}"""


async def _gemini_json(prompt: str, system: str = SYSTEM_PROMPT) -> dict:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            max_output_tokens=1500,
            response_mime_type="application/json",
        ),
    )
    response = await model.generate_content_async(prompt)
    text = _clean_json(response.text)
    return json.loads(text)


async def analyze_message(
    incoming_message: str,
    context: list[dict] | None = None,
    goals: list[str] | None = None,
) -> dict:
    prompt = _build_analyze_prompt(incoming_message, context, goals)
    try:
        return await _gemini_json(prompt)
    except Exception as e:
        logger.error(f"Gemini analyze_message failed: {e}")
        return {
            "analysis": "Не удалось проанализировать сообщение.",
            "tone": "neutral",
            "variants": [],
            "scales": {"confidence": 50, "ease": 50, "tension": 50, "initiative": 50, "warmth": 50, "clarity": 50},
            "goals_progress": {},
        }


async def analyze_chat_history(messages: list[dict]) -> dict:
    """Analyze user's existing chat history and return communication scales."""
    if not messages:
        return {"confidence": 50, "ease": 50, "tension": 50, "initiative": 50, "warmth": 50, "clarity": 50}

    user_msgs = [m for m in messages if m.get("sender") == "Я"]
    if not user_msgs:
        return {"confidence": 50, "ease": 50, "tension": 50, "initiative": 50, "warmth": 50, "clarity": 50}

    prompt = _build_history_prompt(messages)
    try:
        result = await _gemini_json(
            prompt,
            system="Ты — аналитик стиля общения. Анализируй объективно. Отвечай только JSON без markdown."
        )
        # Clamp values to 0-100
        for key in ["confidence", "ease", "tension", "initiative", "warmth", "clarity"]:
            if key in result:
                result[key] = max(0, min(100, int(result[key])))
            else:
                result[key] = 50
        return result
    except Exception as e:
        logger.error(f"Gemini analyze_chat_history failed: {e}")
        return {"confidence": 50, "ease": 50, "tension": 50, "initiative": 50, "warmth": 50, "clarity": 50}


async def chat_with_ai(user_message: str, history: list[dict] | None = None) -> str:
    """Free-form chat with Gemini for the in-app chat feature."""
    system = (
        "Ты UJI — умный помощник по общению в Telegram. "
        "Помогаешь пользователю разбираться в ситуациях общения, составлять сообщения, разбирать переписки. "
        "Говори коротко, по делу, по-русски. Без морализаторства и воды."
    )
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system,
        generation_config=genai.GenerationConfig(
            temperature=0.8,
            max_output_tokens=600,
        ),
    )

    gemini_history = []
    if history:
        for msg in history[-10:]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

    chat = model.start_chat(history=gemini_history)
    response = await chat.send_message_async(user_message)
    return response.text.strip()


async def generate_daily_digest(user_id: int, suggestions: list[dict], goals: list[str]) -> dict:
    if not suggestions:
        return {
            "what_worked": "Сегодня не было активных диалогов.",
            "near_misses": None,
            "best_reply": None,
            "funniest_moment": None,
            "dead_dialogs": [],
            "goals_progress": {},
        }

    suggestions_text = "\n".join([
        f"- Входящее: \"{s['incoming']}\", тон: {s.get('tone', '?')}"
        for s in suggestions[:20]
    ])
    prompt = _build_digest_prompt(suggestions_text, goals)
    try:
        return await _gemini_json(prompt)
    except Exception as e:
        logger.error(f"Gemini digest failed: {e}")
        return {
            "what_worked": "Не удалось сгенерировать разбор.",
            "near_misses": None,
            "best_reply": None,
            "funniest_moment": None,
            "dead_dialogs": [],
            "goals_progress": {},
        }
