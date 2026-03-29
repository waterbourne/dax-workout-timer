"""
LiveSLA — Database Engine & Session Factory
=============================================

Provides SQLAlchemy engines (sync and async) bound to a local SQLite file
and reusable session factories. All ORM models derive from the ``Base``
declarative base exported here.

Usage (sync):
    from app.database import engine, SessionLocal, Base

    Base.metadata.create_all(bind=engine)       # one-time table creation
    with SessionLocal() as session:             # transactional unit of work
        ...

Usage (async):
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        ...
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ---------------------------------------------------------------------------
# Database file lives alongside the project root for the MVP.
# ---------------------------------------------------------------------------
DB_PATH: Path = Path(__file__).resolve().parent.parent / "livesla.db"
DATABASE_URL: str = f"sqlite:///{DB_PATH}"
ASYNC_DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_PATH}"

# Sync engine (for sync operations, migrations, etc.)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},  # required for SQLite + threads
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Async engine (for the polling engine)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Declarative base for all LiveSLA ORM models."""
