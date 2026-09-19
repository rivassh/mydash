"""Mimo code cursor strategy - custom format for Mimo platform."""

from datetime import datetime, timezone
from typing import Optional
import base64

from shared.cursor.strategies.base import CursorStrategy


class MimoCodeCursorStrategy(CursorStrategy):
    """Cursor strategy for Mimo code format.
    
    Format: mimo:{base64_iso_timestamp}
    
    Example:
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        cursor = strategy.encode_cursor(dt)
        # Returns: "mimo:MjAyNC0wMS0wMVQxMjowMDowMFo="
    """
    
    PREFIX = "mimo:"
    
    @property
    def cursor_format(self) -> str:
        return "mimo-code"
    
    def encode_cursor(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        iso_str = dt.isoformat()
        encoded = base64.b64encode(iso_str.encode()).decode()
        return f"{self.PREFIX}{encoded}"
    
    def decode_cursor(self, cursor: str) -> Optional[datetime]:
        if not cursor or not cursor.strip():
            return None
        
        if not cursor.startswith(self.PREFIX):
            return None
        
        try:
            encoded = cursor[len(self.PREFIX):]
            decoded_bytes = base64.b64decode(encoded)
            decoded_str = decoded_bytes.decode()
            dt = datetime.fromisoformat(decoded_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None