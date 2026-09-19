"""Raw string cursor strategy - passthrough without encoding."""

from datetime import datetime
from typing import Optional

from shared.cursor.strategies.base import CursorStrategy


class RawCursorStrategy(CursorStrategy):
    """Cursor strategy that passes strings through without encoding.
    
    Useful for platforms that use their own cursor format (e.g., 
    "next_page_token", "offset", or custom tokens).
    
    Note: This strategy cannot convert raw strings to datetime.
    Use this only if you don't need to decode cursors back to datetimes.
    """
    
    @property
    def cursor_format(self) -> str:
        return "raw"
    
    def encode_cursor(self, dt: datetime) -> str:
        """Return ISO timestamp as string (no encoding)."""
        return dt.isoformat()
    
    def decode_cursor(self, cursor: str) -> Optional[datetime]:
        """Try to parse as ISO datetime, return None on failure."""
        if not cursor or not cursor.strip():
            return None
        
        try:
            return datetime.fromisoformat(cursor)
        except Exception:
            return None