"""SQLAlchemy engine, session factory and declarative base."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Tune the connection pool for PostgreSQL so a burst of concurrent requests from
# the admin panel never queues waiting for a free connection. SQLite (tests/dev
# fallback) uses its own pool and ignores these kwargs, so only pass them for PG.
_engine_kwargs: dict = {"pool_pre_ping": True, "future": True}
if settings.DATABASE_URL.startswith("postgresql"):
    _engine_kwargs.update(
        pool_size=20,
        max_overflow=20,
        pool_recycle=1800,
        pool_timeout=10,
    )

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator:
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
