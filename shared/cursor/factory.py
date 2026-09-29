"""Cursor factory for unified pagination across different platforms."""

from typing import Optional
from datetime import datetime

from shared.cursor.strategies.base import CursorStrategy
from shared.cursor.strategies.iso import Base64ISOCursorStrategy
from shared.cursor.strategies.mimo import MimoCodeCursorStrategy
from shared.cursor.strategies.open_code import OpenCodeCursorStrategy
from shared.cursor.strategies.raw import RawCursorStrategy


class CursorFactory:
    """Factory for creating cursor instances based on strategy.
    
    This factory provides a unified interface to work with different
    cursor encoding/decoding strategies used across various platforms
    (Mimo, OpenCode, generic ISO, etc.).
    
    Usage:
        factory = CursorFactory()
        
        # Use default ISO strategy
        cursor = factory.encode_cursor(datetime.utcnow())
        dt = factory.decode_cursor(cursor)
        
        # Use specific strategy
        factory = CursorFactory("mimo")
        cursor = factory.encode_cursor(dt)
        
        # List available strategies
        for name in factory.list_strategies():
            strategy = factory.get_strategy(name)
            print(f"{name}: {strategy.cursor_format}")
    """
    
    _strategies = {}
    _default_strategy = "iso"
    
    def __init__(self, default_strategy: Optional[str] = None):
        """Initialize cursor factory with available strategies.
        
        Args:
            default_strategy: Name of default strategy (iso, mimo, open_code)
        """
        self._initialize_strategies()
        
        if default_strategy and default_strategy in self._strategies:
            self._default_strategy = default_strategy
        else:
            # Use the first strategy if default not found
            self._default_strategy = next(iter(self._strategies.keys()))
    
    def _initialize_strategies(self):
        """Initialize available cursor strategies."""
        self._strategies = {
            "iso": Base64ISOCursorStrategy(),
            "mimo": MimoCodeCursorStrategy(),
            "open_code": OpenCodeCursorStrategy(),
            "raw": RawCursorStrategy(),
        }
    
    def encode_cursor(self, dt: datetime, strategy_name: Optional[str] = None) -> str:
        """Encode datetime to cursor using specified strategy.
        
        Args:
            dt: The datetime to encode
            strategy_name: Name of strategy to use (defaults to factory default)
            
        Returns:
            Encoded cursor string
        """
        strategy = self.get_strategy(strategy_name) if strategy_name else self.get_strategy(self._default_strategy)
        return strategy.encode_cursor(dt)
    
    def decode_cursor(self, cursor: str, strategy_name: Optional[str] = None) -> Optional[datetime]:
        """Decode cursor string to datetime using specified strategy.
        
        Args:
            cursor: The cursor string to decode
            strategy_name: Name of strategy to use (try all if not specified)
            
        Returns:
            Decoded datetime or None if decoding failed
        """
        if strategy_name:
            strategy = self._get_strategy(strategy_name)
            return strategy.decode_cursor(cursor)
        else:
            # Try all strategies in order of preference
            for strategy in self._strategies.values():
                dt = strategy.decode_cursor(cursor)
                if dt is not None:
                    return dt
            return None
    
    def get_strategy(self, strategy_name: str) -> CursorStrategy:
        """Get a specific cursor strategy instance.
        
        Args:
            strategy_name: Name of strategy to retrieve
            
        Returns:
            CursorStrategy instance
            
        Raises:
            KeyError: If strategy name is not found
        """
        if strategy_name not in self._strategies:
            raise KeyError(f"Unknown cursor strategy: {strategy_name}")
        return self._strategies[strategy_name]
    
    def list_strategies(self) -> list[str]:
        """List all available strategy names.
        
        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())
    
    def get_strategy_for_cursor(self, cursor: str) -> Optional[CursorStrategy]:
        """Determine which strategy can decode the given cursor.
        
        Args:
            cursor: The cursor string to analyze
            
        Returns:
            Matching CursorStrategy or None if no strategy can decode it
        """
        for strategy in self._strategies.values():
            if strategy.decode_cursor(cursor) is not None:
                return strategy
        return None
    
    def __repr__(self) -> str:
        return (
            f"CursorFactory(default={self._default_strategy}, "
            f"strategies={list(self._strategies.keys())})"
    )