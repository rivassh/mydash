"""Cursor/pagination encoding utilities for unified dashboard."""

import base64
from datetime import datetime, timezone
from typing import Optional, Tuple


def encode_cursor(dt: datetime) -> str:
    """
    Encode a datetime to a base64 cursor.
    
    The cursor is a base64-encoded ISO format timestamp.
    Used for cursor-based pagination across all services.
    
    Args:
        dt: The datetime to encode
        
    Returns:
        Base64-encoded cursor string
    """
    # Ensure timezone-aware datetime in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    
    iso_format = dt.isoformat()
    cursor = base64.b64encode(iso_format.encode()).decode()
    return cursor


def decode_cursor(cursor: str) -> Optional[datetime]:
    """
    Decode a base64 cursor to a datetime.
    
    Args:
        cursor: The base64-encoded cursor string
        
    Returns:
        Datetime object or None if cursor is empty/invalid
    """
    if not cursor or not cursor.strip():
        return None
    
    try:
        decoded_bytes = base64.b64decode(cursor)
        decoded_str = decoded_bytes.decode()
        dt = datetime.fromisoformat(decoded_str)
        # Ensure UTC if naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def cursor_to_timestamp(cursor: str) -> Optional[float]:
    """
    Convert cursor to Unix timestamp.
    
    Args:
        cursor: The base64-encoded cursor string
        
    Returns:
        Unix timestamp in seconds, or None if invalid
    """
    dt = decode_cursor(cursor)
    if dt is None:
        return None
    return dt.timestamp()


def timestamp_to_cursor(ts: float) -> str:
    """
    Convert Unix timestamp to cursor.
    
    Args:
        ts: Unix timestamp in seconds
        
    Returns:
        Base64-encoded cursor string
    """
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return encode_cursor(dt)


class CursorRange:
    """Represents a range defined by two cursors."""
    
    def __init__(self, start_cursor: Optional[str] = None, end_cursor: Optional[str] = None):
        self.start_cursor = start_cursor
        self.end_cursor = end_cursor
    
    def has_start(self) -> bool:
        return self.start_cursor is not None and self.start_cursor.strip() != ""
    
    def has_end(self) -> bool:
        return self.end_cursor is not None and self.end_cursor.strip() != ""
    
    def to_dict(self) -> dict:
        return {
            "start_cursor": self.start_cursor,
            "end_cursor": self.end_cursor,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CursorRange":
        return cls(
            start_cursor=data.get("start_cursor"),
            end_cursor=data.get("end_cursor"),
        )