from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

class TagResponse(TagBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    created_at: datetime
