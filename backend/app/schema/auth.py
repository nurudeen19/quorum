"""Authentication request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schema.user import UserResponse


class TokenResponse(BaseModel):
    """OAuth2-style token pair returned by login and refresh."""

    access_token: str = Field(description="JWT access token for Authorization: Bearer")
    refresh_token: str = Field(description="JWT refresh token for /auth/refresh")
    token_type: str = Field(default="bearer", examples=["bearer"])


class RegisterResponse(BaseModel):
    """Outcome of self-service registration."""

    user: UserResponse
    detail: str = Field(
        default="Registration successful. Check your email to verify your account.",
    )


class RefreshRequest(BaseModel):
    """Body for exchanging a refresh token for new tokens."""

    refresh_token: str = Field(description="Refresh JWT returned from login")


class ForgotPasswordRequest(BaseModel):
    """Start password reset (always appears successful to callers)."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Complete password reset using the emailed opaque token."""

    token: str = Field(min_length=10, description="Token from the reset link")
    password: str = Field(min_length=8, description="New password")


class VerifyEmailBody(BaseModel):
    """Optional JSON body alternative to the query token."""

    token: str = Field(min_length=10)


class MessageResponse(BaseModel):
    """Simple status payload."""

    detail: str
