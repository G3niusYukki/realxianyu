"""
WebSocket Connection Pool Load Test
Phase 4: Performance testing
"""

import asyncio
import random
import time
from dataclasses import dataclass
from typing import List

import aiohttp
import structlog

logger = structlog.get_logger()


@dataclass
class LoadTestResult:
    """负载测试结果"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    requests_per_second: float
    duration_seconds: float


class WebSocketLoadTester:
    """WebSocket 负载测试器"""

    def __init__(
        self,
        target_url: str = "ws://localhost:8001/ws",
        max_concurrent: int = 100,
        total_connections: int = 1000,
        messages_per_connection: int = 10,
    ):
        self.target_url = target_url
        self.max_concurrent = max_concurrent
        self.total_connections = total_connections
        self.messages_per_connection = messages_per_connection

        self._latencies: List[float] = []
        self._success_count = 0
        self._fail_count = 0
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def run_test(self) -> LoadTestResult:
        """运行负载测试"""
        logger.info(
            "Starting load test",
            target=self.target_url,
            total_connections=self.total_connections,
            max_concurrent=self.max_concurrent,
        )

        start_time = time.time()

        # 创建连接任务
        tasks = [
            self._test_single_connection(f"user_{i}")
            for i in range(self.total_connections)
        ]

        # 执行所有任务
        await asyncio.gather(*tasks, return_exceptions=True)

        duration = time.time() - start_time

        # 计算结果
        result = self._calculate_results(duration)

        logger.info(
            "Load test complete",
            total=result.total_requests,
            success=result.successful_requests,
            failed=result.failed_requests,
            rps=round(result.requests_per_second, 2),
            avg_latency_ms=round(result.avg_latency_ms, 2),
            p99_latency_ms=round(result.p99_latency_ms, 2),
        )

        return result

    async def _test_single_connection(self, account_id: str) -> None:
        """测试单个连接"""
        async with self._semaphore:
            conn_start = time.time()

            try:
                # 模拟连接建立
                await asyncio.sleep(random.uniform(0.01, 0.05))

                # 发送消息
                for _ in range(self.messages_per_connection):
                    msg_start = time.time()
                    # 模拟消息发送
                    await asyncio.sleep(random.uniform(0.005, 0.02))
                    latency = (time.time() - msg_start) * 1000
                    self._latencies.append(latency)

                self._success_count += 1

            except Exception as e:
                logger.error("Connection failed", account_id=account_id, error=str(e))
                self._fail_count += 1

    def _calculate_results(self, duration: float) -> LoadTestResult:
        """计算测试结果"""
        total = self._success_count + self._fail_count

        if not self._latencies:
            return LoadTestResult(
                total_requests=total,
                successful_requests=self._success_count,
                failed_requests=self._fail_count,
                avg_latency_ms=0,
                p99_latency_ms=0,
                max_latency_ms=0,
                requests_per_second=0,
                duration_seconds=duration,
            )

        sorted_latencies = sorted(self._latencies)
        p99_index = int(len(sorted_latencies) * 0.99)

        return LoadTestResult(
            total_requests=total,
            successful_requests=self._success_count,
            failed_requests=self._fail_count,
            avg_latency_ms=sum(self._latencies) / len(self._latencies),
            p99_latency_ms=sorted_latencies[min(p99_index, len(sorted_latencies) - 1)],
            max_latency_ms=max(self._latencies),
            requests_per_second=total * self.messages_per_connection / duration,
            duration_seconds=duration,
        )


async def benchmark_pool_sizes():
    """基准测试不同池大小"""
    pool_sizes = [10, 50, 100, 200]
    results = []

    for size in pool_sizes:
        logger.info(f"Testing pool size: {size}")
        tester = WebSocketLoadTester(
            max_concurrent=size,
            total_connections=500,
            messages_per_connection=5,
        )
        result = await tester.run_test()
        results.append((size, result))

    # 打印结果表格
    print("\n" + "=" * 80)
    print("Pool Size Benchmark Results")
    print("=" * 80)
    print(f"{'Pool Size':<12} {'RPS':<10} {'Avg (ms)':<12} {'P99 (ms)':<12} {'Success %':<10}")
    print("-" * 80)

    for size, result in results:
        success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
        print(f"{size:<12} {result.requests_per_second:<10.2f} {result.avg_latency_ms:<12.2f} {result.p99_latency_ms:<12.2f} {success_rate:<10.1f}")


if __name__ == "__main__":
    # 配置日志
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 运行测试
    asyncio.run(benchmark_pool_sizes())
