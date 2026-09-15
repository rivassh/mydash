"""Repository layer for database operations with upsert semantics."""

from sqlalchemy import select, insert, update, delete, func, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db import models
from app.schemas import ConversationList, MessageList, SyncStatus
import structlog

logger = structlog.get_logger()


class SourceRepository:
    """Repository for source operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_type(self, source_type: str) -> Optional[models.Source]:
        """Get source by type."""
        result = await self.db.execute(
            select(models.Source).where(models.Source.type == source_type)
        )
        return result.scalar_one_or_none()
    
    async def get_or_create(self, source_type: str) -> models.Source:
        """Get existing source or create new one."""
        source = await self.get_by_type(source_type)
        if source:
            return source
        
        source = models.Source(type=source_type)
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        logger.info("Created new source", source_type=source_type, source_id=source.id)
        return source


class ConversationRepository:
    """Repository for conversation operations with upsert support."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def upsert_conversation(
        self,
        source_id: int,
        remote_conversation_id: str,
        title: str,
        avatar_url: Optional[str] = None,
        last_message_at: Optional[str] = None,
        last_message_preview: Optional[str] = None,
        unread_count: int = 0,
        archived: bool = False,
        pinned: bool = False,
        sync_updated_at: Optional[str] = None,
    ) -> models.Conversation:
        """Upsert a conversation. Uses unique constraint on (source_id, remote_conversation_id)."""
        stmt = pg_insert(models.Conversation).values(
            source_id=source_id,
            remote_conversation_id=remote_conversation_id,
            title=title,
            avatar_url=avatar_url,
            last_message_at=last_message_at,
            last_message_preview=last_message_preview,
            unread_count=unread_count,
            archived=archived,
            pinned=pinned,
            sync_updated_at=sync_updated_at,
        ).on_conflict_do_update(
            index_elements=["source_id", "remote_conversation_id"],
            set_={
                "title": title,
                "avatar_url": avatar_url,
                "last_message_at": last_message_at,
                "last_message_preview": last_message_preview,
                "unread_count": unread_count,
                "archived": archived,
                "pinned": pinned,
                "sync_updated_at": sync_updated_at,
            },
        ).returning(models.Conversation.id)
        
        try:
            result = await self.db.execute(stmt)
            await self.db.commit()
            # Fetch the conversation to return the full object instead of just the ID
            stmt_select = select(models.Conversation).where(
                models.Conversation.source_id == source_id,
                models.Conversation.remote_conversation_id == remote_conversation_id,
            )
            result_select = await self.db.execute(stmt_select)
            return result_select.scalar_one()
        except Exception as e:
            logger.error("Upsert conversation failed", error=str(e), remote_id=remote_conversation_id)
            # Fallback to manual upsert
            stmt_select = select(models.Conversation).where(
                models.Conversation.source_id == source_id,
                models.Conversation.remote_conversation_id == remote_conversation_id,
            )
            result = await self.db.execute(stmt_select)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.title = title
                existing.avatar_url = avatar_url
                existing.last_message_at = last_message_at
                existing.last_message_preview = last_message_preview
                existing.unread_count = unread_count
                existing.archived = archived
                existing.pinned = pinned
                existing.sync_updated_at = sync_updated_at
                await self.db.commit()
                await self.db.refresh(existing)
                return existing
            else:
                conv = models.Conversation(
                    source_id=source_id,
                    remote_conversation_id=remote_conversation_id,
                    title=title,
                    avatar_url=avatar_url,
                    last_message_at=last_message_at,
                    last_message_preview=last_message_preview,
                    unread_count=unread_count,
                    archived=archived,
                    pinned=pinned,
                    sync_updated_at=sync_updated_at,
                )
                self.db.add(conv)
                await self.db.commit()
                await self.db.refresh(conv)
                return conv
        
        return result.scalar_one()
    
    async def list_conversations(
        self,
        source_id: int,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> List[ConversationList]:
        """List conversations with cursor-based pagination."""
        query = (
            select(models.Conversation)
            .where(models.Conversation.source_id == source_id)
            .order_by(models.Conversation.last_message_at.desc().nullslast())
        )
        
        if cursor:
            # Decode cursor (base64 encoded timestamp)
            import base64
            try:
                decoded = base64.b64decode(cursor).decode("utf-8")
                from datetime import datetime
                cursor_dt = datetime.fromisoformat(decoded)
                query = query.where(models.Conversation.last_message_at <= cursor_dt)
            except Exception:
                logger.warning("Invalid cursor, ignoring", cursor=cursor)
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        items = []
        for conv in conversations:
            items.append(ConversationList(
                id=conv.id,
                source_id=conv.source_id,
                remote_conversation_id=conv.remote_conversation_id,
                title=conv.title,
                avatar_url=conv.avatar_url,
                last_message_at=conv.last_message_at,
                last_message_preview=conv.last_message_preview,
                unread_count=conv.unread_count,
                archived=conv.archived,
                pinned=conv.pinned,
                sync_updated_at=conv.sync_updated_at,
            ))
        
        return items
    
    async def get_by_id(self, conv_id: int) -> Optional[models.Conversation]:
        """Get conversation by ID."""
        result = await self.db.execute(
            select(models.Conversation).where(models.Conversation.id == conv_id)
        )
        return result.scalar_one_or_none()


class MessageRepository:
    """Repository for message operations with upsert support."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def upsert_message(
        self,
        conversation_id: int,
        source_message_id: str,
        direction: str,
        sender_name: str,
        body_text: str,
        created_at,
        body_type: str = "text",
        status: Optional[str] = None,
    ) -> models.Message:
        """Upsert a message. Uses unique constraint on (conversation_id, source_message_id)."""
        # Try PostgreSQL upsert first, fallback to manual
        stmt = pg_insert(models.Message).values(
            conversation_id=conversation_id,
            source_message_id=source_message_id,
            direction=direction,
            sender_name=sender_name,
            body_text=body_text,
            body_type=body_type,
            created_at=created_at,
            status=status,
        ).on_conflict_do_update(
            index_elements=["conversation_id", "source_message_id"],
            set_={
                "direction": direction,
                "sender_name": sender_name,
                "body_text": body_text,
                "body_type": body_type,
                "created_at": created_at,
                "status": status,
            },
        ).returning(models.Message.id)
        
        try:
            result = await self.db.execute(stmt)
            await self.db.commit()
            # Fetch the message to return the full object instead of just the ID
            stmt_select = select(models.Message).where(
                models.Message.conversation_id == conversation_id,
                models.Message.source_message_id == source_message_id,
            )
            result_select = await self.db.execute(stmt_select)
            return result_select.scalar_one()
        except Exception as e:
            logger.warning("PG upsert failed, using fallback", error=str(e))
            stmt_select = select(models.Message).where(
                models.Message.conversation_id == conversation_id,
                models.Message.source_message_id == source_message_id,
            )
            result = await self.db.execute(stmt_select)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.direction = direction
                existing.sender_name = sender_name
                existing.body_text = body_text
                existing.body_type = body_type
                existing.created_at = created_at
                existing.status = status
                await self.db.commit()
                await self.db.refresh(existing)
                return existing
            else:
                msg = models.Message(
                    conversation_id=conversation_id,
                    source_message_id=source_message_id,
                    direction=direction,
                    sender_name=sender_name,
                    body_text=body_text,
                    body_type=body_type,
                    created_at=created_at,
                    status=status,
                )
                self.db.add(msg)
                await self.db.commit()
                await self.db.refresh(msg)
                return msg
    
    async def list_messages(
        self,
        conversation_id: int,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> List[MessageList]:
        """List messages with cursor-based pagination."""
        query = (
            select(models.Message)
            .where(models.Message.conversation_id == conversation_id)
            .order_by(models.Message.created_at.desc())  # newest first for pagination
        )
        
        if cursor:
            import base64
            from datetime import datetime
            try:
                decoded = base64.b64decode(cursor).decode("utf-8")
                cursor_dt = datetime.fromisoformat(decoded)
                query = query.where(models.Message.created_at <= cursor_dt)
            except Exception:
                pass
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        messages = result.scalars().all()
        
        items = []
        for msg in messages:
            items.append(MessageList(
                id=msg.id,
                source_message_id=msg.source_message_id,
                direction=msg.direction.value if hasattr(msg.direction, 'value') else str(msg.direction),
                sender_name=msg.sender_name,
                body_text=msg.body_text,
                body_type=msg.body_type,
                created_at=msg.created_at,
                status=msg.status,
            ))
        
        return items


class SyncStateRepository:
    """Repository for sync state operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_state(self, source_id: int) -> Optional[models.SyncState]:
        """Get sync state for a source."""
        result = await self.db.execute(
            select(models.SyncState).where(models.SyncState.source_id == source_id)
        )
        return result.scalar_one_or_none()
    
    async def create_or_update_state(
        self,
        source_id: int,
        cursor: str,
        last_success_at=None,
        last_error_msg: Optional[str] = None,
    ) -> models.SyncState:
        """Create or update sync state."""
        stmt = pg_insert(models.SyncState).values(
            source_id=source_id,
            cursor=cursor,
            last_success_at=last_success_at,
            last_error_msg=last_error_msg,
            updated_at=func.now(),
        ).on_conflict_do_update(
            index_elements=["source_id"],
            set_={
                "cursor": cursor,
                "last_success_at": last_success_at,
                "last_error_msg": last_error_msg,
                "updated_at": func.now(),
            },
        )
        
        try:
            await self.db.execute(stmt)
        except Exception:
            logger.warning("PG upsert for sync state failed, using fallback")
            existing = await self.get_state(source_id)
            if existing:
                existing.cursor = cursor
                existing.last_success_at = last_success_at
                existing.last_error_msg = last_error_msg
                existing.updated_at = func.now()
            else:
                state = models.SyncState(
                    source_id=source_id,
                    cursor=cursor,
                    last_success_at=last_success_at,
                    last_error_msg=last_error_msg,
                )
                self.db.add(state)
        
        await self.db.commit()
        return await self.get_state(source_id)
    
    async def set_error(self, source_id: int, error_msg: str, at_time=None):
        """Record an error state."""
        await self.create_or_update_state(
            source_id=source_id,
            cursor="",
            last_success_at=None,
            last_error_msg=error_msg,
        )
    
    async def get_sync_status(self, source_id: int) -> SyncStatus:
        """Get formatted sync status."""
        state = await self.get_state(source_id)
        if not state:
            return SyncStatus(
                source_id=source_id,
                last_success_at=None,
                last_error=None,
                cursor="",
                in_progress=False,
            )
        
        return SyncStatus(
            source_id=source_id,
            last_success_at=state.last_success_at,
            last_error=state.last_error_msg,
            cursor=state.cursor,
            in_progress=False,
        )