"""Campaigns CRUD endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationDep, pagination_dep
from app.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.campaign_service import CampaignService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[CampaignRead],
    summary="List campaigns",
)
def list_campaigns(
    db: Annotated[Session, Depends(get_db)],
    pagination: Annotated[PaginationDep, Depends(pagination_dep)],
    status: str | None = Query(default=None, pattern="^(active|draft|paused|archived)$"),
    channel: str | None = Query(default=None),
) -> dict:
    """List campaigns with filters."""
    service = CampaignService(db)
    items, total = service.list(
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        status=status,
        channel=channel,
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
    "/{campaign_id}",
    response_model=CampaignRead,
    summary="Get a campaign",
)
def get_campaign(
    campaign_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Return a campaign by ID."""
    return CampaignService(db).get(campaign_id)


@router.post(
    "",
    response_model=CampaignRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a campaign",
)
def create_campaign(
    payload: CampaignCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Create a new campaign."""
    return CampaignService(db).create(payload, actor_id=actor.id)


@router.patch(
    "/{campaign_id}",
    response_model=CampaignRead,
    summary="Update a campaign",
)
def update_campaign(
    campaign_id: uuid.UUID,
    payload: CampaignUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update an existing campaign."""
    return CampaignService(db).update(campaign_id, payload)


@router.delete(
    "/{campaign_id}",
    response_model=MessageResponse,
    summary="Delete a campaign",
)
def delete_campaign(
    campaign_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Delete a campaign."""
    CampaignService(db).delete(campaign_id)
    return {"message": "Campaign deleted"}
