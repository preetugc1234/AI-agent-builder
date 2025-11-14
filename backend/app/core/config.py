"""
Configuration settings for VibeAgent Forge
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "VibeAgent Forge"
    DEBUG: bool = False
    API_VERSION: str = "v1"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://noderush.vercel.app",
        "https://vibeagent-forge.vercel.app"
    ]

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/vibeagent"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # JWT & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    # AWS Services
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "vibeagent-storage")
    AWS_ECR_REGISTRY: str = os.getenv("AWS_ECR_REGISTRY", "")
    AWS_ECS_CLUSTER: str = os.getenv("AWS_ECS_CLUSTER", "vibeagent-cluster")
    AWS_KMS_KEY_ID: str = os.getenv("AWS_KMS_KEY_ID", "")

    # OpenRouter for NVIDIA Nemotron
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    AI_MODEL: str = "nvidia/nemotron-nano-12b-2vl"

    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

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

    # Vercel
    VERCEL_CLIENT_ID: str = os.getenv("VERCEL_CLIENT_ID", "")
    VERCEL_CLIENT_SECRET: str = os.getenv("VERCEL_CLIENT_SECRET", "")

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

    # Docker
    DOCKER_REGISTRY: str = os.getenv("DOCKER_REGISTRY", "")

    # Cloudflare
    CLOUDFLARE_API_TOKEN: str = os.getenv("CLOUDFLARE_API_TOKEN", "")
    CLOUDFLARE_ACCOUNT_ID: str = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
