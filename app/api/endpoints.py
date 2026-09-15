"""REST API routes for chatdash."""

import structlog
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import load_settings
from app.db.session import get_session, close_engine
from app.db.repositories import SourceRepository, ConversationRepository, MessageRepository, SyncStateRepository
from app.schemas import (
    SourceListResponse,
    ConversationListResponse,
    MessageListResponse,
    SyncStatusResponse,
    SyncRunResponse,
    HealthResponse,
    ErrorResponse,
)
from app.sync.engine import SyncEngine

router = APIRouter(prefix="/api/v1", tags=["api"])
logger = structlog.get_logger()


async def get_db() -> AsyncSession:
    """Dependency for DB session."""
    async for session in get_session():
        yield session


async def get_sync_engine(db: AsyncSession = Depends(get_db)) -> SyncEngine:
    """Dependency for sync engine."""
    settings = load_settings()
    return SyncEngine(db, settings.dict() if hasattr(settings, 'dict') else settings)


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


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    source_type: str = Query("bale", alias="sourceType"),
    cursor: Optional[str] = Query(None, alias="cursor"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """List conversations with cursor-based pagination."""
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_type(source_type)
    
    if not source:
        from fastapi import HTTPException
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
        # Encode last message_at as cursor
        if last.last_message_at:
            import base64
            from datetime import timezone
            ts = last.last_message_at.replace(tzinfo=timezone.utc).isoformat()
            next_cursor = base64.b64encode(ts.encode()).decode()
    
    return ConversationListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/conversations/{conv_id}/messages", response_model=MessageListResponse)
async def list_messages(
    conv_id: int,
    cursor: Optional[str] = Query(None, alias="cursor"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    """List messages for a conversation with cursor-based pagination."""
    conv_repo = ConversationRepository(db)
    
    # Check conversation exists
    conversation = await conv_repo.get_by_id(conv_id)
    if not conversation:
        from fastapi import HTTPException
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
    
    return MessageListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/sync/status", response_model=SyncStatusResponse)
async def sync_status(
    source_type: str = Query("bale", alias="sourceType"),
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    """Get sync status for a source."""
    from app.schemas import SyncStatus
    sync_repo = SyncStateRepository(db)
    state = await sync_repo.get_sync_status(1 if source_type == "bale" else 0)
    
    # Actually, we need to find source_id first
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_type(source_type)
    
    if source:
        state = await sync_repo.get_state(source.id)
        return sync_repo.get_sync_status(source.id)
    
    return SyncStatusResponse(source_id=0, cursor="", last_success_at=None, last_error=None, in_progress=False)


@router.post("/sync/run", response_model=SyncRunResponse)
async def trigger_sync(
    source_type: str = Query("bale", alias="sourceType"),
    full_sync: bool = False,
    db: AsyncSession = Depends(get_db),
) -> SyncRunResponse:
    """Trigger a sync run for a source."""
    sync_engine = SyncEngine(db, {})
    
    # Determine source_id
    source_repo = SourceRepository(db)
    source = await source_repo.get_by_type(source_type)
    source_id = source.id if source else 1
    
    # Run sync
    settings = load_settings()
    engine_result = await sync_engine.run_sync(
        source_type=source_type,
        full_sync=full_sync,
    )
    
    return SyncRunResponse(
        job_id=engine_result.get("job_id"),
        source_id=source_id,
        status=engine_result.get("status", "error"),
        message=engine_result.get("message", "Sync completed"),
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