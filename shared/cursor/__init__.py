"""Cursor/pagination encoding utilities for unified dashboard.

This module provides cursor encoding/decoding utilities with support
for multiple cursor formats across different platforms:

- ISO: Base64-encoded ISO 8601 timestamp (default)
- Mimo: Mimo platform format (mimo:base64_iso)
- OpenCode: Open platform format (open:base64_millis)
- Raw: Raw string passthrough

Usage:
    from shared.cursor import CursorFactory, encode_cursor, decode_cursor
    
    # Use factory for multiple strategies
    factory = CursorFactory("mimo")
    cursor = factory.encode_cursor(datetime.utcnow())
    dt = factory.decode_cursor(cursor)
    
    # Use default helpers (ISO format)
    cursor = encode_cursor(datetime.utcnow())
    dt = decode_cursor(cursor)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from shared.cursor.strategies.base import CursorStrategy
from shared.cursor.strategies.iso import Base64ISOCursorStrategy
from shared.cursor.strategies.mimo import MimoCodeCursorStrategy
from shared.cursor.strategies.open_code import OpenCodeCursorStrategy
from shared.cursor.strategies.raw import RawCursorStrategy
from shared.cursor.factory import CursorFactory


# Legacy helper functions (use ISO strategy for backward compatibility)
_default_iso = Base64ISOCursorStrategy()


def encode_cursor(dt: datetime) -> str:
    """Encode datetime to cursor using default ISO strategy."""
    return _default_iso.encode_cursor(dt)


def decode_cursor(cursor: str) -> Optional[datetime]:
    """Decode cursor to datetime using default ISO strategy."""
    return _default_iso.decode_cursor(cursor)


def cursor_to_timestamp(cursor: str) -> Optional[float]:
    """Convert cursor to Unix timestamp."""
    return _default_iso.cursor_to_timestamp(cursor)


def timestamp_to_cursor(ts: float) -> str:
    """Convert Unix timestamp to cursor."""
    return _default_iso.timestamp_to_cursor(ts)


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


__all__ = [
    # Factory for multi-strategy support
    "CursorFactory",
    # Base strategy class
    "CursorStrategy",
    # Concrete strategies
    "Base64ISOCursorStrategy",
    "MimoCodeCursorStrategy",
    "OpenCodeCursorStrategy",
    # Legacy helpers (backward compatible)
    "encode_cursor",
    "decode_cursor",
    "cursor_to_timestamp",
    "timestamp_to_cursor",
    "CursorRange",
]