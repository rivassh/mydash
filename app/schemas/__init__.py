"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ConversationList(BaseModel):
    """Conversation summary for list view."""
    id: int
    source_id: int
    remote_conversation_id: str
    title: str
    avatar_url: Optional[str] = None
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    unread_count: int = 0
    archived: bool = False
    pinned: bool = False
    sync_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageList(BaseModel):
    """Message item for list view."""
    id: int
    source_message_id: str
    direction: str
    sender_name: Optional[str] = None
    body_text: str
    body_type: Optional[str] = "text"
    created_at: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class SyncStatus(BaseModel):
    """Sync state for a source."""
    source_id: int
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    cursor: str = ""
    in_progress: bool = False


class SyncRunResponse(BaseModel):
    """Response from triggering a sync run."""
    source_id: int
    source_type: str
    status: str  # "started", "completed", "failed"
    job_id: Optional[str] = None
    message: str


class SourceInfo(BaseModel):
    """Information about an available source."""
    id: int
    type: str
    name: str
    configured: bool

    class Config:
        from_attributes = True


class SourceListResponse(BaseModel):
    """Response for GET /sources endpoint."""
    sources: List[SourceInfo]
    available_types: List[str] = ["bale"]


class SyncStatusResponse(BaseModel):
    """Response for GET /sync/status endpoint."""
    source_id: int
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    cursor: str = ""
    in_progress: bool = False


class CursorResponse(BaseModel):
    """Cursor for pagination continuation."""
    cursor: Optional[str]
    has_more: bool


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: Optional[datetime] = None
    services: Optional[dict] = None