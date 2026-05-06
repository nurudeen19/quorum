"""Render auth-related HTML and plain-text emails from Jinja2 templates."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _template_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "templates" / "email"


@lru_cache
def _jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(_template_dir()),
        autoescape=select_autoescape(["html", "htm", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_verify_email(*, app_name: str, verify_link: str) -> tuple[str, str]:
    """Return (html, plain_text) for the verification message."""
    env = _jinja_env()
    ctx = {"app_name": app_name, "verify_link": verify_link}
    html = env.get_template("verify_email.html").render(**ctx)
    text = env.get_template("verify_email.txt").render(**ctx)
    return html, text


def render_password_reset(*, app_name: str, reset_link: str) -> tuple[str, str]:
    """Return (html, plain_text) for the password reset message."""
    env = _jinja_env()
    ctx = {"app_name": app_name, "reset_link": reset_link}
    html = env.get_template("password_reset.html").render(**ctx)
    text = env.get_template("password_reset.txt").render(**ctx)
    return html, text
