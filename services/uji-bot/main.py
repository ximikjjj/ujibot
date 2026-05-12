import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from database import init_db
from bot.handlers import router as bot_router
from bot.notifications import set_bot
from api.routes import router as api_router
from telethon_worker import restore_all_sessions

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="UJI Bot API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()

bot: Bot | None = None
dp: Dispatcher | None = None


async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить UJI"),
        BotCommand(command="connect", description="Подключить Telegram-сессию"),
        BotCommand(command="disconnect", description="Отключить сессию"),
        BotCommand(command="status", description="Статус подключения"),
        BotCommand(command="goals", description="Мои цели общения"),
        BotCommand(command="digest", description="Разбор дня"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    await bot.set_my_description(
        "UJI — AI помощник по общению. Читает твои переписки в реальном времени и подсказывает что ответить."
    )
    await bot.set_my_short_description("AI помощник по общению в Telegram")
    logger.info("Bot commands and description set")


async def start_bot():
    global bot, dp
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(bot_router)
    set_bot(bot)
    await setup_bot_commands(bot)
    logger.info("Starting bot polling...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


async def main():
    await init_db()
    logger.info("Database initialized")

    await restore_all_sessions()
    logger.info("Telethon sessions restored")

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=settings.port,
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        start_bot()
    )


if __name__ == "__main__":
    asyncio.run(main())
