"""Sync engine for handling incremental synchronization."""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import (
    SourceRepository,
    ConversationRepository,
    MessageRepository,
    SyncStateRepository,
)
from app.db.session import session_scope
from app.connectors.base import BaseConnector
from app.schemas import SyncStatus
from shared.cursor import CursorFactory

logger = structlog.get_logger()


class SyncEngine:
    """Orchestrates incremental sync for a messaging platform source."""

    def __init__(self, connector: BaseConnector):
        self.connector = connector
        self.source_type = connector.config.get("type", "unknown")
        self.logger = logger.bind(connector=self.__class__.__name__)
        self.cursor_factory = getattr(connector, "cursor_factory", CursorFactory())

    async def run_sync(self, batch_size: int = 100) -> SyncStatus:
        """
        Run a single sync cycle.
        
        Args:
            batch_size: Number of items to process per API call
            
        Returns:
            SyncStatus with results
        """
        self.logger.info("Starting sync cycle")
        
        async with session_scope() as db:
            try:
                # Get or create source record
                source_repo = SourceRepository(db)
                source = await source_repo.get_or_create(self.source_type)
                self.logger.info("Source resolved", source_id=source.id)
                
                # Get current sync state
                sync_state_repo = SyncStateRepository(db)
                current_state = await sync_state_repo.get_state(source.id)
                cursor = current_state.cursor if current_state else ""
                
                # Sync conversations
                await self._sync_conversations(source.id, batch_size, cursor, db)
                
                # Update sync state success
                await sync_state_repo.create_or_update_state(
                    source_id=source.id,
                    cursor=cursor,  # Will be updated by _sync_conversations
                    last_success_at=datetime.utcnow()
                )
                
                self.logger.info("Sync cycle completed successfully")
                return await sync_state_repo.get_sync_status(source.id)
                
            except Exception as e:
                self.logger.error("Sync cycle failed", error=str(e))
                # Mark error state
                if 'source' in locals() and source:
                    sync_state_repo = SyncStateRepository(db)
                    await sync_state_repo.set_error(source.id, str(e))
                
                return SyncStatus(
                    source_id=source.id if 'source' in locals() else None,
                    last_success_at=None,
                    last_error=str(e),
                    cursor="",
                    in_progress=False
                )

    async def _sync_conversations(self, source_id: int, batch_size: int, cursor: str, db: AsyncSession):
        """Sync conversations and their messages."""
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)
        
        # Get conversations from connector
        conversations = await self.connector.sync_conversations(
            cursor=cursor if cursor else None,
            limit=batch_size
        )
        
        self.logger.info(
            "Fetched conversations batch", 
            count=len(conversations),
            cursor=cursor
        )
        
        for conv_data in conversations:
            # Upsert conversation
            conversation = await conversation_repo.upsert_conversation(
                source_id=source_id,
                remote_conversation_id=conv_data["remote_conversation_id"],
                title=conv_data.get("title", ""),
                avatar_url=conv_data.get("avatar_url"),
                last_message_at=conv_data.get("last_message_at"),
                last_message_preview=conv_data.get("last_message_preview"),
                unread_count=conv_data.get("unread_count", 0),
                archived=conv_data.get("archived", False),
                pinned=conv_data.get("pinned", False),
                sync_updated_at=datetime.utcnow()
            )
            
            # Sync messages for this conversation
            await self._sync_messages(
                conversation.id,
                conv_data["remote_conversation_id"],
                batch_size,
                db
            )
        
        # Update cursor if more data available
        if len(conversations) >= batch_size:
            # Use the connector's cursor strategy (could be ISO, Mimo, OpenCode, etc.)
            if conversations:
                last_conv = conversations[-1]
                if last_conv.get("last_message_at"):
                    cursor = self.cursor_factory.encode_cursor(last_conv["last_message_at"])
                    # Update sync state with new cursor
                    sync_state_repo = SyncStateRepository(db)
                    await sync_state_repo.create_or_update_state(
                        source_id=source_id,
                        cursor=cursor,
                        last_success_at=datetime.utcnow()
                    )
                # Also check if connector provided a next cursor
                elif last_conv.get("_next_cursor"):
                    cursor = last_conv["_next_cursor"]
                    sync_state_repo = SyncStateRepository(db)
                    await sync_state_repo.create_or_update_state(
                        source_id=source_id,
                        cursor=cursor,
                        last_success_at=datetime.utcnow()
                    )

    async def _sync_messages(self, conversation_id: int, remote_conversation_id: str, batch_size: int, db: AsyncSession):
        """Sync messages for a specific conversation."""
        message_repo = MessageRepository(db)
        
        # Get messages from connector
        messages = await self.connector.fetch_messages(
            conversation_remote_id=remote_conversation_id,
            limit=batch_size
        )
        
        self.logger.info(
            "Fetched messages batch",
            conversation_id=conversation_id,
            count=len(messages)
        )
        
        for msg_data in messages:
            # Upsert message
            await message_repo.upsert_message(
                conversation_id=conversation_id,
                source_message_id=msg_data["source_message_id"],
                direction=msg_data["direction"],
                sender_name=msg_data.get("sender_name", ""),
                body_text=msg_data.get("body_text", ""),
                created_at=msg_data.get("created_at"),
                body_type=msg_data.get("body_type", "text"),
                status=msg_data.get("status")
            )


async def run_bale_sync(config: Dict[str, Any]) -> SyncStatus:
    """Factory function to run Bale sync."""
    from app.connectors.bale.connector import BaleConnector
    
    connector = BaleConnector(source_id=0, config=config)
    engine = SyncEngine(connector)
    return await engine.run_sync()