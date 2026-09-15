"""Test configuration and fixtures."""

import os
import pytest
from app.db.session import AsyncSession
from sqlalchemy import event
from app.db.models import Base

# Override DB host for tests
os.environ["DB_HOST"] = "localhost"


@pytest.fixture
async def db_session():
    """Provide a database session for tests."""
    from app.db.session import async_session_maker
    async with async_session_maker() as session:
        # Create tables before test
        await Base.metadata.create_all(session)
        yield session
        # Cleanup after test
        await session.rollback()