import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger("api.exception")

def setup_exception_handlers(app: FastAPI):
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = exc.headers.get("code") if exc.headers else None
        if not code:
            code = "HTTP_ERROR"
            if exc.status_code == 404:
                code = "NOT_FOUND"
            elif exc.status_code == 401:
                code = "UNAUTHORIZED"
            elif exc.status_code == 403:
                code = "FORBIDDEN"
            elif exc.status_code == 400:
                code = "BAD_REQUEST"
            elif exc.status_code == 422:
                code = "UNPROCESSABLE_ENTITY"
            
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": code}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "code": "INTERNAL_ERROR"}
        )
