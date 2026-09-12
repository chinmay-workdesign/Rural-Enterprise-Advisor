import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Telegram Bot API (Direct, zero-cost, instant setup)
    TELEGRAM_BOT_TOKEN: str = ""

    # WhatsApp Meta Cloud API
    WHATSAPP_VERIFY_TOKEN: str = "default_verify_token"
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    PHONE_NUMBER_ID: str = ""

    # Google Gemini (Free Tier LLM & Multimodal Audio STT)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # Qdrant Vector DB
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "nabard_benchmarks"

    # Database
    NEON_DATABASE_URL: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    # Cloudflare R2
    CLOUDFLARE_R2_ACCOUNT_ID: str = ""
    CLOUDFLARE_R2_ACCESS_KEY_ID: str = ""
    CLOUDFLARE_R2_SECRET_ACCESS_KEY: str = ""
    CLOUDFLARE_R2_BUCKET_NAME: str = "rural-dpr-storage"
    CLOUDFLARE_R2_PUBLIC_URL: str = "https://pub-r2.dev"

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
        url = self.NEON_DATABASE_URL or self.DATABASE_URL
        if url and not ("user:password" in url or "ep-sample" in url):
            try:
                import psycopg2
                if url.startswith("postgres://"):
                    url = url.replace("postgres://", "postgresql://", 1)
                return url
            except ImportError:
                pass
        # Fallback to local SQLite for tests/local development
        return "sqlite:///./rural_advisor.db"

settings = Settings()
