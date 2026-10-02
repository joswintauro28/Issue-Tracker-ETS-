"""Application configuration loaded from environment variables / .env.

Secrets are never hardcoded: if SECRET_KEY is not provided, a random key is
generated for the current process (with a warning) so development still works
without committed secrets. Production must set SECRET_KEY explicitly.
"""

import secrets
from functools import lru_cache
from logging import getLogger

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = getLogger(__name__)


class Settings(BaseSettings):
    """Runtime settings. Values come from the environment or ``backend/.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "Issue Tracker API"
    API_PREFIX: str = "/api"
    VERSION: str = "0.1.0"

    # Security - SECRET_KEY must come from the environment; no default value.
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, gt=0)

    # Database: SQLite for local development, PostgreSQL for deployment
    # (e.g. postgresql+psycopg://user:pass@host:5432/issue_tracker).
    DATABASE_URL: str = "sqlite:///./issue_tracker.db"

    # Comma-separated list of origins allowed to call the API.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.SECRET_KEY:
        settings.SECRET_KEY = secrets.token_hex(32)
        logger.warning(
            "SECRET_KEY is not set - generated a temporary random key. "
            "Tokens will be invalidated on every restart. Set SECRET_KEY in "
            "backend/.env or the environment."
        )
    return settings


settings = get_settings()
