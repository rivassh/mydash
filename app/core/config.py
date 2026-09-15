"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Centralised application settings."""
    app_name: str = "chatdash"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"
    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "chatdash"
    db_user: str = "chatdash"
    db_password: str = "chatdash"
    bale_connectors: dict = None
    sync_config: dict = None

    def dict(self):
        """Convert to dictionary."""
        return {
            "app_name": self.app_name,
            "app_host": self.app_host,
            "app_port": self.app_port,
            "log_level": self.log_level,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "db_user": self.db_user,
            "db_password": self.db_password,
            "bale_connectors": self.bale_connectors,
            "sync_config": self.sync_config,
        }


def load_settings() -> Settings:
    """Build Settings from environment variables."""
    bale = {
        "mode": os.getenv("BALE_CONNECTOR_MODE", "mock").lower(),
        "base_url": os.getenv("BALE_BASE_URL", "https://api.bale.com"),
        "session_id": os.getenv("BALE_SESSION_ID", ""),
        "user_id": os.getenv("BALE_USER_ID", ""),
        "request_timeout": int(os.getenv("BALE_REQUEST_TIMEOUT", "30")),
        "rate_limit_sec": int(os.getenv("BALE_RATE_LIMIT_SECONDS", "1")),
    }
    sync = {
        "interval": int(os.getenv("SYNC_INTERVAL_SECONDS", "300")),
        "batch_size": int(os.getenv("SYNC_BATCH_SIZE", "100")),
        "initial_depth": int(os.getenv("SYNC_INITIAL_DEPTH", "50")),
        "max_batch": int(os.getenv("SYNC_MAX_MESSAGE_BATCH", "200")),
    }
    return Settings(
        app_name=os.getenv("APP_NAME", "chatdash"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "info"),
        db_host=os.getenv("DB_HOST", "db"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.getenv("DB_NAME", "chatdash"),
        db_user=os.getenv("DB_USER", "chatdash"),
        db_password=os.getenv("DB_PASSWORD", "chatdash"),
        bale_connectors=bale,
        sync_config=sync,
    )


# Create global settings instance
settings = load_settings()