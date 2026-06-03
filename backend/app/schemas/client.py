from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime

class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: str | None = None
    phone: str | None = None

class ClientCreate(ClientBase):
    hourly_rate_cents: int | None = Field(None, ge=0)

class ClientUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    email: str | None = None
    phone: str | None = None
    hourly_rate_cents: int | None = Field(None, ge=0)

class ClientResponseViewer(ClientBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime

class ClientResponse(ClientResponseViewer):
    hourly_rate_cents: int | None

class ClientListItemViewer(ClientResponseViewer):
    project_count: int

class ClientListItem(ClientResponse):
    project_count: int
