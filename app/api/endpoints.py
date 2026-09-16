"""REST API routes for chatdash."""

import structlog
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import load_settings
from app.db.session import get_session
from app.db.repositories import SourceRepository, ConversationRepository, MessageRepository, SyncStateRepository
from app.schemas import (
    SourceInfo,
    SourceListResponse,
    SyncStatusResponse,
    SyncRunResponse,
    HealthResponse,
)
from app.connectors.bale.connector import BaleConnector
from app.sync.engine import SyncEngine

router = APIRouter(prefix="/api/v1", tags=["api"])
logger = structlog.get_logger()


async def get_db() -> AsyncSession:
    """Dependency for DB session."""
    async for session in get_session():
        yield session


@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    db: AsyncSession = Depends(get_db),
) -> SourceListResponse:
    """List available sources."""
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_type("bale")
    
    available_types = ["bale"]
    sources = []
    
    if source:
        sources.append(
            SourceInfo(
                id=source.id,
                type=source.type,
                name="Bale",
            )
        )
    
    return SourceListResponse(sources=sources, available_types=available_types)


@router.get("/conversations")
async def list_conversations(
    source_type: str = Query("bale", alias="sourceType"),
    cursor: Optional[str] = Query(None, alias="cursor"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List conversations with cursor-based pagination."""
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_type(source_type)
    
    if not source:
        raise HTTPException(status_code=404, detail=f"Source type {source_type} not found")
    
    conv_repo = ConversationRepository(db)
    items = await conv_repo.list_conversations(
        source_id=source.id,
        cursor=cursor,
        limit=limit,
    )
    
    # Build next cursor if there are results
    next_cursor = None
    has_more = len(items) == limit
    if items:
        last = items[-1]
        if last.last_message_at:
            import base64
            from datetime import timezone
            ts = last.last_message_at.replace(tzinfo=timezone.utc).isoformat()
            next_cursor = base64.b64encode(ts.encode()).decode()
    
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/conversations/{conv_id}/messages")
async def list_messages(
    conv_id: int,
    cursor: Optional[str] = Query(None, alias="cursor"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List messages for a conversation with cursor-based pagination."""
    conv_repo = ConversationRepository(db)
    
    conversation = await conv_repo.get_by_id(conv_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conv_id} not found")
    
    msg_repo = MessageRepository(db)
    items = await msg_repo.list_messages(
        conversation_id=conv_id,
        cursor=cursor,
        limit=limit,
    )
    
    next_cursor = None
    has_more = len(items) == limit
    if items:
        last = items[-1]
        if last.created_at:
            import base64
            from datetime import timezone
            ts = last.created_at.replace(tzinfo=timezone.utc).isoformat()
            next_cursor = base64.b64encode(ts.encode()).decode()
    
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/sync/status", response_model=SyncStatusResponse)
async def sync_status(
    source_type: str = Query("bale", alias="sourceType"),
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    """Get sync status for a source."""
    sync_repo = SyncStateRepository(db)
    
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_type(source_type)
    
    if source:
        state = await sync_repo.get_state(source.id)
        return SyncStatusResponse(
            source_id=source.id,
            last_success_at=state.last_success_at if state else None,
            last_error=state.last_error_msg if state else None,
            cursor=state.cursor if state else "",
            in_progress=False,
        )
    
    return SyncStatusResponse(source_id=0, cursor="", last_success_at=None, last_error=None, in_progress=False)


@router.post("/sync/run", response_model=SyncRunResponse)
async def trigger_sync(
    source_type: str = Query("bale", alias="sourceType"),
    full_sync: bool = False,
    db: AsyncSession = Depends(get_db),
) -> SyncRunResponse:
    """Trigger a sync run for a source."""
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_type(source_type)
    source_id = source.id if source else 1
    
    connector = BaleConnector(source_id=source_id, config={"mode": "mock"})
    sync_engine = SyncEngine(connector)
    result = await sync_engine.run_sync()
    
    return SyncRunResponse(
        source_id=source_id,
        source_type=source_type,
        status="completed" if not result.last_error else "failed",
        message="Sync completed" if not result.last_error else result.last_error,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness/readiness probe."""
    return HealthResponse(
        status="healthy",
        services={
            "db": "up",
            "api": "up",
        },
    )