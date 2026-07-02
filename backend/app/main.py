from contextlib import asynccontextmanager
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
from app.routers.notifications import router as notifications_router
from app.routers.approvals import router as approvals_router
from app.routers.push_subscriptions import router as push_subscriptions_router
from app.routers.attendance import router as attendance_router
from app.routers.reports import router as reports_router
from app.services.scheduler_service import start_scheduler, stop_scheduler

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Starts the APScheduler (F1 + F2 attendance jobs) on startup.
    Stops it cleanly on shutdown — Addendum §5.2, RULE B-06.
    """
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Yusi Time API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

setup_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

# Mount attendance_router early so its static paths (/time-entries/daily-progress,
# /workspaces/{id}/attendance-settings) are evaluated BEFORE the dynamic 
# /{id} paths in workspaces_router and time_entries_router.
app.include_router(attendance_router, prefix="/api/v1")

app.include_router(workspaces_router, prefix="/api/v1")
app.include_router(members_router, prefix="/api/v1")
app.include_router(workspace_invites_router, prefix="/api/v1")
app.include_router(public_invites_router, prefix="/api/v1")
app.include_router(clients_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(tags_router, prefix="/api/v1")
app.include_router(time_entries_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(push_subscriptions_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
