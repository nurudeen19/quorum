"""Transactional email via the official Mailtrap Python SDK."""

from __future__ import annotations

import asyncio
import logging

import mailtrap as mt
import structlog

from app.config import get_settings
from app.services.email_render import render_password_reset, render_verify_email

logger = structlog.get_logger(__name__)
_std_log = logging.getLogger(__name__)


async def send_email(
    *,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    """Send multipart email when Mailtrap is configured; otherwise log for local dev."""
    settings = get_settings().app
    if not settings.mailtrap_api_token:
        logger.info(
            "email_skipped_no_provider",
            to=to_email,
            subject=subject,
            text=text_body,
            html=html_body,
        )
        return

    client = mt.MailtrapClient(token=settings.mailtrap_api_token)
    mail = mt.Mail(
        sender=mt.Address(email=settings.mail_from_email, name=settings.mail_from_name),
        to=[mt.Address(email=to_email)],
        subject=subject,
        text=text_body,
        html=html_body,
    )

    def _send() -> None:
        client.send(mail)

    try:
        await asyncio.to_thread(_send)
    except Exception:
        _std_log.exception("mailtrap_send_failed", extra={"to": to_email})
        raise
    logger.info("email_sent", to=to_email, subject=subject)


async def send_verification_email(to_email: str, token: str) -> None:
    """Send the verify-email message using HTML + text templates."""
    settings = get_settings().app
    link = f"{settings.frontend_app_base_url.rstrip('/')}/verify-email?token={token}"
    html, text = render_verify_email(app_name=settings.app_name, verify_link=link)
    await send_email(
        to_email=to_email,
        subject=f"{settings.app_name}: verify your email",
        text_body=text,
        html_body=html,
    )


async def send_password_reset_email(to_email: str, token: str) -> None:
    """Send the password-reset message using HTML + text templates."""
    settings = get_settings().app
    link = f"{settings.frontend_app_base_url.rstrip('/')}/reset-password?token={token}"
    html, text = render_password_reset(app_name=settings.app_name, reset_link=link)
    await send_email(
        to_email=to_email,
        subject=f"{settings.app_name}: reset your password",
        text_body=text,
        html_body=html,
    )
