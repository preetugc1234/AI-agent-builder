"""
Configuration settings for NodeRush
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "NodeRush"
    DEBUG: bool = False
    API_VERSION: str = "v1"

    # CORS - accepts comma-separated string or list
    # Add your production frontend URL here or set via environment variable
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://noderush.vercel.app",
        "https://ai-agent-builder-ugag.onrender.com",  # Backend URL for self-origin requests
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Parse CORS_ORIGINS from comma-separated string or list

        Environment variable format:
        CORS_ORIGINS="http://localhost:3000,https://myapp.vercel.app"
        """
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database - Supabase PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/noderush"
    )

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def clean_database_url(cls, v):
        """
        Clean DATABASE_URL by removing unsupported parameters for asyncpg

        Supabase connection strings often include '?pgbouncer=true' which is not
        supported by asyncpg driver. This validator removes such parameters.
        """
        if v and "?" in v:
            # Split URL and query parameters
            base_url, query_string = v.split("?", 1)

            # Parse query parameters
            params = query_string.split("&")

            # Filter out unsupported parameters (pgbouncer)
            supported_params = [
                param for param in params
                if not param.startswith("pgbouncer=")
            ]

            # Reconstruct URL with supported parameters only
            if supported_params:
                return f"{base_url}?{'&'.join(supported_params)}"
            else:
                return base_url

        return v

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
