# models/api_key_models.py - API key data models
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


class UserApiKeyBase(BaseModel):
    limits: Dict[str, int] = Field(default_factory=lambda: {"requests_per_day": 1000, "requests_per_hour": 100})


class UserApiKeyCreate(UserApiKeyBase):
    pass


class UserApiKeyUpdate(BaseModel):
    is_active: Optional[bool] = None
    limits: Optional[Dict[str, int]] = None


class UserApiKeyResponse(UserApiKeyBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserApiKeyGenerateResponse(BaseModel):
    id: int
    user_id: int
    key: str
    limits: Dict[str, int]
    created_at: datetime
    expires_at: Optional[datetime] = None