"""Main entry point for the ChatDash API."""
from app.api.main import app
from app.core.config import settings
from app.core.logging import setup_logging

# Setup structured logging
logger = setup_logging(settings.log_level)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting ChatDash API server")
    uvicorn.run(app, host="0.0.0.0", port=settings.app_port)