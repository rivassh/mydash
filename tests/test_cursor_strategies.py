"""Tests for the pluggable cursor strategy system."""

import pytest
from datetime import datetime, timezone

from shared.cursor import (
    CursorFactory,
    encode_cursor,
    decode_cursor,
    Base64ISOCursorStrategy,
    MimoCodeCursorStrategy,
    OpenCodeCursorStrategy,
    RawCursorStrategy,
)


class TestCursorStrategies:
    """Test all cursor strategies."""

    def test_iso_strategy_round_trip(self):
        """Test ISO strategy can encode and decode consistently."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        strategy = Base64ISOCursorStrategy()
        cursor = strategy.encode_cursor(dt)
        decoded = strategy.decode_cursor(cursor)
        assert decoded == dt

    def test_mimo_strategy_round_trip(self):
        """Test Mimo strategy can encode and decode consistently."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        strategy = MimoCodeCursorStrategy()
        cursor = strategy.encode_cursor(dt)
        assert cursor.startswith("mimo:")
        decoded = strategy.decode_cursor(cursor)
        assert decoded == dt

    def test_open_code_strategy_round_trip(self):
        """Test OpenCode strategy can encode and decode consistently."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        strategy = OpenCodeCursorStrategy()
        cursor = strategy.encode_cursor(dt)
        assert cursor.startswith("open:")
        decoded = strategy.decode_cursor(cursor)
        assert decoded == dt

    def test_raw_strategy_round_trip(self):
        """Test Raw strategy can encode and decode ISO strings."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        strategy = RawCursorStrategy()
        cursor = strategy.encode_cursor(dt)
        assert cursor == "2024-01-15T10:30:00+00:00"
        decoded = strategy.decode_cursor(cursor)
        assert decoded == dt

    def test_cursor_factory_default_strategy(self):
        """Test factory uses default strategy."""
        factory = CursorFactory("mimo")
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        cursor = factory.encode_cursor(dt)
        assert cursor.startswith("mimo:")
        assert factory.decode_cursor(cursor) == dt

    def test_cursor_factory_list_strategies(self):
        """Test factory lists all available strategies."""
        factory = CursorFactory()
        strategies = factory.list_strategies()
        assert "iso" in strategies
        assert "mimo" in strategies
        assert "open_code" in strategies
        assert "raw" in strategies

    def test_cursor_factory_get_strategy_for_cursor(self):
        """Test factory can detect strategy from cursor."""
        factory = CursorFactory()
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        cursor = factory.encode_cursor(dt, "open_code")
        strategy = factory.get_strategy_for_cursor(cursor)
        assert strategy is not None
        assert strategy.cursor_format == "open-code"

    def test_legacy_helpers_still_work(self):
        """Test legacy helper functions still work with ISO strategy."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        cursor = encode_cursor(dt)
        decoded = decode_cursor(cursor)
        assert decoded == dt
