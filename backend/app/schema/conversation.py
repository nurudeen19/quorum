"""Conversation and message API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


MessageRole = Literal["user", "assistant", "system"]


class MessageCreate(BaseModel):
    """Create a message."""

    role: MessageRole = Field(description="Message role")
    content: str = Field(description="Message body")


class MessageResponse(BaseModel):
    """Persisted message."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationCreate(BaseModel):
    """Create a conversation."""

    title: str | None = Field(default=None, description="Optional title")


class ConversationResponse(BaseModel):
    """Conversation metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationWithMessagesResponse(BaseModel):
    """Conversation with recent messages."""

    conversation: ConversationResponse
    messages: list[MessageResponse]


class ConversationListItem(BaseModel):
    """One row for the authenticated user's conversation list."""

    id: UUID
    title: str | None = Field(description="First user line or explicit title when set.")
    created_at: datetime
    updated_at: datetime


class ConversationMessagesResponse(BaseModel):
    """All messages in a conversation (oldest first)."""

    conversation_id: UUID
    messages: list[MessageResponse]


class AttendeeBriefing(BaseModel):
    """One person relevant to the briefing (first message only)."""

    name: str = Field(min_length=1, max_length=500, examples=["Jordan Lee"])
    company: str | None = Field(
        default=None,
        max_length=500,
        examples=["Acme Corp"],
        description="Company for this attendee, if known.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("name must be a non-empty string")
        return value.strip()

    @field_validator("company", mode="before")
    @classmethod
    def empty_company_to_none(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            s = value.strip()
            return s if s else None
        raise TypeError("company must be a string or null")


class BriefingContext(BaseModel):
    """Structured first turn: who + goal. Used only when ``conversation_id`` is omitted."""

    attendees: list[AttendeeBriefing] = Field(
        min_length=1,
        max_length=50,
        description="One or more attendees (name and optional company each).",
    )
    goal: str = Field(
        min_length=1,
        max_length=50_000,
        examples=["Prepare for a 30-min intro with focus on their Q3 roadmap."],
    )

    @field_validator("goal", mode="before")
    @classmethod
    def strip_goal(cls, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("goal must be a non-empty string")
        return value.strip()


def format_briefing_context_user_message(ctx: BriefingContext) -> str:
    """Canonical user message text stored and sent to the briefing graph."""
    lines = ["Attendees:"]
    for a in ctx.attendees:
        if a.company:
            lines.append(f"- {a.name} ({a.company})")
        else:
            lines.append(f"- {a.name}")
    lines.extend(["", "Goal:", ctx.goal])
    return "\n".join(lines)


class ChatStreamRequest(BaseModel):
    """Stream one user turn: structured first message or free-form follow-up."""

    conversation_id: UUID | None = Field(
        default=None,
        description=(
            "Existing conversation to continue. "
            "Omit to start a new conversation (requires ``briefing_context``)."
        ),
    )
    content: str | None = Field(
        default=None,
        description="Free-form user message when continuing an existing conversation.",
    )
    briefing_context: BriefingContext | None = Field(
        default=None,
        description="Required when ``conversation_id`` is omitted; forbidden when it is set.",
    )

    @model_validator(mode="after")
    def validate_new_vs_continue(self) -> ChatStreamRequest:
        if self.conversation_id is None:
            if self.briefing_context is None:
                raise ValueError(
                    "briefing_context is required when starting a new conversation "
                    "(omit conversation_id)."
                )
            if self.content is not None and self.content.strip():
                raise ValueError(
                    "Do not send content when starting a new conversation; use briefing_context only."
                )
        else:
            if self.briefing_context is not None:
                raise ValueError(
                    "briefing_context is only for new conversations; omit it when conversation_id is set."
                )
            if self.content is None or not str(self.content).strip():
                raise ValueError("content is required when continuing a conversation.")
        return self

    def resolved_user_message(self) -> str:
        """Plain-text user message for persistence and the graph."""
        if self.briefing_context is not None:
            return format_briefing_context_user_message(self.briefing_context)
        assert self.content is not None
        return self.content.strip()
