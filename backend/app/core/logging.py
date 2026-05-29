import uuid
import structlog
import logging
import sys
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

def setup_logging():
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        
        logger = structlog.get_logger("api.request")
        
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            
            logger.info("request_completed", status_code=response.status_code)
            return response
        except Exception as e:
            logger.exception("request_failed", exc_info=e)
            raise
