from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clerk_user_id: str
    email: EmailStr | None = None
    full_name: str | None = None
    created_at: datetime
    updated_at: datetime