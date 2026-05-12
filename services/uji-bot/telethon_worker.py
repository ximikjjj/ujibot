import asyncio
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from sqlalchemy import select
from database import AsyncSessionLocal
from models import User, Suggestion
from ai_service import analyze_message
from config import settings

logger = logging.getLogger(__name__)

active_clients: dict[int, TelegramClient] = {}
pending_auth: dict[int, dict] = {}


async def get_user(telegram_id: int) -> User | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()


async def save_suggestion(user_id: int, chat_id: int, incoming: str, analysis_result: dict):
    async with AsyncSessionLocal() as session:
        suggestion = Suggestion(
            user_id=user_id,
            chat_id=chat_id,
            incoming_message=incoming,
            analysis=analysis_result.get("analysis"),
            variants=analysis_result.get("variants", []),
            tone=analysis_result.get("tone")
        )
        session.add(suggestion)
        await session.commit()


async def start_live_reading(telegram_id: int, session_string: str, goals: list[str] = None):
    if telegram_id in active_clients:
        try:
            await active_clients[telegram_id].disconnect()
        except Exception:
            pass

    client = TelegramClient(
        StringSession(session_string),
        settings.telegram_api_id,
        settings.telegram_api_hash
    )

    await client.connect()
    if not await client.is_user_authorized():
        logger.warning(f"User {telegram_id} session is not authorized")
        return False

    @client.on(events.NewMessage(incoming=True))
    async def handle_new_message(event):
        if event.is_private:
            try:
                message_text = event.message.message
                if not message_text or len(message_text) < 2:
                    return

                # Get context: last 10 messages from this chat (both sides)
                context = []
                try:
                    async for msg in client.iter_messages(event.chat_id, limit=10):
                        if msg.message:
                            sender = "Я" if not msg.out is False else "Собеседник"
                            # out=True means sent by us, out=False means received
                            sender = "Я" if msg.out else "Собеседник"
                            context.append({"sender": sender, "text": msg.message})
                    context.reverse()
                except Exception:
                    pass

                result = await analyze_message(
                    incoming_message=message_text,
                    context=context if context else None,
                    goals=goals or []
                )

                await save_suggestion(
                    user_id=telegram_id,
                    chat_id=event.chat_id,
                    incoming=message_text,
                    analysis_result=result
                )

                from bot.notifications import send_suggestion_to_user, store_variants
                store_variants(telegram_id, result.get("variants", []))
                await send_suggestion_to_user(telegram_id, message_text, result)

            except Exception as e:
                logger.error(f"Error handling message for {telegram_id}: {e}")

    active_clients[telegram_id] = client
    logger.info(f"Live reading started for user {telegram_id}")
    return True


async def stop_live_reading(telegram_id: int):
    if telegram_id in active_clients:
        try:
            await active_clients[telegram_id].disconnect()
        except Exception:
            pass
        del active_clients[telegram_id]


async def start_auth_request_code(telegram_id: int, phone: str) -> dict:
    client = TelegramClient(
        StringSession(),
        settings.telegram_api_id,
        settings.telegram_api_hash
    )
    await client.connect()

    result = await client.send_code_request(phone)
    pending_auth[telegram_id] = {
        "client": client,
        "phone": phone,
        "phone_code_hash": result.phone_code_hash
    }
    return {"status": "code_sent", "phone_code_hash": result.phone_code_hash}


async def complete_auth_with_code(telegram_id: int, code: str, password: str = None) -> dict:
    if telegram_id not in pending_auth:
        return {"status": "error", "message": "Нет активного запроса авторизации. Начните заново."}

    auth_data = pending_auth[telegram_id]
    client: TelegramClient = auth_data["client"]

    try:
        await client.sign_in(
            phone=auth_data["phone"],
            code=code,
            phone_code_hash=auth_data["phone_code_hash"]
        )
    except Exception as e:
        if "two-steps" in str(e).lower() or "password" in str(e).lower():
            if not password:
                return {"status": "need_password", "message": "Требуется пароль двухфакторной аутентификации"}
            try:
                await client.sign_in(password=password)
            except Exception as e2:
                return {"status": "error", "message": f"Неверный пароль: {e2}"}
        else:
            return {"status": "error", "message": str(e)}

    session_string = client.session.save()

    async with AsyncSessionLocal() as session:
        user = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = user.scalar_one_or_none()
        if user:
            user.telethon_session = session_string
            user.is_session_active = True
            user.phone = auth_data["phone"]
            await session.commit()

    del pending_auth[telegram_id]

    await start_live_reading(telegram_id, session_string)

    return {"status": "success", "message": "Сессия подключена! UJI теперь читает переписки в реальном времени."}


async def restore_all_sessions():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.is_session_active == True, User.telethon_session != None)
        )
        users = result.scalars().all()

    for user in users:
        try:
            goals_result = []
            from sqlalchemy import select as sa_select
            from models import Goal
            async with AsyncSessionLocal() as session:
                g_result = await session.execute(
                    sa_select(Goal).where(Goal.user_id == user.telegram_id, Goal.is_active == True)
                )
                goals_result = [g.text for g in g_result.scalars().all()]

            success = await start_live_reading(user.telegram_id, user.telethon_session, goals_result)
            if not success:
                async with AsyncSessionLocal() as s:
                    u = await s.execute(select(User).where(User.telegram_id == user.telegram_id))
                    u = u.scalar_one_or_none()
                    if u:
                        u.is_session_active = False
                        await s.commit()
        except Exception as e:
            logger.error(f"Failed to restore session for {user.telegram_id}: {e}")
