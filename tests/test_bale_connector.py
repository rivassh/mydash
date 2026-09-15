"""BDD-style tests for Bale connector functionality."""

import pytest
from app.connectors.bale.connector import BaleConnector


@pytest.mark.asyncio
class TestBaleConnectorMockMode:
    """Test Bale connector in mock mode."""

    async def test_connector_initialization_mock_mode(self):
        """Test that Bale connector initializes correctly in mock mode."""
        config = {
            "mode": "mock",
            "base_url": "https://api.bale.com",
            "session_id": "test-session-id",
            "user_id": "test-user-id",
            "request_timeout": 30,
            "rate_limit_sec": 1
        }
        
        connector = BaleConnector(source_id=1, config=config)
        
        assert connector.mode == "mock"
        assert connector.source_id == 1
        assert connector.base_url == "https://api.bale.com"

    async def test_test_connection_mock_mode(self):
        """Test that connection test passes in mock mode."""
        config = {
            "mode": "mock",
            "base_url": "https://api.bale.com",
            "session_id": "test-session-id",
            "user_id": "test-user-id"
        }
        
        connector = BaleConnector(source_id=1, config=config)
        result = await connector.test_connection()
        
        assert result is True

    async def test_sync_conversations_mock_mode(self):
        """Test fetching conversations in mock mode."""
        config = {
            "mode": "mock",
            "base_url": "https://api.bale.com",
            "session_id": "test-session-id",
            "user_id": "test-user-id"
        }
        
        connector = BaleConnector(source_id=1, config=config)
        
        # Test first page
        conversations = await connector.sync_conversations(cursor=None, limit=5)
        
        assert len(conversations) == 5
        for conv in conversations:
            assert "remote_conversation_id" in conv
            assert "title" in conv
            assert "last_message_preview" in conv
            assert isinstance(conv["unread_count"], int)
        
        # Test with cursor (pagination)
        if len(conversations) == 5:  # We got a full page
            cursor = str(5)  # Mock mode uses numeric cursor
            conversations2 = await connector.sync_conversations(cursor=cursor, limit=5)
            assert len(conversations2) == 5
            # Ensure no overlap
            first_ids = {c["remote_conversation_id"] for c in conversations}
            second_ids = {c["remote_conversation_id"] for c in conversations2}
            assert len(first_ids.intersection(second_ids)) == 0

    async def test_fetch_messages_mock_mode(self):
        """Test fetching messages in mock mode."""
        config = {
            "mode": "mock",
            "base_url": "https://api.bale.com",
            "session_id": "test-session-id",
            "user_id": "test-user-id"
        }
        
        connector = BaleConnector(source_id=1, config=config)
        
        messages = await connector.fetch_messages(
            conversation_remote_id="test_conv_123",
            cursor=None,
            limit=10
        )
        
        assert len(messages) == 10  # Mock returns 10 messages
        for msg in messages:
            assert "source_message_id" in msg
            assert "direction" in msg
            assert msg["direction"] in ["in", "out"]
            assert "sender_name" in msg
            assert "body_text" in msg
            assert "created_at" in msg

    async def test_rate_limiting(self):
        """Test that rate limiting is applied."""
        import time
        config = {
            "mode": "mock",
            "base_url": "https://api.bale.com",
            "session_id": "test-session-id",
            "user_id": "test-user-id",
            "rate_limit_sec": 0.1  # 100ms for fast test
        }
        
        connector = BaleConnector(source_id=1, config=config)
        
        start = time.time()
        await connector._rate_limit_delay()
        await connector._rate_limit_delay()
        elapsed = time.time() - start
        
        # Should have waited at least 0.2 seconds (2 * 0.1)
        assert elapsed >= 0.2


@pytest.mark.asyncio
class TestBaleConnectorRealModeStructure:
    """Test that Bale connector has proper structure for real mode."""

    async def test_connector_has_required_methods(self):
        """Test that connector implements required interface methods."""
        config = {
            "mode": "mock",
            "base_url": "https://api.bale.com",
            "session_id": "test-session-id",
            "user_id": "test-user-id"
        }
        
        connector = BaleConnector(source_id=1, config=config)
        
        # Check that required methods exist
        assert hasattr(connector, 'sync_conversations')
        assert hasattr(connector, 'fetch_messages')
        assert hasattr(connector, 'test_connection')
        assert callable(getattr(connector, 'sync_conversations'))
        assert callable(getattr(connector, 'fetch_messages'))
        assert callable(getattr(connector, 'test_connection'))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])