"""Product repository."""

from __future__ import annotations

from typing import Any

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for :class:`Product`."""

    model = Product

    def get_by_sku(self, sku: str) -> Product | None:
        """Return a product by SKU."""
        return self.db.query(Product).filter(Product.sku == sku).first()

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
        search: str | None = None,
        search_fields: list[str] | None = None,
        order_by: str | None = None,
        order_dir: str = "asc",
    ) -> tuple[list[Product], int]:
        """List products with optional filters/search/sort."""
        return super().list(
            offset=offset,
            limit=limit,
            filters=filters,
            search=search,
            search_fields=search_fields or ["name", "sku", "category"],
            order_by=order_by,
            order_dir=order_dir,
        )
