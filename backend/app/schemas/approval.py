import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

class SubmitWeekRequest(BaseModel):
    week_start: date = Field(..., description="Must be a Monday")

class RejectSubmissionRequest(BaseModel):
    note: str = Field(..., min_length=1)

class TimesheetSubmissionResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    week_start: date
    status: str
    submitted_at: datetime
    reviewed_by_user_id: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    rejection_note: str | None = None

    model_config = ConfigDict(from_attributes=True)
