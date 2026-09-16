"""Cursor encoding utilities."""

from datetime import datetime, timezone
import base64


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
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    iso_format = dt.isoformat()
    cursor = base64.b64encode(iso_format.encode()).decode()
    return cursor