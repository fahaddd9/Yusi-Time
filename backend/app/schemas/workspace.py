"""
Workspace Pydantic schemas.

WorkspaceSummary is the lightweight form returned in list views and auth responses.
"""

from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class WorkspaceSummary(BaseModel):
    """Lightweight workspace info — used in lists and auth responses."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    logo_url: Optional[str] = None
    created_at: datetime
