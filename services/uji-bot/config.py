import os

BOT_API_PORT = int(os.environ.get("BOT_API_PORT", "8000"))

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_API_ID = int(os.environ["TELEGRAM_API_ID"])
TELEGRAM_API_HASH = os.environ["TELEGRAM_API_HASH"]
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
DATABASE_URL = os.environ["DATABASE_URL"]


class Settings:
    telegram_bot_token: str = TELEGRAM_BOT_TOKEN
    telegram_api_id: int = TELEGRAM_API_ID
    telegram_api_hash: str = TELEGRAM_API_HASH
    openai_api_key: str = OPENAI_API_KEY
    google_api_key: str = GOOGLE_API_KEY
    database_url: str = DATABASE_URL
    port: int = BOT_API_PORT


settings = Settings()
