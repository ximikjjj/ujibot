import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database import AsyncSessionLocal
from models import User
from telethon_worker import start_auth_request_code, complete_auth_with_code, active_clients
import os

logger = logging.getLogger(__name__)
router = Router()

REPLIT_DOMAIN = os.environ.get("REPLIT_DOMAINS", "").split(",")[0].strip()
MINI_APP_URL = f"https://{REPLIT_DOMAIN}" if REPLIT_DOMAIN else ""


class AuthStates(StatesGroup):
    waiting_phone = State()
    waiting_code = State()
    waiting_password = State()


async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None) -> User:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


@router.message(CommandStart())
async def cmd_start(message: Message):
    await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    name = message.from_user.first_name or "друг"
    is_active = message.from_user.id in active_clients

    buttons = []
    if MINI_APP_URL:
        buttons.append([InlineKeyboardButton(
            text="📱 Открыть UJI",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )])

    if not is_active:
        buttons.append([InlineKeyboardButton(text="🔗 Подключить Telegram-сессию", callback_data="connect_session")])
    else:
        buttons.append([InlineKeyboardButton(text="⛔ Отключить сессию", callback_data="disconnect_session")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    status = "✅ Сессия подключена — UJI читает переписки." if is_active else "⭕ Сессия не подключена."

    await message.answer(
        f"Привет, {name}! 👋\n\n"
        f"Я <b>UJI</b> — твой помощник по общению в Telegram.\n\n"
        f"Вижу входящие сообщения и сразу подсказываю что написать: коротко, по делу, без морали.\n\n"
        f"<b>Статус:</b> {status}",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message(Command("connect"))
async def cmd_connect(message: Message, state: FSMContext):
    await message.answer(
        "Для live-чтения переписок нужно подключить твою Telegram-сессию.\n\n"
        "Введи номер телефона в формате <code>+79991234567</code>:",
        parse_mode="HTML"
    )
    await state.set_state(AuthStates.waiting_phone)


@router.message(Command("disconnect"))
async def cmd_disconnect(message: Message):
    from telethon_worker import stop_live_reading
    await stop_live_reading(message.from_user.id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if user:
            user.is_session_active = False
            await session.commit()

    await message.answer("⛔ Сессия отключена. UJI больше не читает переписки.")


@router.message(Command("status"))
async def cmd_status(message: Message):
    is_active = message.from_user.id in active_clients
    status = "✅ активна" if is_active else "⭕ не подключена"
    await message.answer(f"Статус сессии: <b>{status}</b>", parse_mode="HTML")


@router.message(Command("goals"))
async def cmd_goals(message: Message):
    async with AsyncSessionLocal() as session:
        from models import Goal
        result = await session.execute(
            select(Goal).where(Goal.user_id == message.from_user.id, Goal.is_active == True)
        )
        goals = result.scalars().all()

    if not goals:
        await message.answer("Цели не установлены.\n\nОткрой Mini App чтобы добавить цели общения.")
        return

    text = "<b>🎯 Твои цели:</b>\n\n"
    for g in goals:
        text += f"• {g.text}\n"
    await message.answer(text, parse_mode="HTML")


@router.message(Command("digest"))
async def cmd_digest(message: Message):
    from datetime import date
    from models import DailyDigest
    today = date.today().isoformat()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DailyDigest).where(
                DailyDigest.user_id == message.from_user.id,
                DailyDigest.date == today
            )
        )
        digest = result.scalar_one_or_none()

    if not digest:
        await message.answer(
            "Дневной разбор за сегодня ещё не готов.\n"
            "Он генерируется на основе переписок дня."
        )
        return

    text = "<b>📊 Разбор за сегодня</b>\n\n"
    if digest.what_worked:
        text += f"✅ <b>Что получилось:</b>\n{digest.what_worked}\n\n"
    if digest.near_misses:
        text += f"⚡ <b>Чуть не испортил:</b>\n{digest.near_misses}\n\n"
    if digest.best_reply:
        text += f"⭐ <b>Лучший ответ:</b>\n{digest.best_reply}\n\n"
    await message.answer(text, parse_mode="HTML")


@router.message(AuthStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    await message.answer("📤 Отправляю код подтверждения...")

    try:
        await start_auth_request_code(message.from_user.id, phone)
        await state.update_data(phone=phone)
        await state.set_state(AuthStates.waiting_code)
        await message.answer(
            "✅ Код отправлен в Telegram.\n\n"
            "Введи код (например <code>12345</code>):",
            parse_mode="HTML"
        )
    except Exception as e:
        await state.clear()
        await message.answer(f"❌ Ошибка: {e}\n\nПопробуй ещё раз — /connect")


@router.message(AuthStates.waiting_code)
async def process_code(message: Message, state: FSMContext):
    code = message.text.strip().replace(" ", "")
    await message.answer("🔍 Проверяю код...")

    result = await complete_auth_with_code(message.from_user.id, code)

    if result["status"] == "success":
        await state.clear()
        await message.answer(
            "✅ Сессия подключена!\n\n"
            "UJI теперь видит входящие сообщения и будет присылать подсказки сразу."
        )
    elif result["status"] == "need_password":
        await state.set_state(AuthStates.waiting_password)
        await message.answer("🔒 Требуется пароль двухфакторной аутентификации.\nВведи пароль:")
    else:
        await state.clear()
        await message.answer(f"❌ Ошибка: {result['message']}\n\nПопробуй ещё раз — /connect")


@router.message(AuthStates.waiting_password)
async def process_password(message: Message, state: FSMContext):
    password = message.text.strip()
    result = await complete_auth_with_code(message.from_user.id, "", password=password)

    if result["status"] == "success":
        await state.clear()
        await message.answer("✅ Сессия подключена! UJI теперь читает переписки.")
    else:
        await state.clear()
        await message.answer(f"❌ Ошибка: {result['message']}\n\nПопробуй ещё раз — /connect")


@router.callback_query(F.data == "connect_session")
async def cb_connect(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введи номер телефона в формате <code>+79991234567</code>:",
        parse_mode="HTML"
    )
    await state.set_state(AuthStates.waiting_phone)
    await callback.answer()


@router.callback_query(F.data == "disconnect_session")
async def cb_disconnect(callback: CallbackQuery):
    from telethon_worker import stop_live_reading
    await stop_live_reading(callback.from_user.id)
    await callback.message.answer("⛔ Сессия отключена.")
    await callback.answer()


@router.callback_query(F.data.startswith("copy:"))
async def cb_copy_variant(callback: CallbackQuery):
    """User tapped 'Copy variant N' button — send them the text directly."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("Ошибка")
        return

    idx = int(parts[1]) - 1
    user_id = int(parts[2])

    from bot.notifications import get_variants
    variants = get_variants(user_id)

    if 0 <= idx < len(variants):
        variant_text = variants[idx]
        await callback.message.answer(
            f"📋 <b>Вариант {idx + 1}:</b>\n\n{variant_text}",
            parse_mode="HTML"
        )
        await callback.answer(f"Вариант {idx + 1} отправлен")
    else:
        await callback.answer("Вариант недоступен")
