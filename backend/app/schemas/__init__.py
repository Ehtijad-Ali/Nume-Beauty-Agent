"""Pydantic v2 schemas (request/response models)."""

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest, LogoutRequest
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate, CampaignList
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationParams, MessageResponse, IDResponse
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentRead, KnowledgeDocumentUpdate
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate, ProductList
from app.schemas.role import RoleRead
from app.schemas.setting import SettingCreate, SettingRead, SettingUpdate, SettingBulkUpdate
from app.schemas.token import TokenPayload
from app.schemas.upload import UploadCreate, UploadRead, UploadUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserList, UserBrief

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshRequest",
    "LogoutRequest",
    "CampaignCreate",
    "CampaignRead",
    "CampaignUpdate",
    "CampaignList",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationParams",
    "MessageResponse",
    "IDResponse",
    "KnowledgeDocumentCreate",
    "KnowledgeDocumentRead",
    "KnowledgeDocumentUpdate",
    "ProductCreate",
    "ProductRead",
    "ProductUpdate",
    "ProductList",
    "RoleRead",
    "SettingCreate",
    "SettingRead",
    "SettingUpdate",
    "SettingBulkUpdate",
    "TokenPayload",
    "UploadCreate",
    "UploadRead",
    "UploadUpdate",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserList",
    "UserBrief",
]
