"""Role schema."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class RoleRead(BaseModel):
    """Role read schema."""

    id: uuid.UUID
    name: str
    description: str | None = None
    is_system: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
