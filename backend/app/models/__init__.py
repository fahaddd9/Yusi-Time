# Import all models here so that:
# 1. SQLAlchemy's mapper is aware of every table (needed by Alembic autogenerate)
# 2. All relationship forward-refs resolve correctly at startup

from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.invite import Invite
from app.models.audit_log import AuditLog
from app.models.notification import Notification

# Phase 3 Models
from app.models.client import Client
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.tag import Tag

__all__ = [
    "User",
    "PasswordResetToken",
    "Workspace",
    "WorkspaceMember",
    "Invite",
    "AuditLog",
    "Notification",
    "Client",
    "Project",
    "ProjectMember",
    "Task",
    "Tag",
]
