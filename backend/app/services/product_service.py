"""Product service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Business logic for products."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductRepository(db)

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        category: str | None = None,
    ) -> tuple[list[Product], int]:
        """List products with pagination + filters."""
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if category:
            filters["category"] = category
        return self.repo.list(
            offset=(page - 1) * page_size,
            limit=page_size,
            filters=filters,
            search=search,
        )

    def get(self, product_id: uuid.UUID) -> Product:
        """Return a product by ID or raise."""
        product = self.repo.get(product_id)
        if not product:
            raise NotFoundError("Product not found")
        return product

    def create(self, payload: ProductCreate, *, actor_id: uuid.UUID | None = None) -> Product:
        """Create a product. Raises on duplicate SKU."""
        if self.repo.get_by_sku(payload.sku):
            raise ConflictError("SKU already exists")
        data = payload.model_dump()
        if actor_id:
            data["owner_id"] = actor_id
        # metadata is reserved keyword in pydantic, remap
        if "metadata" in data:
            data["metadata_json"] = data.pop("metadata")
        product = self.repo.create(data)
        self.db.commit()
        return product

    def update(self, product_id: uuid.UUID, payload: ProductUpdate) -> Product:
        """Update a product."""
        product = self.get(product_id)
        data = payload.model_dump(exclude_unset=True)
        if "sku" in data and data["sku"] and data["sku"] != product.sku:
            existing = self.repo.get_by_sku(data["sku"])
            if existing and existing.id != product_id:
                raise ConflictError("SKU already exists")
        if "metadata" in data:
            data["metadata_json"] = data.pop("metadata")
        updated = self.repo.update(product, data)
        self.db.commit()
        return updated

    def delete(self, product_id: uuid.UUID) -> None:
        """Delete a product."""
        product = self.get(product_id)
        self.repo.delete(product)
        self.db.commit()
