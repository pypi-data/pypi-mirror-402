"""Celery tasks module"""

from .yi_celery import YiCelery

# 导出全局单例实例，使用 instance 属性简化导出
yi_celery = YiCelery.instance()

__all__ = ["YiCelery", "yi_celery"]
