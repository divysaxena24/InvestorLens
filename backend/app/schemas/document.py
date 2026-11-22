from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    filename: str
    mime_type: str
    file_size_bytes: int
    company_name: str | None = None
    report_period: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime