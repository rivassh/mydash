"""FastAPI main application."""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import structlog
import logging
import sys

from app.core.config import load_settings
from app.core.logging import setup_logging
from app.db.session import get_session
from app.db.repositories import SourceRepository, ConversationRepository, MessageRepository, SyncStateRepository
from app.schemas import (
    SourceInfo, SourceListResponse, ConversationList, MessageList,
    SyncStatus, SyncRunResponse, HealthResponse, SyncStatusResponse,
    CursorResponse,
)
from app.connectors.bale.connector import BaleConnector
from app.sync.engine import SyncEngine

# Setup logging
logger = setup_logging(str(load_settings().log_level))
settings = load_settings()

app = FastAPI(
    title="ChatDash API",
    version="0.1",
    description="Offline-first messaging aggregator API (Phase 1: Bale)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_db():
    """Verify database connection on startup."""
    logger.info("Starting ChatDash API", app="chatdash", version="0.1")
    try:
        async with get_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            logger.info("Database connection verified")
    except Exception as e:
        logger.warning("Database connection issue", error=str(e))


@app.on_event("shutdown")
async def shutdown_db():
    """Cleanup on shutdown."""
    logger.info("Shutting down ChatDash API")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness/readiness probe."""
    return HealthResponse(
        status="healthy",
        services={"db": "up", "api": "up"},
    )


@app.get("/sources", response_model=SourceListResponse)
async def get_sources(session: AsyncSession = Depends(get_session)):
    """List available sources."""
    source_repo = SourceRepository(session)
    source = await source_repo.get_by_type("bale")
    
    sources = []
    if source:
        sources.append(SourceInfo(id=source.id, type="bale", name="Bale", configured=True))
    else:
        sources.append(SourceInfo(id=0, type="bale", name="Bale", configured=False))
    
    return SourceListResponse(sources=sources, available_types=["bale"])


@app.get("/conversations")
async def get_conversations(
    source_type: str = Query("bale", alias="sourceType"),
    cursor: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """Cursor-based pagination for conversations."""
    if source_type and source_type != "bale":
        raise HTTPException(400, "Only Bale source supported in Phase 1")
    
    source_repo = SourceRepository(session)
    source = await source_repo.get_by_type(source_type)
    source_id = source.id if source else 1
    
    conv_repo = ConversationRepository(session)
    items = await conv_repo.list_conversations(
        source_id=source_id,
        cursor=cursor,
        limit=limit,
    )
    
    # Build next cursor
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


@app.get("/conversations/{conv_id}/messages")
async def get_messages(
    conv_id: int,
    cursor: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """Messages for a specific conversation."""
    conv_repo = ConversationRepository(session)
    conversation = await conv_repo.get_by_id(conv_id)
    if not conversation:
        raise HTTPException(404, f"Conversation {conv_id} not found")
    
    msg_repo = MessageRepository(session)
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


@app.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    source_type: str = Query("bale", alias="sourceType"),
    session: AsyncSession = Depends(get_session),
):
    """Get sync status for a source."""
    source_repo = SourceRepository(session)
    source = await source_repo.get_by_type(source_type)
    
    if source:
        sync_repo = SyncStateRepository(session)
        state = await sync_repo.get_state(source.id)
        if state:
            return SyncStatusResponse(
                source_id=source.id,
                last_success_at=state.last_success_at,
                last_error=state.last_error_msg,
                cursor=state.cursor,
                in_progress=False,
            )
    
    return SyncStatusResponse(source_id=0, cursor="", last_success_at=None, last_error=None, in_progress=False)


@app.post("/sync/run", response_model=SyncRunResponse)
async def trigger_sync(
    source_type: str = Query("bale", alias="sourceType"),
    full_sync: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """Trigger a sync run for a source."""
    if source_type != "bale":
        raise HTTPException(400, "Only Bale source supported in Phase 1")
    
    connector = BaleConnector(source_id=0, config={"mode": "mock"})
    sync_engine = SyncEngine(connector)
    result = await sync_engine.run_sync()
    
    return SyncRunResponse(
        source_id=result.source_id or 0,
        source_type=source_type,
        status="completed" if not result.last_error else "failed",
        job_id=None,
        message="Sync completed" if not result.last_error else result.last_error,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.app_port)