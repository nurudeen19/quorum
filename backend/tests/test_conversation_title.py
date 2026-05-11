"""Conversation title helpers for briefing threads."""

from __future__ import annotations

from datetime import datetime, timezone

from app.schema.conversation import BriefingContext, briefing_conversation_title


def test_briefing_conversation_title_prefers_company() -> None:
    ctx = BriefingContext(
        attendees=[{"name": "Connor Doyle", "company": "Cause Strategy Partners"}],
        goal="Prepare for intro call.",
    )
    at = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)

    assert briefing_conversation_title(ctx, at=at) == "Cause Strategy Partners · May 11, 2026"


def test_briefing_conversation_title_uses_first_name_without_company() -> None:
    ctx = BriefingContext(
        attendees=[{"name": "Jordan Lee"}],
        goal="Prepare for intro call.",
    )
    at = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)

    assert briefing_conversation_title(ctx, at=at) == "Jordan · May 11, 2026"
