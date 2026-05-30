from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging, RequestLoggingMiddleware
from app.core.exceptions import setup_exception_handlers
from app.routers.auth import router as auth_router

setup_logging()

app = FastAPI(title="Yusi Time API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

setup_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
