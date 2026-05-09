"""User API schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr = Field(
        description="User email address",
        examples=["user@example.com"],
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

    model_config = ConfigDict(from_attributes=True)

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
    """Sign-in payload: email **or** username (same field), plus password."""

    model_config = ConfigDict(extra="ignore")

    login: str = Field(
        min_length=1,
        description="Email address or username (as registered).",
        examples=["user@example.com", "johndoe"],
    )
    password: str = Field(
        description="User password",
        examples=["securepassword123"],
    )

    @field_validator("login", mode="before")
    @classmethod
    def strip_login(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="before")
    @classmethod
    def legacy_email_field(cls, data: Any) -> Any:
        """Accept older clients that send ``email`` instead of ``login``."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        login_val = out.get("login")
        if (login_val is None or (isinstance(login_val, str) and not login_val.strip())) and out.get(
            "email"
        ):
            out["login"] = str(out["email"]).strip()
        return out