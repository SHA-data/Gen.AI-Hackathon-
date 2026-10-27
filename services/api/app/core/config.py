"""Core configuration settings for FastAPI service."""
import os
from typing import Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: Literal["dev", "test", "prod"] = "dev"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/neuralcfo")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-hackathon-key-2026-very-secure-32bytes")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Model configuration (Swappable per Part B0.4)
    MODEL_NAME: str = os.getenv("MODEL_NAME", "nvidia/nemotron-3-super")
    FALLBACK_MODEL_NAME: str = os.getenv("FALLBACK_MODEL_NAME", "nvidia/nemotron-3.5-lightning")
    
    # Backend flags for modular independence (Part B2.5)
    FINANCE_BACKEND: Literal["fake", "real"] = "fake"
    MOONSHOT_BACKEND: Literal["fake", "real"] = "fake"
    MEMORY_BACKEND: Literal["fake", "postgres", "meterless"] = "fake"
    
    # Storage
    DOCUMENT_STORAGE_DIR: str = os.getenv("DOCUMENT_STORAGE_DIR", "/tmp/neuralcfo_docs")

    model_config = {
        "env_file": ".env",
        "extra": "allow",
    }

settings = Settings()
