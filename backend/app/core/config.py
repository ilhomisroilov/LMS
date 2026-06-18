"""Application settings loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Look for .env in the current dir or the project root (so it works whether
    # the app is started from backend/ or the repository root).
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    # General
    PROJECT_NAME: str = "EduCore"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEFAULT_LANGUAGE: str = "uz"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://educore:educore_pass@localhost:5432/educore"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RATE_LIMIT_PER_MINUTE: int = 120

    # CORS — comma-separated list of allowed origins (kept as str to avoid
    # JSON-decoding issues when loaded from a .env file).
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_DIR: str = "./storage/uploads"

    # Bot internal auth
    BOT_API_TOKEN: str = "bot-internal-secret-token"

    # Seed admin
    FIRST_ADMIN_PHONE: str = "+998901112233"
    FIRST_ADMIN_PASSWORD: str = "Admin12345"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
