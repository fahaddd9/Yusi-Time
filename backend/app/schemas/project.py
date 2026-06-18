from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    client_id: UUID | None = None
    default_billable: bool = True
    visibility: str = "public"
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

class ProjectCreate(ProjectBase):
    budget_hours: float | None = Field(None, gt=0)
    budget_amount_cents: int | None = Field(None, gt=0)
    hourly_rate_cents: int | None = Field(None, ge=0)

class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    client_id: UUID | None = None
    default_billable: bool | None = None
    visibility: str | None = None
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    budget_hours: float | None = Field(None, gt=0)
    budget_amount_cents: int | None = Field(None, gt=0)
    hourly_rate_cents: int | None = Field(None, ge=0)
    status: str | None = Field(None, pattern="^(active|archived)$")

class ProjectResponseViewer(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    client_name: str | None = None
    status: str
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

class ProjectResponse(ProjectResponseViewer):
    budget_hours: float | None = None
    budget_amount_cents: int | None = None
    hourly_rate_cents: int | None = None

class ProjectListItemViewer(ProjectResponseViewer):
    hours_logged: float | None = None

class ProjectListItem(ProjectResponse):
    hours_logged: float | None = None

class ProjectMemberCreate(BaseModel):
    user_id: UUID

class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: UUID
    user_id: UUID
    added_at: datetime
    added_by_user_id: UUID | None = None
