"""Chat HTTP: list/load conversations, stream messages, delegate briefing to ``ChatService``."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_history_service
from app.config import get_settings
from app.graph.briefing_graph import BriefingState
from app.models.user import User
from app.schema.conversation import (
    ChatStreamRequest,
    ConversationListItem,
    ConversationMessagesResponse,
    MessageFeedbackUpdate,
    MessageResponse,
)
from app.services.chat_service import (
    ChatService,
    chat_stream_state_payload,
    get_chat_service,
)
from app.services.exceptions import ConversationNotFoundError
from app.services.history_service import HistoryService

router = APIRouter()


@router.get(
    "/conversations",
    response_model=list[ConversationListItem],
    summary="List my conversations",
)
async def list_my_conversations(
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    history: HistoryService = Depends(get_history_service),
    limit: int = Query(50, ge=1, le=200),
) -> list[ConversationListItem]:
    """Return the authenticated user's briefing threads, newest ``updated_at`` first."""
    rows = await history.list_conversations_for_user(session, current.id, limit=limit)
    return [
        ConversationListItem(
            id=r.id,
            title=r.title,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
    summary="Load messages for a conversation",
)
async def get_conversation_messages(
    conversation_id: UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    history: HistoryService = Depends(get_history_service),
) -> ConversationMessagesResponse:
    """Return all messages in chronological order when the thread belongs to the current user."""
    msgs = await history.list_messages_for_user(session, current.id, conversation_id)
    if msgs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=[MessageResponse.model_validate(m) for m in msgs],
    )


@router.patch(
    "/messages/{message_id}/feedback",
    response_model=MessageResponse,
    summary="Rate an assistant message (thumbs up/down)",
)
async def patch_message_feedback(
    message_id: UUID,
    body: MessageFeedbackUpdate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    history: HistoryService = Depends(get_history_service),
) -> MessageResponse:
    """Set or clear user feedback on an assistant reply (owner's conversation only)."""
    msg = await history.set_message_feedback_for_user(
        session,
        current.id,
        message_id,
        body.feedback,
    )
    if msg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found, not an assistant reply, or not in your conversation.",
        )
    return MessageResponse.model_validate(msg)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
)
async def delete_my_conversation(
    conversation_id: UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    history: HistoryService = Depends(get_history_service),
) -> Response:
    """Remove a conversation and its messages (owner only)."""
    ok = await history.delete_conversation_for_user(session, current.id, conversation_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
