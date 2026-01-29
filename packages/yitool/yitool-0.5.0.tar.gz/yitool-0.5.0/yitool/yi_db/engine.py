from sqlalchemy.ext.asyncio import create_async_engine

from yitool.yi_config import config as settings

# Map database URL prefixes to async driver suffixes
ASYNC_DRIVER_MAP = {
    "mysql": "asyncmy",
    "postgresql": "asyncpg",
    "sqlite": "aiosqlite",
}

# Lazy-initialized database engines
_engine_master = None
_engine_slave = None
_engine_tasks = None
_engine = None


def get_async_db_url(db_url: str) -> str:
    """Get async database URL by adding appropriate async driver suffix."""
    # Extract base database type (mysql, postgresql, sqlite)
    base_type = None
    for db_type in ASYNC_DRIVER_MAP.keys():
        if db_type in db_url:
            base_type = db_type
            break

    if base_type:
        # Get appropriate async driver suffix
        async_suffix = ASYNC_DRIVER_MAP[base_type]

        # Check if URL already has a driver
        if "+" in db_url.split("://")[0]:
            # URL already has a driver, return as is
            return db_url
        else:
            # Rebuild URL with async driver
            protocol = f"{base_type}+{async_suffix}"
            connection_string = db_url.split("://", 1)[1]
            return f"{protocol}://{connection_string}"

    return db_url


def create_engine_for_config(db_config) -> str:
    """Create async engine for given database configuration."""
    # Check if we're in a test environment or alembic environment
    import sys
    is_test = "pytest" in sys.modules
    is_alembic = "alembic" in sys.modules

    if is_test or is_alembic:
        # In test or alembic environment, use in-memory SQLite database
        db_url = "sqlite+aiosqlite:///:memory:"
        # SQLite doesn't support pool-related arguments
    return create_async_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=True if settings.app.environment == "development" else False,
    )

    # In normal environment, use the configured database URL
    db_url = get_async_db_url(db_config.url)

    # Check if the database is SQLite
    if "sqlite+" in db_url:
        # SQLite doesn't support pool-related arguments
        return create_async_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=True if settings.app.environment == "development" else False,
        )

    # For other databases (MySQL, PostgreSQL), use the pool-related arguments
    return create_async_engine(
        db_url,
        pool_size=db_config.pool_size,
        max_overflow=db_config.max_overflow,
        pool_timeout=db_config.pool_timeout,
        pool_recycle=db_config.pool_recycle,
        echo=True if settings.app.environment == "development" else False,
    )


def get_engine_master():
    """Get or create master database engine (lazy initialization)."""
    global _engine_master
    if _engine_master is None:
        _engine_master = create_engine_for_config(settings.datasource.master)
    return _engine_master


def get_engine_slave():
    """Get or create slave database engine (lazy initialization)."""
    global _engine_slave
    if _engine_slave is None:
        _engine_slave = create_engine_for_config(settings.datasource.slave) if settings.datasource.slave else None
    return _engine_slave


def get_engine_tasks():
    """Get or create tasks database engine (lazy initialization)."""
    global _engine_tasks
    if _engine_tasks is None:
        _engine_tasks = create_engine_for_config(settings.datasource.tasks) if settings.datasource.tasks else get_engine_master()
    return _engine_tasks


def get_engine():
    """Get default database engine (master)."""
    global _engine
    if _engine is None:
        _engine = get_engine_master()
    return _engine


__all__ = ["get_engine", "get_engine_master", "get_engine_slave", "get_engine_tasks", "create_sqlmodel_engine"]


def create_sqlmodel_engine(
    connection_string: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    **kwargs
):
    """
    Create SQLModel-compatible sync engine.

    Args:
        connection_string: Database connection string
        echo: Whether to echo SQL statements
        pool_size: Connection pool size
        max_overflow: Maximum overflow connection count
        **kwargs: Additional engine parameters

    Returns:
        SQLAlchemy Engine instance

    Example:
        from yitool.yi_db.engine import create_sqlmodel_engine

        engine = create_sqlmodel_engine("sqlite:///test.db")
        with Session(engine) as session:
            pass

    Note:
        This function provides a consistent interface with SqlModelUtils.create_engine()
        for convenient use within the yitool.yi_db module.
    """
    try:
        from sqlmodel import create_engine as sqlmodel_create_engine
    except ImportError:
        raise ImportError(
            "sqlmodel package not installed. Install with: uv pip install sqlmodel"
        ) from None
    
    return sqlmodel_create_engine(
        connection_string,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        **kwargs
    )


async def create_async_sqlmodel_engine(connection_string: str, **kwargs):
    """
    Create SQLModel-compatible async engine.

    Args:
        connection_string: Database connection string
        **kwargs: Additional engine parameters

    Returns:
        SQLAlchemy AsyncEngine instance

    Example:
        from yitool.yi_db.engine import create_async_sqlmodel_engine

        engine = await create_async_sqlmodel_engine("sqlite+aiosqlite:///test.db")
        async with AsyncSession(engine) as session:
            pass

    Note:
        SQLModel's async engine is actually based on SQLAlchemy.
        This function provides a consistent interface with SqlModelUtils.create_async_engine().
    """
    try:
        from sqlalchemy.ext.asyncio import create_async_engine as sqlalchemy_async_create
    except ImportError:
        raise ImportError(
            "sqlalchemy-ext-asyncio package not installed."
        ) from None
    
    # SQLModel's async engine is actually based on SQLAlchemy
    return sqlalchemy_async_create(connection_string, **kwargs)
