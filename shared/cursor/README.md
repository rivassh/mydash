"""README for cursor strategies in the unified dashboard.

The cursor system is designed to be pluggable so that different data sources
(can be any platform like Mimo Code, OpenCode, Kir.dev, or any other) can use
their own cursor format while the rest of the system remains agnostic.

## How it works

1. Each connector (e.g., Bale, Eitaa, Telegram) specifies a `cursor_strategy`
   in its config (default: `"iso"`).
2. The `CursorFactory` creates the appropriate strategy instance.
3. The sync engine uses the connector's cursor factory to encode/decode cursors.
4. The API layer passes cursors through without modification.

## Available strategies

- `iso` (default): Base64-encoded ISO 8601 timestamp
- `mimo`: Prefix `mimo:` + base64-encoded ISO timestamp
- `open_code`: Prefix `open:` + base64-encoded Unix milliseconds
- `raw`: Raw string passthrough (no encoding)

## Usage

```python
from shared.cursor import CursorFactory

factory = CursorFactory("mimo")
cursor = factory.encode_cursor(datetime.utcnow())
dt = factory.decode_cursor(cursor)
```

## Adding a new strategy

1. Create a new file in `shared/cursor/strategies/` implementing `CursorStrategy`
2. Register it in `CursorFactory._strategies`
3. Document it here

"""