# UJI Bot

AI-помощник по общению в Telegram — читает переписки в реальном времени и подсказывает что ответить, анализирует стиль общения.

## Run & Operate

- Воркфлоу **"Start application"** — фронт (Vite, порт 5000)
- Воркфлоу **"UJI Bot"** — Python бот + FastAPI (порт 8000)
- `cd services/uji-bot && pip install -r requirements.txt` — установка Python зависимостей
- `pnpm install` — установка Node зависимостей

## Stack

- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS 4, wouter
- **Bot**: Python, aiogram 3 (Telegram bot), Telethon (чтение чатов), FastAPI
- **AI**: Google Gemini 1.5 Flash (бесплатный)
- **DB**: PostgreSQL + SQLAlchemy (async) + Alembic
- **Monorepo**: pnpm workspaces

## Where things live

- `uji/` — React фронт (Telegram Mini App)
- `services/uji-bot/` — Python бот + FastAPI API
- `services/uji-bot/ai_service.py` — весь AI (Gemini)
- `services/uji-bot/telethon_worker.py` — чтение чатов в реальном времени
- `services/uji-bot/api/routes.py` — REST API эндпоинты
- `services/uji-bot/bot/handlers.py` — Telegram bot команды
- `uji/src/pages/` — страницы приложения
- `uji/src/lib/api.ts` — API клиент фронта

## Architecture decisions

- Фронт проксирует `/bot-api/*` → `localhost:8000` через Vite proxy
- Gemini вызывается через нативный SDK `google-generativeai` (не OpenAI compat)
- При первом подключении сессии — автоматический scan последних 10 чатов для реальных показателей
- WebSocket `/bot-api/ws/{telegram_id}` для live-подсказок в приложении
- Бот и FastAPI запускаются в одном asyncio процессе через `asyncio.gather`

## Product

- Подключение Telegram-сессии через Telethon (MTProto)
- Реальное чтение входящих сообщений → Gemini анализирует → варианты ответа в бот и в приложение
- Анализ истории чатов при первом входе → реальные показатели общения
- Чат с AI прямо в приложении
- Дневной разбор переписок
- Цели общения с отслеживанием прогресса

## User preferences

- Интерфейс и общение — на русском языке
- AI: только бесплатный Gemini 1.5 Flash
- Показатели должны быть реальными (из анализа), не заглушка 50

## Gotchas

- `BOT_API_PORT=8000` — порт Python бота
- `PORT=5000` — порт фронта
- `BASE_PATH=/` — обязательно для Vite
- После изменений Python кода — перезапустить воркфлоу "UJI Bot"
- `REPLIT_DOMAINS` используется для формирования Mini App URL в боте
