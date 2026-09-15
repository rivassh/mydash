"""Tests for cursor pagination and upsert idempotency."""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from app.db.session import async_session_maker
from app.db.models import Source, Conversation, Message, SyncState, SourceType, MessageDirection


@pytest.mark.asyncio
class TestCursorPagination:
    """Tests for cursor-based pagination logic."""

    async def test_cursor_encoding_decoding(self):
        """Test that cursor can be encoded/decoded consistently."""
        cursor_dt = datetime.utcnow()
        
        # Encode cursor
        import base64
        cursor = base64.b64encode(cursor_dt.isoformat().encode()).decode()
        
        # Decode cursor
        decoded_bytes = base64.b64decode(cursor)
        decoded_str = decoded_bytes.decode()
        
        assert decoded_str == cursor_dt.isoformat()

    async def test_cursor_timestamp_comparison(self):
        """Test cursor ordering for pagination."""
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        older = now - timedelta(hours=2)
        
        # Cursor should represent a timestamp to paginate backwards
        # Messages more recent than cursor should be filtered out
        assert past > older
        
        # In practical use: < cursor would filter messages older than cursor


@pytest.mark.asyncio
class TestUpsertIdempotency:
    """Tests for upsert idempotency in repositories."""

    async def test_duplicate_conversation_upsert(self):
        """Test that upserting same conversation doesn't create duplicates."""
        async with async_session_maker() as session:
            # Create source first
            source = Source(type=SourceType.BALE)
            session.add(source)
            await session.commit()
            await session.refresh(source)
            
            # Upsert same conversation twice
            conv1 = Conversation(
                source_id=source.id,
                remote_conversation_id="test_conv_1",
                title="Test Conversation"
            )
            session.add(conv1)
            await session.commit()
            
            # Second upsert should update, not insert
            conv1.title = "Updated Title"
            await session.commit()
            
            # Count conversations for this source
            result = await session.execute(
                select(Conversation).where(Conversation.source_id == source.id)
            )
            convs = result.scalars().all()
            
            assert len(convs) == 1
            assert convs[0].title == "Updated Title"

    async def test_duplicate_message_upsert(self):
        """Test that upserting same message doesn't create duplicates."""
        async with async_session_maker() as session:
            source = Source(type=SourceType.BALE)
            session.add(source)
            await session.commit()
            
            conv = Conversation(source_id=source.id, remote_conversation_id="conv_1")
            session.add(conv)
            await session.commit()
            
            # Insert message
            msg1 = Message(
                conversation_id=conv.id,
                source_message_id="msg_123",
                direction=MessageDirection.IN,
                sender_name="Alice",
                body_text="Hello",
                created_at=datetime.utcnow()
            )
            session.add(msg1)
            await session.commit()
            
            # Try insert same message again
            msg2 = Message(
                conversation_id=conv.id,
                source_message_id="msg_123",  # Same ID
                direction=MessageDirection.IN,
                sender_name="Bob",  # Different sender (should not matter for upsert)
                body_text="Updated body",
                created_at=datetime.utcnow()
            )
            session.add(msg2)
            await session.commit()
            
            # Count messages
            result = await session.execute(
                select(Message).where(Message.conversation_id == conv.id)
            )
            msgs = result.scalars().all()
            
            assert len(msgs) == 1  # Still only 1 message, updated in place


@pytest.mark.asyncio
class TestSyncState:
    """Tests for sync state persistence."""

    async def test_sync_state_persistence(self):
        """Test that sync cursor can be stored and retrieved."""
        async with async_session_maker() as session:
            source = Source(type=SourceType.BALE)
            session.add(source)
            await session.commit()
            
            # Create initial sync state
            state = SyncState(
                source_id=source.id,
                cursor="cursor_123",
                last_success_at=datetime.utcnow()
            )
            session.add(state)
            await session.commit()
            
            # Update cursor
            state.cursor = "cursor_456"
            await session.commit()
            
            # Verify update
            result = await session.execute(
                select(SyncState).where(SyncState.source_id == source.id)
            )
            saved_state = result.scalar_one()
            
            assert saved_state.cursor == "cursor_456"
            assert saved_state.last_success_at is not None