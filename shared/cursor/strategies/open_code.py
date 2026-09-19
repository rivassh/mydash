"""Open code cursor strategy - generic open platform format."""

from datetime import datetime, timezone
from typing import Optional
import base64

from shared.cursor.strategies.base import CursorStrategy


class OpenCodeCursorStrategy(CursorStrategy):
    """Cursor strategy for open code format.
    
    Format: open:{base64_timestamp_millis}
    
    Uses Unix milliseconds encoded in base64 for compactness.
    
    Example:
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        cursor = strategy.encode_cursor(dt)
        # Returns: "open:MTcwOTY2NzIwMDAwMA=="
    """
    
    PREFIX = "open:"
    
    @property
    def cursor_format(self) -> str:
        return "open-code"
    
    def encode_cursor(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        ts_millis = int(dt.timestamp() * 1000)
        encoded = base64.b64encode(str(ts_millis).encode()).decode()
        return f"{self.PREFIX}{encoded}"
    
    def decode_cursor(self, cursor: str) -> Optional[datetime]:
        if not cursor or not cursor.strip():
            return None
        
        if not cursor.startswith(self.PREFIX):
            return None
        
        try:
            encoded = cursor[len(self.PREFIX):]
            decoded_bytes = base64.b64decode(encoded)
            ts_millis = int(decoded_bytes.decode())
            dt = datetime.fromtimestamp(ts_millis / 1000.0, tz=timezone.utc)
            return dt
        except Exception:
            return None