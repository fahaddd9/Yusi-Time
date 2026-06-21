import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class NotificationResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    title: str
    message: str
    event_metadata: dict | None = None
    read_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationReadRequest(BaseModel):
    ids: list[uuid.UUID]
