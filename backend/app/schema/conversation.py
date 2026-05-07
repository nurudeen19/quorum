"""Conversation and message API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
