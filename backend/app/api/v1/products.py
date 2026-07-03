"""Products CRUD endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationDep, pagination_dep
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.product import ProductCreate, ProductList, ProductRead, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[ProductList],
    summary="List products",
)
def list_products(
    db: Annotated[Session, Depends(get_db)],
    pagination: Annotated[PaginationDep, Depends(pagination_dep)],
    status: str | None = Query(default=None, pattern="^(active|draft|paused|archived)$"),
    category: str | None = Query(default=None),
) -> dict:
    """List products with pagination, search and filters."""
    service = ProductService(db)
    items, total = service.list(
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        status=status,
        category=category,
    )
    pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get a product",
)
def get_product(
    product_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Return a product by ID."""
    return ProductService(db).get(product_id)


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
def create_product(
    payload: ProductCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Create a new product."""
    return ProductService(db).create(payload, actor_id=actor.id)


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    summary="Update a product",
)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update an existing product."""
    return ProductService(db).update(product_id, payload)


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="Delete a product",
)
def delete_product(
    product_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Delete a product."""
    ProductService(db).delete(product_id)
    return {"message": "Product deleted"}
