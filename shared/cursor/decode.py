"""Cursor decoding utilities."""

import base64
from datetime import datetime, timezone
from typing import Optional


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