"""Bale messaging platform connector."""

import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import hmac
import time
from app.connectors.base import BaseConnector
from shared.cursor import CursorFactory

logger = structlog.get_logger()


class BaleConnector(BaseConnector):
    """Connector for Bale messaging platform."""

    def __init__(self, source_id: int, config: Dict[str, Any]):
        super().__init__(source_id, config)
        self.base_url = config.get("base_url", "https://api.bale.com")
        self.session_id = config.get("session_id", "")
        self.user_id = config.get("user_id", "")
        self.request_timeout = config.get("request_timeout", 30)
        self.mode = config.get("mode", "mock").lower()
        # Cursor strategy: "iso" (default), "mimo", "open_code", or custom
        cursor_strategy = config.get("cursor_strategy", "iso")
        self.cursor_factory = CursorFactory(cursor_strategy)
        self.headers = {
            "Authorization": f"Bearer {self.session_id}",
            "Content-Type": "application/json",
        }
        self.logger = self.logger.bind(mode=self.mode)

    async def test_connection(self) -> bool:
        """Test connection to Bale API."""
        if self.mode == "mock":
            self.logger.info("Bale connector in mock mode - connection test passed")
            return True
            
        # In real mode, attempt a simple API call
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/user/me",
                    headers=self.headers,
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            self.logger.warning("Bale connection test failed", error=str(e))
            return False

    async def sync_conversations(self, cursor: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Sync conversations from Bale.
        
        In mock mode, returns sample data.
        In real mode, makes API calls to Bale endpoints.
        """
        await self._rate_limit_delay()
        
        if self.mode == "mock":
            conversations = self._mock_conversations(cursor, limit)
            # If we have a next cursor, include it in the last conversation for the sync engine to pick up
            if self._last_cursor and conversations:
                conversations[-1]["_next_cursor"] = self._last_cursor
            return conversations
        
        # Real Bale API implementation would go here
        # This is a placeholder showing the structure
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                params = {"limit": limit}
                if cursor:
                    params["cursor"] = cursor
                    
                response = await client.get(
                    f"{self.base_url}/v1/chats",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Normalize Bale response to internal format
                conversations = []
                for chat in data.get("chats", []):
                    conversations.append({
                        "remote_conversation_id": str(chat["id"]),
                        "title": chat.get("title") or chat.get("peer", {}).get("username") or f"Chat {chat['id']}",
                        "avatar_url": chat.get("peer", {}).get("avatar"),
                        "last_message_at": self._parse_bale_timestamp(chat.get("last_message_time")),
                        "last_message_preview": self._extract_last_message_preview(chat.get("last_message")),
                        "unread_count": chat.get("unread_count", 0),
                    })
                
                # Update cursor for pagination
                next_cursor = data.get("pagination", {}).get("next_cursor")
                if next_cursor:
                    # Store cursor info for client
                    pass
                    
                return conversations
                
        except Exception as e:
            self.logger.error("Failed to sync conversations", error=str(e))
            raise

    async def fetch_messages(
        self, 
        conversation_remote_id: str, 
        cursor: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch messages for a conversation from Bale.
        
        In mock mode, returns sample messages.
        In real mode, calls Bale messages endpoint.
        """
        await self._rate_limit_delay()
        
        if self.mode == "mock":
            return self._mock_messages(conversation_remote_id, cursor, limit)
        
        # Real implementation
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                params = {"limit": limit}
                if cursor:
                    params["cursor"] = cursor
                    
                response = await client.get(
                    f"{self.base_url}/v1/chats/{conversation_remote_id}/messages",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                messages = []
                for msg in data.get("messages", []):
                    messages.append({
                        "source_message_id": str(msg["id"]),
                        "direction": "in" if msg.get("outgoing") is False else "out",
                        "sender_name": msg.get("sender", {}).get("username", "Unknown"),
                        "body_text": msg.get("text", ""),
                        "body_type": msg.get("type", "text"),
                        "created_at": self._parse_bale_timestamp(msg.get("date")),
                    })
                
                return messages
                
        except Exception as e:
            self.logger.error("Failed to fetch messages", error=str(e), conversation_id=conversation_remote_id)
            raise

    def _mock_conversations(self, cursor: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Generate mock conversation data for development."""
        # Decode cursor using the cursor factory (handles multiple formats)
        if cursor and cursor.strip():
            dt = self.cursor_factory.decode_cursor(cursor)
            if dt:
                start_idx = int(dt.timestamp()) % 1000  # Use timestamp as index
            else:
                start_idx = 0
        else:
            start_idx = 0
        conversations = []
        
        for i in range(start_idx, min(start_idx + limit, start_idx + 20)):  # 20 total mock convs
            conversations.append({
                "remote_conversation_id": f"bale_conv_{i}",
                "title": f"Mock Conversation {i}",
                "avatar_url": f"https://example.com/avatar{i}.jpg",
                "last_message_at": self._get_mock_timestamp(hours_ago=i*2),
                "last_message_preview": f"This is a mock message from conversation {i}",
                "unread_count": i % 3,  # 0, 1, 2 unread
            })
        
        # Return next cursor if more data available
        if start_idx + limit < 20:
            self._last_cursor = self.cursor_factory.encode_cursor(self._get_mock_timestamp(hours_ago=0))
        else:
            self._last_cursor = None
            
        return conversations

    def _mock_messages(self, conversation_remote_id: str, cursor: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Generate mock message data for development."""
        start_idx = int(cursor) if cursor and cursor.isdigit() else 0
        messages = []
        
        # Generate 5-15 messages per conversation
        msg_count = min(limit, 10 + (hash(conversation_remote_id) % 5))
        
        for i in range(start_idx, start_idx + msg_count):
            messages.append({
                "source_message_id": f"{conversation_remote_id}_msg_{i}",
                "direction": "in" if i % 2 == 0 else "out",
                "sender_name": "Mock User" if i % 2 == 0 else "You",
                "body_text": f"Mock message {i} in conversation {conversation_remote_id}",
                "body_type": "text",
                "created_at": self._get_mock_timestamp(hours_ago=i),
            })
        
        return messages

    def _parse_bale_timestamp(self, ts: Any) -> Optional[datetime]:
        """Parse Bale timestamp to datetime."""
        if not ts:
            return None
        try:
            # Bale might send Unix timestamp or ISO string
            if isinstance(ts, (int, float)):
                return datetime.fromtimestamp(ts / 1000.0)  # Assuming milliseconds
            elif isinstance(ts, str):
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            pass
        return None

    def _extract_last_message_preview(self, last_message: Any) -> str:
        """Extract preview text from last message object."""
        if not last_message:
            return ""
        if isinstance(last_message, dict):
            return last_message.get("text", "")[:200]  # Limit preview length
        return str(last_message)[:200]

    def _get_mock_timestamp(self, hours_ago: int = 0) -> datetime:
        """Generate a mock timestamp for testing."""
        from datetime import timedelta
        return datetime.utcnow() - timedelta(hours=hours_ago)