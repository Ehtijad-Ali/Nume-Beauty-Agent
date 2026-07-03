"""Product schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ProductCreate(BaseModel):
    """Payload to create a product."""

    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None
    price: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    stock: int = Field(default=0, ge=0)
    status: str = Field(default="draft", pattern="^(active|draft|paused|archived)$")
    image_url: str | None = None
    metadata: dict | None = None


class ProductUpdate(BaseModel):
    """Payload to update a product. All fields optional."""

    name: str | None = Field(default=None, max_length=255)
    sku: str | None = Field(default=None, max_length=100)
    category: str | None = None
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    stock: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, pattern="^(active|draft|paused|archived)$")
    image_url: str | None = None
    metadata: dict | None = None


class ProductRead(BaseModel):
    """Product read schema."""

    id: uuid.UUID
    name: str
    sku: str
    category: str | None = None
    description: str | None = None
    price: Decimal
    currency: str
    stock: int
    status: str
    image_url: str | None = None
    owner_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductList(BaseModel):
    """Product list item."""

    id: uuid.UUID
    name: str
    sku: str
    category: str | None = None
    price: Decimal
    stock: int
    status: str
    image_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
