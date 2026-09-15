"""Main entry point for the ChatDash API."""
import signal
import asyncio
import logging
from fastapi.middleware.baseshape import BaseHTTPMiddleware
from contextvars import contextvar
from app.db.session import AsyncSession, async_sessionmaker
from app.core.config import settings
from app.api.main import app
from app.logging import setup_logging
from app.schemas import SyncStatus


def graceful_exit():
    """Close async database session on SIGINT/SIGTERM."""
    async def shutdown():
        async_sessionmaker.remove()
        await async_sessionmaker().close()
        sys.exit(0)
    
    return shutdown


# Setup structured logging
logger = setup_logging(settings.log_level)

# Create logger instance
import structlog
log = structlog.get_logger()

# Add signal handlers
signal.signal(signal.SIGINT, lambda *args: graceful_exit())
signal.signal(signal.SIGTERM, lambda *args: graceful_exit())

# Create database session variable accessible to modules
session_cache = contextvar.AsyncContextVar("session")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting ChatDash API server")
    logger.info("Configuration", settings=settings.dict())
    uvicorn.run(app, host="0.0.0.0", port=settings.app_port)