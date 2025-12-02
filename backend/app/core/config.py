"""
Configuration settings for NodeRush
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "NodeRush"
    DEBUG: bool = False
    API_VERSION: str = "v1"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://noderush.vercel.app",
    ]

    # Database - Supabase PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/noderush"
    )

    # Redis - Upstash Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # JWT & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # OpenRouter for NVIDIA Nemotron
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    AI_MODEL: str = "nvidia/nemotron-nano-12b-v2-vl:free"

    # Integration OAuth Credentials
    # Gmail
    GMAIL_CLIENT_ID: str = os.getenv("GMAIL_CLIENT_ID", "")
    GMAIL_CLIENT_SECRET: str = os.getenv("GMAIL_CLIENT_SECRET", "")

    # Slack
    SLACK_CLIENT_ID: str = os.getenv("SLACK_CLIENT_ID", "")
    SLACK_CLIENT_SECRET: str = os.getenv("SLACK_CLIENT_SECRET", "")

    # GitHub
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")

    # Notion
    NOTION_CLIENT_ID: str = os.getenv("NOTION_CLIENT_ID", "")
    NOTION_CLIENT_SECRET: str = os.getenv("NOTION_CLIENT_SECRET", "")

    # Google Sheets
    GOOGLE_SHEETS_CLIENT_ID: str = os.getenv("GOOGLE_SHEETS_CLIENT_ID", "")
    GOOGLE_SHEETS_CLIENT_SECRET: str = os.getenv("GOOGLE_SHEETS_CLIENT_SECRET", "")

    # Payment
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
