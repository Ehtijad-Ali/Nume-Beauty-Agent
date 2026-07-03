"""Campaign service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.campaign import Campaign
from app.repositories.campaign_repo import CampaignRepository
from app.schemas.campaign import CampaignCreate, CampaignUpdate


class CampaignService:
    """Business logic for campaigns."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CampaignRepository(db)

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        channel: str | None = None,
    ) -> tuple[list[Campaign], int]:
        """List campaigns with filters."""
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if channel:
            filters["channel"] = channel
        return self.repo.list(
            offset=(page - 1) * page_size,
            limit=page_size,
            filters=filters,
            search=search,
        )

    def get(self, campaign_id: uuid.UUID) -> Campaign:
        """Return a campaign by ID or raise."""
        campaign = self.repo.get(campaign_id)
        if not campaign:
            raise NotFoundError("Campaign not found")
        return campaign

    def create(self, payload: CampaignCreate, *, actor_id: uuid.UUID | None = None) -> Campaign:
        """Create a campaign."""
        data = payload.model_dump()
        if actor_id and not data.get("owner_id"):
            data["owner_id"] = actor_id
        campaign = self.repo.create(data)
        self.db.commit()
        return campaign

    def update(self, campaign_id: uuid.UUID, payload: CampaignUpdate) -> Campaign:
        """Update a campaign."""
        campaign = self.get(campaign_id)
        data = payload.model_dump(exclude_unset=True)
        updated = self.repo.update(campaign, data)
        self.db.commit()
        return updated

    def delete(self, campaign_id: uuid.UUID) -> None:
        """Delete a campaign."""
        campaign = self.get(campaign_id)
        self.repo.delete(campaign)
        self.db.commit()
