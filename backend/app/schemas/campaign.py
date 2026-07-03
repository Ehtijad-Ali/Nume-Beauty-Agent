"""Campaign schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class CampaignBase(BaseModel):
    """Shared campaign fields."""

    name: str = Field(min_length=1, max_length=255)
    channel: str = Field(min_length=1, max_length=50)
    status: str = Field(default="draft", pattern="^(active|draft|paused|archived)$")
    budget: Decimal = Field(default=Decimal("0"), ge=0)
    spent: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    impressions: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    @model_validator(mode="after")
    def _check_dates(self) -> "CampaignBase":
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("end_date must be after start_date")
        if self.spent > self.budget:
            raise ValueError("spent cannot exceed budget")
        return self


class CampaignCreate(CampaignBase):
    """Payload to create a campaign."""

    owner_id: uuid.UUID | None = None


class CampaignUpdate(BaseModel):
    """Payload to update a campaign. All fields optional."""

    name: str | None = Field(default=None, max_length=255)
    channel: str | None = None
    status: str | None = Field(default=None, pattern="^(active|draft|paused|archived)$")
    budget: Decimal | None = Field(default=None, ge=0)
    spent: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    impressions: int | None = Field(default=None, ge=0)
    clicks: int | None = Field(default=None, ge=0)
    conversions: int | None = Field(default=None, ge=0)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    owner_id: uuid.UUID | None = None


class CampaignRead(CampaignBase):
    """Campaign read schema."""

    id: uuid.UUID
    owner_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampaignList(BaseModel):
    """Campaign list item."""

    id: uuid.UUID
    name: str
    channel: str
    status: str
    budget: Decimal
    spent: Decimal
    currency: str
    impressions: int
    clicks: int
    conversions: int
    owner_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
