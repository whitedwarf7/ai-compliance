import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all incoming requests."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        start_time = time.time()

        # Add request ID to request state
        request.state.request_id = request_id

        # Log request
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            },
        )

        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log response
        logger.info(
            f"Response {request_id}: {response.status_code} ({duration_ms}ms)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


