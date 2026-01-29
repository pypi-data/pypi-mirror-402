# models/user_models.py - User-related data models
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Set
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    language: str = "en"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    language: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[int] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# --- User verification models ---

class EmailVerificationRequest(BaseModel):
    """Model for user email verification request."""

    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class ResendVerificationRequest(BaseModel):
    """Model for requesting resend of verification code."""

    email: EmailStr


class SuccessResponse(BaseModel):
    """Model for successful operation response."""

    message: str


# --- User RSS feeds models ---

class UserRSSFeedBase(BaseModel):
    url: str
    name: Optional[str] = None
    category_id: Optional[int] = None
    language: str = "en"


class UserRSSFeedCreate(UserRSSFeedBase):
    pass


class UserRSSFeedUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserRSSFeedResponse(UserRSSFeedBase):
    id: str
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCategoriesUpdate(BaseModel):
    category_ids: Set[int]


class UserCategoriesResponse(BaseModel):
    category_ids: List[int]


# --- Telegram linking models ---

class TelegramLinkResponse(BaseModel):
    link_code: str
    instructions: str


class TelegramLinkStatusResponse(BaseModel):
    is_linked: bool
    telegram_id: Optional[int] = None
    linked_at: Optional[str] = None