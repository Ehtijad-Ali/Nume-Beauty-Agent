"""JWT token schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    type: Literal["access", "refresh"]
    iat: int
    exp: int
    jti: str

    model_config = {"from_attributes": True}
