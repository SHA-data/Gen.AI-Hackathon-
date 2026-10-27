"""Core configuration settings for FastAPI service."""
import os
from typing import Literal, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: Literal["dev", "test", "prod"] = "dev"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./neuralcfo.db",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-hackathon-key-2026-very-secure-32bytes")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Model configuration (Swappable per Part B0.4)
    MODEL_NAME: str = os.getenv("MODEL_NAME", "nvidia/nemotron-3-super")
    FALLBACK_MODEL_NAME: str = os.getenv("FALLBACK_MODEL_NAME", "nvidia/nemotron-3.5-lightning")

    # Engine Defaults
    DEFAULT_BASE_CURRENCY: str = "USD"
    DEFAULT_CASH_FLOOR_WEEKS: int = 12
    ENGINE_VERSION: str = "0.1.0"

    # Backend flags for modular independence (Part B2.5)
    FINANCE_BACKEND: Literal["fake", "real"] = "fake"
    MOONSHOT_BACKEND: Literal["fake", "real"] = "fake"
    MEMORY_BACKEND: Literal["fake", "postgres", "meterless"] = "fake"

    # Sponsor Integrations: Zetaris & Meterless
    ZETARIS_ENABLED: bool = False
    ZETARIS_ENDPOINT: Optional[str] = None
    ZETARIS_API_KEY: Optional[str] = None
    ZETARIS_DATABASE: Optional[str] = None

    METERLESS_API_KEY: Optional[str] = None
    METERLESS_ENDPOINT: Optional[str] = None

    # Storage
    DOCUMENT_STORAGE_DIR: str = os.getenv("DOCUMENT_STORAGE_DIR", "/tmp/neuralcfo_docs")

    model_config = {
        "env_file": ".env",
        "extra": "allow",
    }


settings = Settings()
