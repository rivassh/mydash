"""Base connector interface for messaging platforms."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class BaseConnector(ABC):
    """Abstract base class for messaging platform connectors."""

    def __init__(self, source_id: int, config: Dict[str, Any]):
        self.source_id = source_id
        self.config = config
        self.logger = logger.bind(connector=self.__class__.__name__)

    @abstractmethod
    async def sync_conversations(self, cursor: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch conversations from the platform.
        
        Args:
            cursor: Pagination cursor for incremental sync
            limit: Maximum number of conversations to fetch
            
        Returns:
            List of normalized conversation dictionaries
        """
        pass

    @abstractmethod
    async def fetch_messages(
        self, 
        conversation_remote_id: str, 
        cursor: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch messages for a specific conversation.
        
        Args:
            conversation_remote_id: Platform-specific conversation ID
            cursor: Pagination cursor for incremental sync
            limit: Maximum number of messages to fetch
            
        Returns:
            List of normalized message dictionaries
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the connector can reach the platform API."""
        pass

    async def _rate_limit_delay(self):
        """Simple rate limiting based on config."""
        delay = self.config.get("rate_limit_sec", 1)
        if delay > 0:
            import asyncio
            await asyncio.sleep(delay)