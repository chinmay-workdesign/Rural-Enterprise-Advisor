import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Telegram Bot API (Direct, zero-cost, instant setup)
    TELEGRAM_BOT_TOKEN: str = ""

    # WhatsApp Meta Cloud API (Retained for future deployment)
    WHATSAPP_VERIFY_TOKEN: str = "default_verify_token"
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    PHONE_NUMBER_ID: str = ""

    # Google Gemini (Free Tier LLM & Multimodal Audio STT)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Database
    DATABASE_URL: Optional[str] = None

    # General
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    BACKEND_INTERNAL_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        """Returns configured database URL or falls back to local SQLite."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite:///./rural_advisor.db"

settings = Settings()
