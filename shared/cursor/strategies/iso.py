"""Base64-encoded ISO timestamp cursor strategy (default)."""

from datetime import datetime, timezone
from typing import Optional
import base64

from shared.cursor.strategies.base import CursorStrategy


class Base64ISOCursorStrategy(CursorStrategy):
    """Default cursor strategy: base64-encoded ISO 8601 timestamp.
    
    Example:
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        cursor = strategy.encode_cursor(dt)
        # Returns something like: "MjAyNC0wMS0wMVQxMjowMDowMFo="
        
        decoded = strategy.decode_cursor(cursor)
        # Returns the original datetime
    """
    
    @property
    def cursor_format(self) -> str:
        return "base64-iso"
    
    def encode_cursor(self, dt: datetime) -> str:
        """Encode datetime to base64-encoded ISO string."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        iso_str = dt.isoformat()
        return base64.b64encode(iso_str.encode()).decode()
    
    def decode_cursor(self, cursor: str) -> Optional[datetime]:
        """Decode base64-encoded ISO string to datetime."""
        if not cursor or not cursor.strip():
            return None
        
        try:
            decoded_bytes = base64.b64decode(cursor)
            decoded_str = decoded_bytes.decode()
            dt = datetime.fromisoformat(decoded_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None