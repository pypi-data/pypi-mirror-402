from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from .engine import get_engine_master, get_engine_tasks

# Lazy-initialized session makers
_yi_async_session_master = None
_yi_async_session_tasks = None


def get_yi_async_session_master():
    """Get or create master session maker (lazy initialization)."""
    global _yi_async_session_master
    if _yi_async_session_master is None:
        _yi_async_session_master = sessionmaker(
            get_engine_master(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _yi_async_session_master


def get_yi_async_session_tasks():
    """Get or create tasks session maker (lazy initialization)."""
    global _yi_async_session_tasks
    if _yi_async_session_tasks is None:
        _yi_async_session_tasks = sessionmaker(
            get_engine_tasks(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _yi_async_session_tasks


def get_yi_async_session():
    """Get default session maker (master)."""
    return get_yi_async_session_master()


async def yi_get_db() -> AsyncSession:
    """Dependency to get DB session (default: master)."""
    session_maker = get_yi_async_session_master()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def yi_get_db_master() -> AsyncSession:
    """Dependency to get master DB session."""
    session_maker = get_yi_async_session_master()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def yi_get_db_tasks() -> AsyncSession:
    """Dependency to get tasks DB session."""
    session_maker = get_yi_async_session_tasks()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# For compatibility with tests
yi_async_session = get_yi_async_session
yi_async_session_master = get_yi_async_session_master
yi_async_session_tasks = get_yi_async_session_tasks


__all__ = [
    "get_yi_async_session",
    "get_yi_async_session_master",
    "get_yi_async_session_tasks",
    "yi_async_session",
    "yi_async_session_master",
    "yi_async_session_tasks",
    "yi_get_db",
    "yi_get_db_master",
    "yi_get_db_tasks",
]
