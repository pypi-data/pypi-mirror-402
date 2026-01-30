from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# Database naming convention for PostgreSQL (default)
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

# Database naming convention for MySQL
MYSQL_INDEXES_NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Create metadata instances with naming conventions

# Default metadata (for master datasource, usually MySQL)
metadata_master = MetaData(naming_convention=MYSQL_INDEXES_NAMING_CONVENTION)

# Metadata for tasks datasource (usually PostgreSQL)
metadata_tasks = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

# Default metadata alias
metadata = metadata_master

# Create base classes for different datasources

# Base class for master datasource models
YiBaseEntity = declarative_base(metadata=metadata_master)

# Base class for tasks datasource models
YiBaseEntityTasks = declarative_base(metadata=metadata_tasks)

__all__ = [
    "YiBaseEntity",
    "YiBaseEntityTasks",
    "metadata",
    "metadata_master",
    "metadata_tasks"
]
