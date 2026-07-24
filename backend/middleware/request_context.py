from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from services.logging_service import new_request_id

logger = logging.getLogger("api.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or new_request_id()
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response: Response = await call_next(request)
            return response
        except Exception:
            logger.exception("request_failed", extra={"request_id": request_id, "path": request.url.path, "method": request.method})
            raise
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            status_code = locals().get("response").status_code if "response" in locals() else 500
            logger.info("request_completed", extra={"request_id": request_id, "path": request.url.path, "method": request.method, "status_code": status_code, "duration_ms": duration_ms})
            if "response" in locals():
                response.headers["x-request-id"] = request_id
