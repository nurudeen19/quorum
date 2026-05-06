"""User API schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """User creation schema."""
    email: str = Field(
        description="User email address",
        examples=["user@example.com"]
    )
    username: str = Field(
        description="Unique username",
        examples=["johndoe"]
    )
    password: str = Field(
        min_length=8,
        description="User password (minimum 8 characters)",
        examples=["securepassword123"]
    )
    full_name: str | None = Field(
        default=None,
        description="User full name", 
        examples=["John Doe"]
    )


class UserResponse(BaseModel):
    """User response schema."""
    id: UUID = Field(
        description="Unique user identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    email: str = Field(
        description="User email address",
        examples=["user@example.com"]
    )
    username: str = Field(
        description="Unique username",
        examples=["johndoe"]
    )
    full_name: str | None = Field(
        description="User full name",
        examples=["John Doe"]
    )
    is_active: bool = Field(
        description="User active status",
        examples=[True]
    )
    is_verified: bool = Field(
        description="Email verification status",
        examples=[False]
    )
    created_at: datetime = Field(
        description="User creation timestamp",
        examples=["2026-05-06T10:30:00Z"]
    )
    updated_at: datetime = Field(
        description="Last update timestamp",
        examples=["2026-05-06T10:30:00Z"]
    )
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User update schema."""
    full_name: str | None = Field(
        default=None,
        description="User full name",
        examples=["John Doe"]
    )
    is_active: bool | None = Field(
        default=None,
        description="User active status",
        examples=[True]
    )


class UserLogin(BaseModel):
    """User login schema."""
    email: str = Field(
        description="User email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        description="User password",
        examples=["securepassword123"]
    )