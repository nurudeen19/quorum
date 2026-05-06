"""Registration, login, tokens, email verification, password reset."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schema.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    RefreshRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailBody,
)
from app.schema.user import UserCreate, UserLogin, UserResponse
from app.services import (
    AuthService,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserConflictError,
)


def get_auth_service() -> AuthService:
    return AuthService()


router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register",
)
async def register(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    try:
        user = await auth.register(session, payload)
    except UserConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    detail = (
        "Registration successful. You can sign in."
        if user.is_verified
        else "Registration successful. Check your email to verify your account."
    )
    return RegisterResponse(user=UserResponse.model_validate(user), detail=detail)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
)
async def login(
    payload: UserLogin,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        access, refresh = await auth.login(session, payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except EmailNotVerifiedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
)
async def refresh_tokens(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        access, new_refresh = await auth.refresh(session, payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.get(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email (link)",
)
async def verify_email_get(
    token: str = Query(..., min_length=10),
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await auth.verify_email(session, token)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(detail="Email verified. You can sign in.")


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email (JSON)",
)
async def verify_email_post(
    payload: VerifyEmailBody,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await auth.verify_email(session, payload.token)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(detail="Email verified. You can sign in.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth.request_password_reset(session, payload.email)
    return MessageResponse(
        detail="If an account exists for that email, reset instructions were sent.",
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
)
async def reset_password(
    payload: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await auth.reset_password(session, payload.token, payload.password)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(detail="Password updated. You can sign in.")
