from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime

class TaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    assignee_user_id: UUID | None = None
    estimated_hours: float | None = Field(None, gt=0)
    billable_override: bool | None = None

class TaskCreate(TaskBase):
    project_id: UUID
    hourly_rate_cents: int | None = Field(None, ge=0)

class TaskUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    assignee_user_id: UUID | None = None
    estimated_hours: float | None = Field(None, gt=0)
    billable_override: bool | None = None
    hourly_rate_cents: int | None = Field(None, ge=0)

class TaskResponseViewer(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

class TaskResponse(TaskResponseViewer):
    hourly_rate_cents: int | None = None
