"""Registration, login, tokens, email verification, password reset."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.auth_limits import (
    rate_auth_forgot_password,
    rate_auth_login,
    rate_auth_logout,
    rate_auth_refresh,
    rate_auth_register,
    rate_auth_reset_password,
    rate_auth_verify,
)
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.schema.auth import (
    ForgotPasswordRequest,
    LogoutRequest,
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
@limiter.limit(rate_auth_register)
async def register(
    request: Request,
    response: Response,
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
@limiter.limit(rate_auth_login)
async def login(
    request: Request,
    response: Response,
    payload: UserLogin,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        access, refresh = await auth.login(session, payload.login, payload.password)
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
@limiter.limit(rate_auth_refresh)
async def refresh_tokens(
    request: Request,
    response: Response,
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        access, new_refresh = await auth.refresh(session, payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout (revoke refresh token)",
)
@limiter.limit(rate_auth_logout)
async def logout(
    request: Request,
    response: Response,
    payload: LogoutRequest,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await auth.logout(session, payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return MessageResponse(detail="Session ended. Refresh token revoked.")


@router.get(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email (link)",
)
@limiter.limit(rate_auth_verify)
async def verify_email_get(
    request: Request,
    response: Response,
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
@limiter.limit(rate_auth_verify)
async def verify_email_post(
    request: Request,
    response: Response,
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
@limiter.limit(rate_auth_forgot_password)
async def forgot_password(
    request: Request,
    response: Response,
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
@limiter.limit(rate_auth_reset_password)
async def reset_password(
    request: Request,
    response: Response,
    payload: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await auth.reset_password(session, payload.token, payload.password)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(detail="Password updated. You can sign in.")
