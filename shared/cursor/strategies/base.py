"""Base cursor strategy interface for unified dashboard pagination."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class CursorStrategy(ABC):
    """Abstract base class for cursor encoding/decoding strategies.
    
    Each strategy defines how to encode a datetime to a cursor string
    and decode a cursor string back to a datetime.
    
    Subclasses should implement:
    - encode_cursor(dt): Convert datetime to cursor string
    - decode_cursor(cursor): Convert cursor string to datetime
    - cursor_format: Human-readable format name
    """
    
    @property
    @abstractmethod
    def cursor_format(self) -> str:
        """Return a human-readable format name for this strategy."""
    
    @abstractmethod
    def encode_cursor(self, dt: datetime) -> str:
        """Encode a datetime to a cursor string.
        
        Args:
            dt: The datetime to encode (will be normalized to UTC)
            
        Returns:
            Base64-encoded or otherwise formatted cursor string
        """
    
    @abstractmethod
    def decode_cursor(self, cursor: str) -> Optional[datetime]:
        """Decode a cursor string to a datetime.
        
        Args:
            cursor: The cursor string to decode
            
        Returns:
            Datetime object or None if cursor is empty/invalid
        """
    
    def cursor_to_timestamp(self, cursor: str) -> Optional[float]:
        """Convert cursor to Unix timestamp (seconds).
        
        Default implementation decodes cursor then returns timestamp.
        Override if a more direct conversion is needed.
        """
        dt = self.decode_cursor(cursor)
        if dt is None:
            return None
        return dt.timestamp()
    
    def timestamp_to_cursor(self, ts: float) -> str:
        """Convert Unix timestamp to cursor.
        
        Default implementation creates datetime then encodes.
        Override if a more direct conversion is needed.
        """
        from datetime import timezone
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return self.encode_cursor(dt)