import logging
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from yitool.yi_config import config


class YiRequestIdMiddleware(BaseHTTPMiddleware):
    """请求ID中间件，为每个请求生成唯一的请求ID"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 从请求头获取请求ID，如果没有则生成一个
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # 将请求ID添加到请求状态中
        request.state.request_id = request_id

        # 调用下一个中间件或路由处理函数
        response = await call_next(request)

        # 将请求ID添加到响应头中
        response.headers["X-Request-ID"] = request_id

        return response


class YiRequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件，记录请求的详细信息"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 获取配置
        settings = config.settings
        
        # 如果请求日志功能未启用，直接调用下一个中间件
        if not settings or not settings.middleware.request_log.enabled:
            return await call_next(request)

        # 记录请求开始时间
        start_time = datetime.utcnow()

        # 记录请求基本信息
        method = request.method
        url = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, "request_id", "unknown")

        # 记录请求头
        headers = dict(request.headers) if settings.middleware.request_log.include_headers else {}

        # 调用下一个中间件或路由处理函数
        response = await call_next(request)

        # 计算请求处理时间
        process_time = datetime.utcnow() - start_time
        process_time_ms = int(process_time.total_seconds() * 1000)

        # 构建日志信息
        log_info = {
            "request_id": request_id,
            "method": method,
            "url": url,
            "client_ip": client_ip,
            "status_code": response.status_code,
            "process_time_ms": process_time_ms,
        }

        # 添加请求头到日志（如果配置了）
        if headers:
            log_info["headers"] = headers

        # 获取日志记录器
        logger = logging.getLogger("fastapi.request")
        log_level = getattr(logging, settings.middleware.request_log.log_level.upper(), logging.INFO)

        # 记录日志
        logger.log(log_level, "Request processed", extra=log_info)

        return response


class YiResponseTimeMiddleware(BaseHTTPMiddleware):
    """响应时间监控中间件，记录请求的响应时间并进行统计"""

    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        # 响应时间统计字典
        self.response_times = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 获取配置
        settings = config.settings
        
        # 如果响应时间监控功能未启用，直接调用下一个中间件
        if not settings or not settings.middleware.response_time.enabled:
            return await call_next(request)

        # 记录请求开始时间
        start_time = datetime.utcnow()

        # 调用下一个中间件或路由处理函数
        response = await call_next(request)

        # 计算请求处理时间
        process_time = datetime.utcnow() - start_time
        process_time_seconds = process_time.total_seconds()

        # 将响应时间添加到统计字典
        path = request.url.path
        self.response_times[path].append(process_time_seconds)

        # 检查是否为慢请求
        if process_time_seconds > settings.middleware.response_time.slow_request_threshold:
            # 记录慢请求日志
            logger = logging.getLogger("fastapi.slow_request")
            logger.warning(
                "Slow request detected",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "method": request.method,
                    "url": path,
                    "process_time_seconds": round(process_time_seconds, 3),
                    "threshold_seconds": settings.middleware.response_time.slow_request_threshold,
                }
            )

        # 将处理时间添加到响应头中
        response.headers["X-Process-Time"] = str(int(process_time_seconds * 1000))

        return response


class YiRateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件，限制单位时间内的请求数量"""

    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        # 存储请求计数 {key: [timestamp1, timestamp2, ...]}
        self.requests = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 获取配置
        settings = config.settings
        
        # 如果限流功能未启用，直接调用下一个中间件
        if not settings or not settings.middleware.rate_limit.enabled:
            return await call_next(request)

        # 生成限流键
        key = self._get_rate_limit_key(request)
        now = datetime.utcnow().timestamp()
        window_seconds = settings.middleware.rate_limit.window_seconds
        limit = settings.middleware.rate_limit.limit

        # 清理过期的请求记录
        self.requests[key] = [t for t in self.requests[key] if now - t < window_seconds]

        # 检查是否超过限流阈值
        if len(self.requests[key]) >= limit:
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(window_seconds)}
            )

        # 记录当前请求时间
        self.requests[key].append(now)

        # 调用下一个中间件或路由处理函数
        response = await call_next(request)

        # 添加限流相关的响应头
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(limit - len(self.requests[key]))
        response.headers["X-RateLimit-Reset"] = str(int(now + window_seconds))

        return response

    def _get_rate_limit_key(self, request: Request) -> str:
        """生成限流键"""
        # 获取配置
        settings = config.settings
        if not settings:
            return "default"
            
        key_func = settings.middleware.rate_limit.key_func

        if key_func == "ip":
            return request.client.host if request.client else "unknown"
        elif key_func == "user":
            # 如果有当前用户，使用用户ID作为键
            if hasattr(request.state, "user_id"):
                return str(request.state.user_id)
            return "anonymous"
        elif key_func == "api_key":
            # 从请求头或查询参数获取API密钥
            if settings.api_key:
                api_key = request.headers.get(settings.api_key.header_name)
                if not api_key:
                    api_key = request.query_params.get(settings.api_key.query_param_name)
                return api_key or "anonymous"
            return "anonymous"
        else:
            return request.client.host if request.client else "unknown"


class CircuitBreakerState:
    """熔断状态"""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class YiCircuitBreakerMiddleware(BaseHTTPMiddleware):
    """熔断中间件，防止服务雪崩"""

    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        # 熔断状态存储 {endpoint: state}
        self.states = defaultdict(dict)
        # 初始化默认状态
        for endpoint in ["default"]:
            self.states[endpoint] = {
                "state": CircuitBreakerState.CLOSED,
                "failure_count": 0,
                "last_failure_time": None,
                "success_count": 0
            }

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 获取配置
        settings = config.settings
        
        # 如果熔断功能未启用，直接调用下一个中间件
        if not settings or not settings.middleware.circuit_breaker.enabled:
            return await call_next(request)

        endpoint = request.url.path
        if endpoint not in self.states:
            self.states[endpoint] = {
                "state": CircuitBreakerState.CLOSED,
                "failure_count": 0,
                "last_failure_time": None,
                "success_count": 0
            }

        state_info = self.states[endpoint]
        now = datetime.utcnow()

        # 检查熔断状态
        if state_info["state"] == CircuitBreakerState.OPEN:
            # 检查是否可以尝试恢复
            recovery_timeout = settings.middleware.circuit_breaker.recovery_timeout
            if state_info["last_failure_time"] and \
               (now - state_info["last_failure_time"]).total_seconds() > recovery_timeout:
                # 切换到HALF_OPEN状态，允许尝试恢复
                state_info["state"] = CircuitBreakerState.HALF_OPEN
                state_info["success_count"] = 0
            else:
                # 熔断状态下，直接返回503
                raise HTTPException(
                    status_code=HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service unavailable due to circuit breaker",
                    headers={"Retry-After": str(recovery_timeout)}
                )

        try:
            # 调用下一个中间件或路由处理函数
            response = await call_next(request)

            # 处理成功情况
            if response.status_code >= 500:
                # 服务器错误，视为失败
                await self._handle_failure(endpoint, state_info)
            else:
                # 请求成功
                await self._handle_success(endpoint, state_info)

            return response
        except Exception:
            # 处理异常情况
            await self._handle_failure(endpoint, state_info)
            raise

    async def _handle_success(self, endpoint: str, state_info: dict[str, Any]) -> None:
        """处理成功请求"""
        if state_info["state"] == CircuitBreakerState.HALF_OPEN:
            # HALF_OPEN状态下，成功计数+1
            state_info["success_count"] += 1
            # 如果成功次数达到阈值，切换到CLOSED状态
            if state_info["success_count"] >= 3:  # 连续3次成功，恢复正常
                state_info["state"] = CircuitBreakerState.CLOSED
                state_info["failure_count"] = 0
                state_info["last_failure_time"] = None
        elif state_info["state"] == CircuitBreakerState.CLOSED:
            # CLOSED状态下，失败计数重置
            state_info["failure_count"] = 0

    async def _handle_failure(self, endpoint: str, state_info: dict[str, Any]) -> None:
        """处理失败请求"""
        settings = config.settings
        state_info["failure_count"] += 1
        state_info["last_failure_time"] = datetime.utcnow()

        # 检查是否达到熔断阈值
        if settings and state_info["failure_count"] >= settings.middleware.circuit_breaker.failure_threshold:
            state_info["state"] = CircuitBreakerState.OPEN
        elif state_info["state"] == CircuitBreakerState.HALF_OPEN:
            # HALF_OPEN状态下，任何失败都会立即切换到OPEN状态
            state_info["state"] = CircuitBreakerState.OPEN


class YiCORSMiddleware(BaseHTTPMiddleware):
    """自定义CORS中间件，基于settings配置"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 处理OPTIONS请求
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)

        # 获取配置
        settings = config.settings
        
        # 添加CORS头
        origin = request.headers.get("Origin")
        if settings and settings.cors and origin:
            # 检查origin是否在允许列表中
            if "*" in settings.cors.origins or origin in settings.cors.origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = ", ".join(settings.cors.methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(settings.cors.headers)
                response.headers["Access-Control-Max-Age"] = str(settings.cors.max_age)

        return response
