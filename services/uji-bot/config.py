import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = os.environ["TELEGRAM_BOT_TOKEN"]
    telegram_api_id: int = int(os.environ["TELEGRAM_API_ID"])
    telegram_api_hash: str = os.environ["TELEGRAM_API_HASH"]
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    google_api_key: str = os.environ.get("GOOGLE_API_KEY", "")
    database_url: str = os.environ["DATABASE_URL"]
    port: int = int(os.environ.get("BOT_API_PORT", "8000"))

    class Config:
        env_file = ".env"


settings = Settings()
