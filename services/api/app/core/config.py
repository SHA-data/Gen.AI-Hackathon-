import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./neuralcfo.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Security
    JWT_SECRET: str = "demo-secret-key-change-in-production-never-commit-actual-secrets-32bytes"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Engine Defaults
    DEFAULT_BASE_CURRENCY: str = "USD"
    DEFAULT_CASH_FLOOR_WEEKS: int = 12
    ENGINE_VERSION: str = "0.1.0"

    # Sponsor Integrations
    ZETARIS_ENABLED: bool = False
    ZETARIS_ENDPOINT: Optional[str] = None
    ZETARIS_API_KEY: Optional[str] = None
    ZETARIS_DATABASE: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
