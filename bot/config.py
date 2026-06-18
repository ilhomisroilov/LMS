"""Bot configuration from environment."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    TELEGRAM_BOT_TOKEN: str = "put-token-here"
    BOT_API_BASE_URL: str = "http://localhost:8000/api/v1"
    BOT_API_TOKEN: str = "bot-internal-secret-token"
    BOT_DEFAULT_LANGUAGE: str = "uz"


settings = BotSettings()
