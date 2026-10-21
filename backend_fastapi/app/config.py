"""BCMS Designer FastAPI Backend — Configuration."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    SESSION_SECRET: str

    # App
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:8000"
    PAGE_SIZE: int = 50
    TIMEZONE: str = "Asia/Tashkent"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
