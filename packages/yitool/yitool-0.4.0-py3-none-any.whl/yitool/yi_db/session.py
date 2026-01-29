from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from .engine import engine_master, engine_tasks

# Create async session makers for different datasources

# Master datasource session maker
yi_async_session_master = sessionmaker(
    engine_master,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Tasks datasource session maker
yi_async_session_tasks = sessionmaker(
    engine_tasks,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Default session maker is master
yi_async_session = yi_async_session_master


async def yi_get_db() -> AsyncSession:
    """Dependency to get DB session (default: master)."""
    async with yi_async_session_master() as session:
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
    async with yi_async_session_master() as session:
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
    async with yi_async_session_tasks() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


__all__ = [
    "yi_async_session",
    "yi_async_session_master",
    "yi_async_session_tasks",
    "yi_get_db",
    "yi_get_db_master",
    "yi_get_db_tasks",
]
