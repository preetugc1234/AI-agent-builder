"""
Integrations API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.models.models import User, UserIntegration
from app.schemas.schemas import IntegrationConnect, IntegrationResponse
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all integrations for the current user
    """
    result = await db.execute(
        select(UserIntegration).where(UserIntegration.user_id == current_user.id)
    )
    integrations = result.scalars().all()

    return integrations


@router.post("/connect")
async def connect_integration(
    integration_data: IntegrationConnect,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Connect a new integration
    """
    # TODO: Implement OAuth flow or API key validation
    # For now, just create a placeholder integration

    service = integration_data.service

    # Check if already connected
    result = await db.execute(
        select(UserIntegration).where(
            UserIntegration.user_id == current_user.id,
            UserIntegration.service_name == service
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{service} is already connected"
        )

    # Create integration (encrypted data would be handled by KMS in production)
    new_integration = UserIntegration(
        user_id=current_user.id,
        service_name=service,
        auth_type="api_key" if integration_data.credentials else "oauth",
        encrypted_data="encrypted_placeholder",  # TODO: Encrypt with KMS
        is_active=True
    )

    db.add(new_integration)
    await db.commit()
    await db.refresh(new_integration)

    return {
        "message": f"{service} connected successfully",
        "integration_id": str(new_integration.id)
    }


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_integration(
    integration_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect an integration
    """
    result = await db.execute(
        select(UserIntegration).where(
            UserIntegration.id == integration_id,
            UserIntegration.user_id == current_user.id
        )
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )

    await db.delete(integration)
    await db.commit()

    return None


@router.get("/available")
async def get_available_integrations():
    """
    Get list of available integrations
    """
    return {
        "integrations": [
            {
                "name": "gmail",
                "display_name": "Gmail",
                "category": "communication",
                "auth_type": "oauth"
            },
            {
                "name": "slack",
                "display_name": "Slack",
                "category": "communication",
                "auth_type": "oauth"
            },
            {
                "name": "twilio",
                "display_name": "Twilio",
                "category": "communication",
                "auth_type": "api_key"
            },
            {
                "name": "supabase",
                "display_name": "Supabase",
                "category": "database",
                "auth_type": "api_key"
            },
            {
                "name": "google_sheets",
                "display_name": "Google Sheets",
                "category": "spreadsheet",
                "auth_type": "oauth"
            },
            {
                "name": "airtable",
                "display_name": "Airtable",
                "category": "database",
                "auth_type": "api_key"
            },
            {
                "name": "notion",
                "display_name": "Notion",
                "category": "knowledge",
                "auth_type": "oauth"
            },
            {
                "name": "openai",
                "display_name": "OpenAI",
                "category": "ai",
                "auth_type": "api_key"
            },
            {
                "name": "langchain",
                "display_name": "LangChain",
                "category": "ai",
                "auth_type": "api_key"
            },
            {
                "name": "github",
                "display_name": "GitHub",
                "category": "code",
                "auth_type": "oauth"
            },
            {
                "name": "vercel",
                "display_name": "Vercel",
                "category": "deployment",
                "auth_type": "oauth"
            }
        ]
    }
