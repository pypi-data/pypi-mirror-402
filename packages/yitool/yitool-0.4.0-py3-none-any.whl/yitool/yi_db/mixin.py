from datetime import datetime

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column


class YiTimestampMixin:
    """时间戳混合类"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class YiSoftDeleteMixin:
    """软删除混合类"""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class YiBaseMixin(YiTimestampMixin, YiSoftDeleteMixin):
    """基础混合类，包含ID、时间戳和软删除"""

    pass
