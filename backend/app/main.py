from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging, RequestLoggingMiddleware
from app.core.exceptions import setup_exception_handlers
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.workspaces import router as workspaces_router
from app.routers.members import router as members_router
from app.routers.invites import workspace_invites_router, public_invites_router
from app.routers.clients import router as clients_router
from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router
from app.routers.tags import router as tags_router
from app.routers.time_entries import router as time_entries_router

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

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")
app.include_router(members_router, prefix="/api/v1")
app.include_router(workspace_invites_router, prefix="/api/v1")
app.include_router(public_invites_router, prefix="/api/v1")
app.include_router(clients_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(tags_router, prefix="/api/v1")
app.include_router(time_entries_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
