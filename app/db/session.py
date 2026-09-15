"""Database session management for async SQLAlchemy."""

import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

DB_USER = os.getenv("DB_USER", "chatdash")
DB_PASSWORD = os.getenv("DB_PASSWORD", "chatdash")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "chatdash")

ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    """FastAPI dependency for DB session."""
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def session_scope() -> AsyncSession:
    """Context manager for manual session handling."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_engine():
    await engine.dispose()