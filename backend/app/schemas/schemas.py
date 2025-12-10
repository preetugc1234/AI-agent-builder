"""
Pydantic schemas for request/response validation
Enhanced with comprehensive input validation, XSS prevention, and prompt injection protection
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re


# ============= User Schemas =============
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength

        Requirements:
        - Minimum 8 characters
        - Maximum 128 characters
        - At least one letter (a-z, A-Z)
        - At least one digit (0-9)
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if len(v) > 128:
            raise ValueError('Password must be 128 characters or less')

        # Check for at least one letter
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')

        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')

        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID
    subscription_tier: str
    subscription_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Agent Schemas =============
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    vibe_prompt: str = Field(..., min_length=10, max_length=5000)

    @field_validator('name')
    @classmethod
    def validate_name_xss(cls, v: str) -> str:
        """
        Prevent XSS attacks in name field

        Blocks:
        - HTML tags (< and >)
        - Script tags
        - Event handlers
        """
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')

        # Check for HTML tags
        if '<' in v or '>' in v:
            raise ValueError('Name cannot contain HTML tags (< or >)')

        # Check for script-like patterns
        dangerous_patterns = [
            'script',
            'javascript:',
            'onerror',
            'onload',
            'onclick'
        ]

        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f'Name contains suspicious pattern: {pattern}')

        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description_xss(cls, v: Optional[str]) -> Optional[str]:
        """
        Prevent XSS attacks in description field
        """
        if v is None:
            return v

        if not v.strip():
            return None

        # Check for HTML tags
        if '<' in v or '>' in v:
            raise ValueError('Description cannot contain HTML tags (< or >)')

        # Check for script-like patterns
        dangerous_patterns = [
            '<script',
            'javascript:',
            'onerror=',
            'onload=',
            'onclick='
        ]

        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f'Description contains suspicious pattern: {pattern}')

        return v.strip()

    @field_validator('vibe_prompt')
    @classmethod
    def validate_prompt_injection(cls, v: str) -> str:
        """
        Prevent prompt injection attacks

        Blocks suspicious keywords that could:
        - Override system prompts
        - Leak sensitive information
        - Jailbreak the AI
        """
        if not v or not v.strip():
            raise ValueError('Vibe prompt cannot be empty')

        v_lower = v.lower()

        # Prompt injection blacklist
        injection_patterns = [
            'ignore previous',
            'ignore all previous',
            'disregard previous',
            'forget previous',
            'system:',
            'system prompt',
            'you are now',
            'new instructions',
            'jailbreak',
            'dan mode',
            'developer mode',
            'ignore instructions',
            'bypass restrictions'
        ]

        for pattern in injection_patterns:
            if pattern in v_lower:
                raise ValueError(f'Prompt contains suspicious pattern: "{pattern}". Please rephrase your request.')

        # Check for excessive control characters
        control_char_count = sum(1 for char in v if ord(char) < 32 and char not in '\n\r\t')
        if control_char_count > 5:
            raise ValueError('Prompt contains too many control characters')

        return v.strip()


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    vibe_prompt: Optional[str] = Field(None, min_length=10, max_length=5000)
    status: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name_xss(cls, v: Optional[str]) -> Optional[str]:
        """Prevent XSS attacks in name field"""
        if v is None:
            return v

        if not v.strip():
            raise ValueError('Name cannot be empty')

        # Check for HTML tags
        if '<' in v or '>' in v:
            raise ValueError('Name cannot contain HTML tags (< or >)')

        # Check for script-like patterns
        dangerous_patterns = ['script', 'javascript:', 'onerror', 'onload', 'onclick']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f'Name contains suspicious pattern: {pattern}')

        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description_xss(cls, v: Optional[str]) -> Optional[str]:
        """Prevent XSS attacks in description field"""
        if v is None:
            return v

        if not v.strip():
            return None

        # Check for HTML tags
        if '<' in v or '>' in v:
            raise ValueError('Description cannot contain HTML tags (< or >)')

        # Check for script-like patterns
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onload=', 'onclick=']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f'Description contains suspicious pattern: {pattern}')

        return v.strip()

    @field_validator('vibe_prompt')
    @classmethod
    def validate_prompt_injection(cls, v: Optional[str]) -> Optional[str]:
        """Prevent prompt injection attacks"""
        if v is None:
            return v

        if not v.strip():
            raise ValueError('Vibe prompt cannot be empty')

        v_lower = v.lower()

        # Prompt injection blacklist
        injection_patterns = [
            'ignore previous',
            'ignore all previous',
            'disregard previous',
            'forget previous',
            'system:',
            'system prompt',
            'you are now',
            'new instructions',
            'jailbreak',
            'dan mode',
            'developer mode',
            'ignore instructions',
            'bypass restrictions'
        ]

        for pattern in injection_patterns:
            if pattern in v_lower:
                raise ValueError(f'Prompt contains suspicious pattern: "{pattern}". Please rephrase your request.')

        # Check for excessive control characters
        control_char_count = sum(1 for char in v if ord(char) < 32 and char not in '\n\r\t')
        if control_char_count > 5:
            raise ValueError('Prompt contains too many control characters')

        return v.strip()

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate agent status"""
        if v is None:
            return v

        allowed_statuses = ['draft', 'generating', 'ready', 'error', 'deployed']

        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')

        return v


class AgentResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    vibe_prompt: str
    generated_code: Optional[str]
    docker_image_url: Optional[str]
    status: str
    integrations: List[str]
    flow_data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============= Integration Schemas =============
class IntegrationConnect(BaseModel):
    service: str = Field(..., min_length=1, max_length=100)
    credentials: Optional[Dict[str, str]] = None
    redirect_uri: Optional[str] = Field(None, max_length=500)

    @field_validator('service')
    @classmethod
    def validate_service_name(cls, v: str) -> str:
        """Validate service name"""
        if not v or not v.strip():
            raise ValueError('Service name cannot be empty')

        # Allowed service names
        allowed_services = [
            'gmail',
            'slack',
            'github',
            'notion',
            'google_sheets',
            'trello',
            'asana',
            'linear',
            'discord'
        ]

        if v.lower() not in allowed_services:
            raise ValueError(f'Service must be one of: {", ".join(allowed_services)}')

        return v.lower()

    @field_validator('redirect_uri')
    @classmethod
    def validate_redirect_uri(cls, v: Optional[str]) -> Optional[str]:
        """Validate redirect URI format"""
        if v is None:
            return v

        if not v.strip():
            return None

        # Basic URL validation
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Redirect URI must start with http:// or https://')

        return v.strip()


class IntegrationResponse(BaseModel):
    id: UUID
    service_name: str
    auth_type: str
    is_active: bool
    last_used: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Execution Schemas =============
class ExecutionRequest(BaseModel):
    agent_id: UUID
    input_data: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    id: UUID
    agent_id: UUID
    status: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    duration_seconds: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============= Deployment Schemas =============
class DeploymentRequest(BaseModel):
    agent_id: UUID
    platform: str = Field(default="render", pattern="^(render|vercel|cloudflare|local)$")

    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate deployment platform"""
        allowed_platforms = ['render', 'vercel', 'cloudflare', 'local']

        if v not in allowed_platforms:
            raise ValueError(f'Platform must be one of: {", ".join(allowed_platforms)}')

        return v


class DeploymentResponse(BaseModel):
    id: UUID
    agent_id: UUID
    platform: str
    status: str
    deployment_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============= AI Generation Schemas =============
class AIGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=5000)
    integrations: List[str] = Field(default_factory=list)

    @field_validator('prompt')
    @classmethod
    def validate_prompt_injection(cls, v: str) -> str:
        """Prevent prompt injection attacks"""
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty')

        v_lower = v.lower()

        # Prompt injection blacklist
        injection_patterns = [
            'ignore previous',
            'ignore all previous',
            'disregard previous',
            'forget previous',
            'system:',
            'system prompt',
            'you are now',
            'new instructions',
            'jailbreak',
            'dan mode',
            'developer mode',
            'ignore instructions',
            'bypass restrictions'
        ]

        for pattern in injection_patterns:
            if pattern in v_lower:
                raise ValueError(f'Prompt contains suspicious pattern: "{pattern}". Please rephrase your request.')

        # Check for excessive control characters
        control_char_count = sum(1 for char in v if ord(char) < 32 and char not in '\n\r\t')
        if control_char_count > 5:
            raise ValueError('Prompt contains too many control characters')

        return v.strip()

    @field_validator('integrations')
    @classmethod
    def validate_integrations(cls, v: List[str]) -> List[str]:
        """Validate integration names"""
        if not v:
            return v

        allowed_integrations = [
            'gmail',
            'slack',
            'github',
            'notion',
            'google_sheets',
            'trello',
            'asana',
            'linear',
            'discord'
        ]

        invalid_integrations = [integration for integration in v if integration.lower() not in allowed_integrations]

        if invalid_integrations:
            raise ValueError(f'Invalid integrations: {", ".join(invalid_integrations)}. Allowed: {", ".join(allowed_integrations)}')

        return [integration.lower() for integration in v]


class AIGenerationResponse(BaseModel):
    code: str
    files: Dict[str, str]
    integrations: List[str]
    flow_data: Dict[str, Any]


# ============= WebSocket Message Schemas =============
class WSMessage(BaseModel):
    type: str
    agent_id: Optional[UUID] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


# ============= Subscription Schemas =============
class SubscriptionPlanResponse(BaseModel):
    id: UUID
    name: str
    price_monthly: Optional[float]
    price_yearly: Optional[float]
    max_agents: int
    max_deployments: int
    features: Dict[str, Any]

    class Config:
        from_attributes = True
