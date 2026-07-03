"""Repository layer — data access classes."""

from app.repositories.audit_log_repo import AuditLogRepository
from app.repositories.base import BaseRepository
from app.repositories.campaign_repo import CampaignRepository
from app.repositories.knowledge_repo import KnowledgeDocumentRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.setting_repo import SettingRepository
from app.repositories.upload_repo import UploadRepository
from app.repositories.user_repo import UserRepository

__all__ = [
    "AuditLogRepository",
    "BaseRepository",
    "CampaignRepository",
    "KnowledgeDocumentRepository",
    "ProductRepository",
    "RoleRepository",
    "SessionRepository",
    "SettingRepository",
    "UploadRepository",
    "UserRepository",
]
