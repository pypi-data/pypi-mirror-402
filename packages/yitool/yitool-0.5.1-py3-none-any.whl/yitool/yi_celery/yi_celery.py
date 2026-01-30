"""Celery application configuration"""

import yaml
from celery import Celery
from celery.result import AsyncResult

from yitool.log import logger
from yitool.yi_config.celery import CeleryConfig
from yitool.yi_singleton import YiSingleton


class YiCelery(Celery, YiSingleton):
    """自定义 Celery 应用类，提供更灵活的配置和扩展能力

    其他项目可以通过继承这个类来自定义自己的 Celery 应用，
    并根据需要覆盖或扩展其功能。
    """

    @property
    def finalized(self):
        """是否已完成配置"""
        return getattr(self, "_finalized", False)

    @finalized.setter
    def finalized(self, value):
        """设置是否已完成配置"""
        self._finalized = value

    @property
    def on_configure(self):
        """配置完成时的回调"""
        return getattr(self, "_on_configure", lambda: None)

    @on_configure.setter
    def on_configure(self, value):
        """设置配置完成时的回调"""
        self._on_configure = value

    def __init__(self, *args, **kwargs):
        """初始化 Celery 应用

        Args:
            app_name: 应用名称
            broker: 消息代理 URL，默认从配置中获取
            backend: 结果后端 URL，默认从配置中获取
            include: 要包含的任务模块列表
            celery_config: Celery 配置对象或配置字典，可选
            **kwargs: 其他 Celery 配置参数
        """
        # 禁止直接实例化
        if not self.__class__ in self.__class__._instances:
            raise RuntimeError(
                f"Direct instantiation of {self.__class__.__name__} is not allowed. "
                f"Please use {self.__class__.__name__}.instance() to get the singleton instance."
            )
        
        # 只有当实例是新创建的时候才执行初始化
        if not hasattr(self, "_initialized"):
            # 提取 celery_config 参数，其他参数直接传递给父类
            celery_config = kwargs.pop("celery_config", None)
            
            # 初始化父类
            super().__init__(*args, **kwargs)

            # 支持配置字典转换为配置对象
            if isinstance(celery_config, dict):
                celery_config = CeleryConfig(**celery_config)

            # 加载默认配置
            self._load_default_config(celery_config)
            
            # 设置必要的属性
            self._initialized = True
            self._finalized = False  # 使用内部属性
            self._on_configure = lambda: None  # 使用内部属性
            self._pending = []  # 添加 _pending 属性，用于任务注册

    def _on_initialize(self, app_name="yitool-tasks", broker=None, backend=None, include=None, celery_config=None, **kwargs):
        """初始化方法"""
        # 初始化逻辑在 __init__ 中处理
        pass

    def _on_cleanup(self):
        """清理方法"""
        # 清理逻辑
        self._initialized = False

    @classmethod
    def instance(cls, app_name="yitool-tasks", broker=None, backend=None, include=None, celery_config=None, **kwargs):
        """获取单例实例"""
        # 检查是否已经有实例
        if cls in cls._instances:
            return cls._instances[cls]
        
        # 创建新实例
        with cls._get_lock():
            if cls not in cls._instances:
                # 创建实例
                instance = object.__new__(cls)
                cls._instances[cls] = instance
                
                # 初始化必要的属性
                instance._initialized = False
                instance._finalized = False
                instance._pending = []
                instance._on_configure = lambda: None
                
                # 初始化父类
                Celery.__init__(instance, app_name, broker=broker, backend=backend, include=include or ["yitool.yi_celery.email_tasks"], **kwargs)
                
                # 支持配置字典转换为配置对象
                if isinstance(celery_config, dict):
                    celery_config = CeleryConfig(**celery_config)
                
                # 加载默认配置
                instance._load_default_config(celery_config)
                
                # 标记为已初始化
                instance._initialized = True
                
                # 为 yitool 内置的邮件任务添加特定路由
                try:
                    if not hasattr(instance.conf, "task_routes") or instance.conf.task_routes is None:
                        instance.conf.task_routes = {}
                    
                    # 确保邮件任务路由存在
                    if "yitool.yi_celery.email_tasks.*" not in instance.conf.task_routes:
                        instance.conf.task_routes = {
                            # 将 yitool 内置的 email_tasks 路由到 email 队列
                            "yitool.yi_celery.email_tasks.*": {
                                "queue": "email"
                            },
                            # 其他任务使用默认路由
                            **instance.conf.task_routes
                        }
                except Exception as e:
                    logger.warning(f"Error setting up task routes: {e}")
        
        return cls._instances[cls]

    def _load_default_config(self, celery_config=None):
        """加载默认配置

        从配置对象加载 Celery 配置，如果配置不存在，则使用默认值。

        Args:
            celery_config: Celery 配置对象，可选
        """
        # 默认配置值
        default_config = {
            "task_serializer": "json",
            "result_serializer": "json",
            "accept_content": ["json"],
            "timezone": "UTC",
            "enable_utc": True,
            "worker_concurrency": 4,
            "worker_max_tasks_per_child": 100,
            "worker_log_level": "info",
            "beat_schedule": {},
            "task_default_priority": 5,
            "task_queue_max_priority": 10
        }

        # 如果提供了配置对象，使用它
        if celery_config:
            # 从配置对象加载设置
            timezone = getattr(celery_config, "timezone", default_config["timezone"])
            self.conf.update({
                "task_serializer": getattr(celery_config, "task_serializer", default_config["task_serializer"]),
                "result_serializer": getattr(celery_config, "result_serializer", default_config["result_serializer"]),
                "accept_content": getattr(celery_config, "accept_content", default_config["accept_content"]),
                "timezone": timezone,
                "enable_utc": getattr(celery_config, "enable_utc", default_config["enable_utc"]),
                "broker_url": getattr(celery_config, "broker_url", None),
                "result_backend": getattr(celery_config, "result_backend", None),
            })

            # 获取配置值，使用默认值作为后备
            worker_config = getattr(celery_config, "worker", {})
            beat_config = getattr(celery_config, "beat", {})

            # 更新其他配置项
            self.conf.update(
                worker_concurrency=worker_config.get("concurrency", default_config["worker_concurrency"]),
                worker_max_tasks_per_child=worker_config.get("max_tasks_per_child", default_config["worker_max_tasks_per_child"]),
                worker_log_level=worker_config.get("log_level", default_config["worker_log_level"]),
                beat_schedule=beat_config.get("schedule", default_config["beat_schedule"]),
                task_default_priority=worker_config.get("default_priority", default_config["task_default_priority"]),
                task_queue_max_priority=worker_config.get("max_priority", default_config["task_queue_max_priority"])
            )
        else:
            # 使用默认配置
            self.conf.update(default_config)

        # 设置默认队列和路由
        self.conf.task_default_queue = "default"
        self.conf.task_routes = {
            # 将 yitool 内置的 email_tasks 路由到 email 队列
            "yitool.yi_celery.email_tasks.*": {
                "queue": "email"
            },
            # 其他任务使用默认路由
            "*": {
                "queue": "default"
            }
        }
    
    def set_task_priority(self, task_name: str, priority: int) -> None:
        """设置任务优先级

        Args:
            task_name: 任务名称
            priority: 优先级，范围 0-10，10 最高
        """
        # 确保优先级在有效范围内
        priority = max(0, min(10, priority))
        
        # 更新任务路由配置，添加优先级
        if not hasattr(self.conf, "task_routes") or self.conf.task_routes is None:
            self.conf.task_routes = {}
        
        # 检查是否已有该任务的路由配置
        if task_name in self.conf.task_routes:
            # 更新现有配置
            route_config = self.conf.task_routes[task_name]
            if isinstance(route_config, dict):
                route_config["priority"] = priority
        else:
            # 添加新的路由配置
            self.conf.task_routes[task_name] = {
                "priority": priority
            }
        
        logger.info(f"Set priority for task {task_name} to {priority}")
    
    def get_task_priority(self, task_name: str) -> int | None:
        """获取任务优先级

        Args:
            task_name: 任务名称

        Returns:
            任务优先级，如果未设置则返回 None
        """
        if hasattr(self.conf, "task_routes") and self.conf.task_routes:
            if task_name in self.conf.task_routes:
                route_config = self.conf.task_routes[task_name]
                if isinstance(route_config, dict) and "priority" in route_config:
                    return route_config["priority"]
        return None
    
    def send_task_with_priority(self, task_name: str, args=None, kwargs=None, priority: int = 5, **options):
        """发送带优先级的任务

        Args:
            task_name: 任务名称
            args: 任务参数列表
            kwargs: 任务参数字典
            priority: 任务优先级，范围 0-10，10 最高
            **options: 其他任务选项

        Returns:
            任务 ID
        """
        # 确保优先级在有效范围内
        priority = max(0, min(10, priority))
        
        # 设置任务优先级
        options["priority"] = priority
        
        # 发送任务
        return self.send_task(task_name, args=args, kwargs=kwargs, **options)
    
    def health_check(self) -> dict:
        """执行健康检查

        Returns:
            健康检查结果字典
        """
        try:
            # 检查与 broker 的连接
            broker_connected = False
            try:
                # 尝试发送一个测试任务到 broker
                self.send_task(
                    "celery.ping",
                    args=[],
                    kwargs={},
                    queue="default",
                    timeout=5
                )
                broker_connected = True
            except Exception as e:
                logger.error(f"Broker connection check failed: {e}")
            
            # 检查结果后端
            backend_available = False
            try:
                # 尝试获取一个不存在的任务结果，测试后端连接
                AsyncResult("non-existent-task-id", app=self)
                # 这里我们不关心结果，只关心是否能连接到后端
                backend_available = True
            except Exception as e:
                logger.error(f"Backend connection check failed: {e}")
            
            # 检查工作节点状态
            workers_available = False
            try:
                # 尝试获取工作节点列表
                inspect = self.control.inspect()
                if inspect:
                    workers = inspect.ping()
                    if workers:
                        workers_available = True
            except Exception as e:
                logger.error(f"Workers check failed: {e}")
            
            # 构建健康检查结果
            health_status = {
                "status": "healthy" if all([broker_connected, backend_available]) else "unhealthy",
                "broker": {
                    "connected": broker_connected
                },
                "backend": {
                    "available": backend_available
                },
                "workers": {
                    "available": workers_available
                },
                "timestamp": self.now().isoformat()
            }
            
            return health_status
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": self.now().isoformat()
            }
    
    def get_task_stats(self) -> dict:
        """获取任务统计信息

        Returns:
            任务统计信息字典
        """
        try:
            stats = {}
            
            # 获取工作节点信息
            inspect = self.control.inspect()
            if inspect:
                # 获取工作节点状态
                workers = inspect.stats()
                if workers:
                    stats["workers"] = {}
                    for worker_name, worker_stats in workers.items():
                        stats["workers"][worker_name] = {
                            "tasks_processed": worker_stats.get("total", {}).get("tasks", 0),
                            "uptime": worker_stats.get("uptime", 0)
                        }
            
                # 获取队列信息
                queues = inspect.active_queues()
                if queues:
                    stats["queues"] = {}
                    for worker_name, worker_queues in queues.items():
                        stats["queues"][worker_name] = [q["name"] for q in worker_queues]
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get task stats: {e}")
            return {"error": str(e)}
    
    def setup_task_retry_strategy(self, max_retries: int = 3, retry_backoff: int = 1, retry_backoff_max: int = 60, retry_jitter: bool = True):
        """设置任务重试策略

        Args:
            max_retries: 最大重试次数
            retry_backoff: 重试退避时间（秒）
            retry_backoff_max: 最大重试退避时间（秒）
            retry_jitter: 是否启用重试抖动
        """
        # 更新默认任务配置
        self.conf.update({
            "task_annotations": {
                "*": {
                    "max_retries": max_retries,
                    "retry_backoff": retry_backoff,
                    "retry_backoff_max": retry_backoff_max,
                    "retry_jitter": retry_jitter
                }
            }
        })
        
        logger.info(f"Set up task retry strategy: max_retries={max_retries}, retry_backoff={retry_backoff}, retry_backoff_max={retry_backoff_max}, retry_jitter={retry_jitter}")

    @classmethod
    def from_config(cls, source, app_name=None, broker=None, backend=None, include=None, **kwargs):
        """从指定源创建 Celery 应用实例

        Args:
            source: 配置源，可以是文件路径或字典
            app_name: 应用名称
            broker: 消息代理 URL，默认从配置中获取
            backend: 结果后端 URL，默认从配置中获取
            include: 要包含的任务模块列表
            **kwargs: 其他 Celery 配置参数

        Returns:
            YiCelery: 配置好的 Celery 应用实例
        """
        # 从指定源加载配置
        if isinstance(source, str):
            # 从文件加载配置
            with open(source) as f:
                config_dict = yaml.safe_load(f)
            config = CeleryConfig(**config_dict.get("celery", {}))
        elif isinstance(source, dict):
            # 从字典加载配置
            if "celery" in source:
                # 处理嵌套的 celery 配置
                config = CeleryConfig(**source["celery"])
            else:
                # 直接使用字典作为配置
                config = CeleryConfig(**source)
        else:
            # 直接使用配置对象
            config = source

        # 如果没有指定应用名称，从配置中获取
        if not app_name and hasattr(config, "app_name"):
            app_name = config.app_name

        # 传递配置对象到 instance 方法
        return cls.instance(app_name=app_name or "yitool-tasks", broker=broker, backend=backend, include=include, celery_config=config, **kwargs)


