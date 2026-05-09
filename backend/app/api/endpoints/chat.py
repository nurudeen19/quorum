"""Chat HTTP: validate input, delegate conversation + briefing flow to :class:`~app.services.chat_service.ChatService`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_history_service
from app.config import get_settings
from app.graph.briefing_graph import BriefingState
from app.models.user import User
from app.schema.conversation import ChatStreamRequest
from app.services.chat_service import (
    ChatService,
    chat_stream_state_payload,
    get_chat_service,
)
from app.services.exceptions import ConversationNotFoundError
from app.services.history_service import HistoryService

router = APIRouter()


@router.post(
    "/stream",
    summary="Stream a message in a conversation",
    description=(
        "Messages always belong to a **conversation**; users may have many. "
        "**New thread:** omit `conversation_id` and send `briefing_context` "
        "(attendees + goal). **Continue:** send `conversation_id` and `content` only."
    ),
    response_class=StreamingResponse,
)
async def chat_stream(
    body: ChatStreamRequest,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    history: HistoryService = Depends(get_history_service),
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """Delegate conversation resolution, history, graph run, and persistence to ``ChatService``."""
    settings = get_settings()
    user_text = body.resolved_user_message()
    if len(user_text) > settings.max_user_input_chars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message exceeds maximum length.",
        )

    try:
        conversation_id, history_text = await chat_service.begin_user_turn(
            session,
            history,
            user_id=current.id,
            conversation_id=body.conversation_id,
            user_content=user_text,
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from None

    async def event_stream():
        yield chat_service.sse_event({"event": "meta", "conversation_id": str(conversation_id)})
        final_state: BriefingState | None = None
        async for state in chat_service.stream_briefing_values(
            user_message=user_text,
            conversation_history=history_text,
            user_id=current.id,
            conversation_id=conversation_id,
        ):
            final_state = state
            yield chat_service.sse_event(
                {"event": "state", "data": chat_stream_state_payload(state)}
            )
        if final_state is not None:
            await chat_service.record_assistant_turn(
                session,
                history,
                conversation_id=conversation_id,
                state=final_state,
            )
        yield chat_service.sse_event({"event": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
