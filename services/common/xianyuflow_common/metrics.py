"""
Performance monitoring and metrics collection
Phase 4: Performance optimization
"""

import functools
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

import structlog
from prometheus_client import Counter, Gauge, Histogram, Info

logger = structlog.get_logger()

# Service info
SERVICE_INFO = Info("xianyu_service", "Service information")

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "xianyu_http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION = Histogram(
    "xianyu_http_request_duration_seconds",
    "HTTP request duration",
    ["service", "method", "endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

HTTP_REQUEST_SIZE = Histogram(
    "xianyu_http_request_size_bytes",
    "HTTP request size",
    ["service", "method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

# Database metrics
DB_QUERIES_TOTAL = Counter(
    "xianyu_db_queries_total",
    "Total database queries",
    ["service", "operation", "table"]
)

DB_QUERY_DURATION = Histogram(
    "xianyu_db_query_duration_seconds",
    "Database query duration",
    ["service", "operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

DB_CONNECTIONS = Gauge(
    "xianyu_db_connections",
    "Database connections",
    ["service", "state"]  # state: active, idle, waiting
)

# Cache metrics
CACHE_HITS_TOTAL = Counter(
    "xianyu_cache_hits_total",
    "Total cache hits",
    ["service", "cache_level", "cache_name"]
)

CACHE_MISSES_TOTAL = Counter(
    "xianyu_cache_misses_total",
    "Total cache misses",
    ["service", "cache_level", "cache_name"]
)

CACHE_SIZE = Gauge(
    "xianyu_cache_size",
    "Cache size",
    ["service", "cache_level", "cache_name"]
)

# Business metrics
MESSAGES_PROCESSED = Counter(
    "xianyu_messages_processed_total",
    "Total messages processed",
    ["service", "message_type", "status"]
)

QUOTES_CALCULATED = Counter(
    "xianyu_quotes_calculated_total",
    "Total quotes calculated",
    ["service", "courier"]
)

ORDERS_PROCESSED = Counter(
    "xianyu_orders_processed_total",
    "Total orders processed",
    ["service", "status"]
)

# WebSocket metrics
WS_CONNECTIONS = Gauge(
    "xianyu_ws_connections",
    "WebSocket connections",
    ["service", "account_id"]
)

WS_MESSAGES = Counter(
    "xianyu_ws_messages_total",
    "WebSocket messages",
    ["service", "direction"]  # direction: sent, received
)

WS_LATENCY = Histogram(
    "xianyu_ws_latency_seconds",
    "WebSocket message latency",
    ["service"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
)

# AI metrics
AI_REQUESTS = Counter(
    "xianyu_ai_requests_total",
    "Total AI requests",
    ["service", "model", "status"]
)

AI_TOKENS = Counter(
    "xianyu_ai_tokens_total",
    "Total AI tokens",
    ["service", "model", "token_type"]  # token_type: prompt, completion
)

AI_LATENCY = Histogram(
    "xianyu_ai_latency_seconds",
    "AI request latency",
    ["service", "model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

CONTEXT_LEVELS = Gauge(
    "xianyu_context_levels",
    "Context level cache entries",
    ["service", "level"]  # level: l1, l2, l3
)


class MetricsMiddleware:
    """FastAPI metrics middleware"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        SERVICE_INFO.info({"service": service_name})

    async def __call__(self, request, call_next):
        start_time = time.time()

        # Record request size
        request_size = int(request.headers.get("content-length", 0))

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Get route info
        route = request.url.path
        method = request.method
        status_code = response.status_code

        # Record metrics
        HTTP_REQUESTS_TOTAL.labels(
            service=self.service_name,
            method=method,
            endpoint=route,
            status_code=str(status_code)
        ).inc()

        HTTP_REQUEST_DURATION.labels(
            service=self.service_name,
            method=method,
            endpoint=route
        ).observe(duration)

        HTTP_REQUEST_SIZE.labels(
            service=self.service_name,
            method=method,
            endpoint=route
        ).observe(request_size)

        return response


def timed(metric: Histogram, labels: dict | None = None):
    """Decorator to time function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def counted(metric: Counter, labels: dict | None = None):
    """Decorator to count function calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if labels:
                metric.labels(**labels).inc()
            else:
                metric.inc()
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if labels:
                metric.labels(**labels).inc()
            else:
                metric.inc()
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


@contextmanager
def db_timer(service: str, operation: str, table: str):
    """Context manager for database query timing"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        DB_QUERY_DURATION.labels(
            service=service,
            operation=operation,
            table=table
        ).observe(duration)
        DB_QUERIES_TOTAL.labels(
            service=service,
            operation=operation,
            table=table
        ).inc()


@contextmanager
def cache_timer(service: str, cache_level: str, cache_name: str, hit: bool):
    """Context manager for cache metrics"""
    if hit:
        CACHE_HITS_TOTAL.labels(
            service=service,
            cache_level=cache_level,
            cache_name=cache_name
        ).inc()
    else:
        CACHE_MISSES_TOTAL.labels(
            service=service,
            cache_level=cache_level,
            cache_name=cache_name
        ).inc()
    yield


class PerformanceProfiler:
    """性能分析器"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._profiles: dict[str, Any] = {}

    def start(self, name: str) -> None:
        """开始性能分析"""
        self._profiles[name] = {
            "start_time": time.time(),
            "start_memory": None,  # Could add memory profiling
        }

    def end(self, name: str) -> dict:
        """结束性能分析"""
        if name not in self._profiles:
            return {}

        profile = self._profiles[name]
        duration = time.time() - profile["start_time"]

        result = {
            "name": name,
            "duration_seconds": duration,
            "service": self.service_name,
        }

        # Log slow operations
        if duration > 1.0:  # 1 second threshold
            logger.warning(
                "Slow operation detected",
                operation=name,
                duration_seconds=duration,
                service=self.service_name
            )

        del self._profiles[name]
        return result


# Import asyncio for decorator checks
import asyncio
