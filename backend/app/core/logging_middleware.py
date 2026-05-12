from time import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time()
        user_id = None
        conversation_id = None
        # Try to extract user_id from request.state (set by dependencies) or JWT claims
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        # Try to extract conversation_id from path/query/body
        if "conversation_id" in request.path_params:
            conversation_id = request.path_params["conversation_id"]
        elif "conversation_id" in request.query_params:
            conversation_id = request.query_params["conversation_id"]
        # Optionally, parse JSON body for conversation_id (skip for performance)
        try:
            response = await call_next(request)
        except Exception as exc:
            duration = time() - start_time
            logger.error(
                "request_error",
                method=request.method,
                path=request.url.path,
                status=500,
                duration_ms=int(duration * 1000),
                user_id=user_id,
                conversation_id=conversation_id,
                error=str(exc),
            )
            raise
        duration = time() - start_time
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=int(duration * 1000),
            user_id=user_id,
            conversation_id=conversation_id,
        )
        return response
