# XianyuFlow v10 - Phase 2: 服务拆分实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将单体 `mimic_ops.py` 拆分为 6 个独立的微服务，实现服务间 gRPC 通信和事件驱动架构

**Architecture:** 每个服务为独立的 Python FastAPI 应用，通过 gRPC 进行同步调用，通过 Kafka 进行异步事件通知，共享基础库 `xianyuflow-common`

**Tech Stack:** Python 3.12, FastAPI, gRPC, Kafka, SQLAlchemy 2.0, Pydantic v2, dependency-injector

---

## 文件结构

```
services/
├── common/                      # 共享基础库
│   ├── xianyuflow_common/
│   │   ├── __init__.py
│   │   ├── config.py           # 统一配置管理
│   │   ├── database.py         # 数据库连接池
│   │   ├── kafka.py            # Kafka 客户端封装
│   │   ├── grpc/               # gRPC 生成的代码
│   │   ├── models/             # Pydantic 共享模型
│   │   └── telemetry.py        # 可观测性工具
│   ├── pyproject.toml
│   └── Dockerfile
│
├── gateway-service/            # 闲管家 API 网关
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── client.py           # 闲管家 HTTP 客户端
│   │   ├── signing.py          # 签名算法
│   │   └── routes.py
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── quote-service/              # 物流报价服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── engine.py           # 报价计算引擎
│   │   ├── cost_table.py       # 成本表管理
│   │   └── providers.py        # 外部运力 API
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── ai-service/                 # AI 服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── client.py           # LLM 客户端
│   │   ├── context.py          # 上下文管理
│   │   ├── prompts/            # Prompt 模板
│   │   └── state_machine.py    # 对话状态机
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── message-service/            # 消息服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── websocket.py        # WebSocket 连接池
│   │   ├── handler.py          # 消息处理器
│   │   └── reply.py            # 回复生成
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── order-service/              # 订单服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py           # SQLAlchemy 模型
│   │   ├── state_machine.py    # 订单状态机
│   │   └── virtual_goods.py    # 虚拟商品核销
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
└── scheduler-service/          # 定时任务服务
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   └── jobs/
    │       ├── price_poller.py
    │       └── listing_polisher.py
    ├── tests/
    ├── pyproject.toml
    └── Dockerfile
```

---

## Task 1: 创建共享基础库 (xianyuflow-common)

**Files:**
- Create: `services/common/pyproject.toml`
- Create: `services/common/xianyuflow_common/__init__.py`
- Create: `services/common/xianyuflow_common/config.py`
- Create: `services/common/xianyuflow_common/database.py`

**Step 1: 创建 pyproject.toml**

```toml
# services/common/pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "xianyuflow-common"
version = "0.1.0"
description = "XianyuFlow shared components"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "dependency-injector>=4.41",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "redis>=5.0",
    "kafka-python-ng>=2.2",
    "grpcio>=1.59",
    "opentelemetry-api>=1.21",
    "opentelemetry-sdk>=1.21",
    "opentelemetry-instrumentation-fastapi>=0.42",
    "structlog>=23.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.1",
    "mypy>=1.7",
    "ruff>=0.1",
]
```

**Step 2: 创建配置管理模块**

```python
# services/common/xianyuflow_common/config.py
"""统一配置管理，替代全局 get_config()"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = "localhost"
    port: int = 5432
    name: str = "xianyuflow"
    user: str = "xianyu"
    password: str = Field(default="xianyu2024", exclude=True)
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    password: str = Field(default="xianyu2024", exclude=True)
    db: int = 0


class KafkaConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KAFKA_")

    bootstrap_servers: str = "localhost:9092"
    client_id: str = "xianyuflow"


class AIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AI_")

    deepseek_api_key: str = Field(default="", exclude=True)
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    default_model: str = "deepseek-chat"
    max_context_messages: int = 20


class XianyuConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="XIANYU_")

    app_key: str = ""
    app_secret: str = Field(default="", exclude=True)
    base_url: str = "https://api.xianguanjia.com"


class ServiceConfig(BaseSettings):
    """服务通用配置"""
    model_config = SettingsConfigDict(env_prefix="SERVICE_")

    name: str = "xianyuflow-service"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    environment: str = "development"

    # 子配置
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    xianyu: XianyuConfig = Field(default_factory=XianyuConfig)
```

**Step 3: 创建数据库模块**

```python
# services/common/xianyuflow_common/database.py
"""数据库连接池管理"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import DatabaseConfig

Base = declarative_base()


class Database:
    """数据库连接池管理器"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine = None
        self._session_factory = None

    async def connect(self):
        """初始化连接池"""
        self._engine = create_async_engine(
            self.config.dsn,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_pre_ping=True,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self):
        """关闭连接池"""
        if self._engine:
            await self._engine.dispose()

    async def create_tables(self):
        """创建所有表"""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
```

**Step 4: 创建 Kafka 模块**

```python
# services/common/xianyuflow_common/kafka.py
"""Kafka 客户端封装"""

import json
from typing import Any, Callable

from kafka import KafkaConsumer, KafkaProducer

from .config import KafkaConfig


class KafkaClient:
    """Kafka 客户端"""

    def __init__(self, config: KafkaConfig):
        self.config = config
        self._producer = None
        self._consumers = []

    def connect(self):
        """初始化生产者"""
        self._producer = KafkaProducer(
            bootstrap_servers=self.config.bootstrap_servers,
            client_id=self.config.client_id,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )

    def disconnect(self):
        """关闭连接"""
        if self._producer:
            self._producer.close()
        for consumer in self._consumers:
            consumer.close()

    def publish(self, topic: str, message: dict[str, Any], key: str | None = None):
        """发布消息"""
        future = self._producer.send(topic, value=message, key=key)
        return future.get(timeout=10)

    def consume(
        self,
        topics: list[str],
        group_id: str,
        handler: Callable[[dict], None],
    ):
        """消费消息（应在独立线程/进程中运行）"""
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=self.config.bootstrap_servers,
            group_id=group_id,
            client_id=f"{self.config.client_id}-{group_id}",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        self._consumers.append(consumer)

        for message in consumer:
            try:
                handler(message.value)
            except Exception as e:
                # 记录错误但不阻塞消费
                print(f"Error handling message: {e}")


# 预定义的主题
TOPICS = {
    "orders.paid": "orders.paid",
    "messages.received": "messages.received",
    "quotes.calculated": "quotes.calculated",
    "listings.published": "listings.published",
    "cookies.expired": "cookies.expired",
}
```

**Step 5: 测试安装**

```bash
cd services/common
pip install -e ".[dev]"
python -c "from xianyuflow_common.config import ServiceConfig; print('OK')"
```

Expected: `OK`

**Step 6: Commit**

```bash
git add services/common/
git commit -m "feat(services): add xianyuflow-common shared library with config, db, kafka"
```

---

## Task 2: 创建 gateway-service

**Files:**
- Create: `services/gateway-service/pyproject.toml`
- Create: `services/gateway-service/app/__init__.py`
- Create: `services/gateway-service/app/main.py`
- Create: `services/gateway-service/app/client.py`
- Create: `services/gateway-service/Dockerfile`

**Step 1: 创建项目配置**

```toml
# services/gateway-service/pyproject.toml
[project]
name = "gateway-service"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "xianyuflow-common",
    "fastapi>=0.104",
    "uvicorn[standard]>=0.24",
    "httpx>=0.25",
]

[tool.hatch.metadata]
allow-direct-references = true
```

**Step 2: 创建主应用**

```python
# services/gateway-service/app/main.py
"""Gateway Service - 闲管家 API 网关"""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from xianyuflow_common.config import ServiceConfig, XianyuConfig
from xianyuflow_common.database import Database

from .client import XianGuanJiaClient

config = ServiceConfig(name="gateway-service")
db = Database(config.db)
xgj_client = XianGuanJiaClient(config.xianyu)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await db.connect()
    yield
    await db.disconnect()


app = FastAPI(
    title="Gateway Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": config.name}


@app.get("/api/v1/users/authorized")
async def list_authorized_users():
    """获取已授权用户列表"""
    try:
        result = await xgj_client.list_authorized_users()
        return result
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Xianyu API error: {e}")


@app.get("/api/v1/products")
async def list_products(page: int = 1, page_size: int = 20):
    """获取商品列表"""
    try:
        result = await xgj_client.list_products(page, page_size)
        return result
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Xianyu API error: {e}")


@app.post("/api/v1/products")
async def create_product(product: dict):
    """创建商品"""
    try:
        result = await xgj_client.create_product(product)
        return result
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Xianyu API error: {e}")


@app.get("/api/v1/orders")
async def list_orders(status: str | None = None, page: int = 1):
    """获取订单列表"""
    try:
        result = await xgj_client.list_orders(status, page)
        return result
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Xianyu API error: {e}")


@app.post("/api/v1/orders/{order_id}/price")
async def modify_order_price(order_id: str, price: dict):
    """修改订单价格"""
    try:
        result = await xgj_client.modify_order_price(order_id, price)
        return result
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Xianyu API error: {e}")


@app.post("/api/v1/orders/{order_id}/ship")
async def ship_order(order_id: str, shipping: dict):
    """订单发货"""
    try:
        result = await xgj_client.ship_order(order_id, shipping)
        return result
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Xianyu API error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)
```

**Step 3: 创建闲管家客户端**

```python
# services/gateway-service/app/client.py
"""闲管家 API 客户端"""

import hashlib
import json
import time
from typing import Any

import httpx

from xianyuflow_common.config import XianyuConfig


class XianGuanJiaClient:
    """闲管家开放平台客户端"""

    def __init__(self, config: XianyuConfig):
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=30.0,
        )

    def _sign(self, body: str, timestamp: str) -> str:
        """生成请求签名"""
        body_md5 = hashlib.md5(body.encode()).hexdigest()
        sign_str = f"{self.config.app_key},{body_md5},{timestamp},{self.config.app_secret}"
        return hashlib.md5(sign_str.encode()).hexdigest()

    async def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        """发送请求"""
        body = json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":"))
        timestamp = str(int(time.time()))
        sign = self._sign(body, timestamp)

        params = {
            "appid": self.config.app_key,
            "timestamp": timestamp,
            "sign": sign,
        }

        response = await self._client.request(
            method=method,
            url=path,
            params=params,
            content=body.encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    async def list_authorized_users(self) -> dict:
        """获取已授权用户"""
        return await self._request("POST", "/api/open/user/authorize/list", {})

    async def list_products(self, page: int = 1, page_size: int = 20) -> dict:
        """获取商品列表"""
        return await self._request("POST", "/api/open/product/list", {
            "page": page,
            "pageSize": page_size,
        })

    async def create_product(self, product: dict) -> dict:
        """创建商品"""
        return await self._request("POST", "/api/open/product/create", product)

    async def list_orders(self, status: str | None = None, page: int = 1) -> dict:
        """获取订单列表"""
        payload = {"page": page, "pageSize": 20}
        if status:
            payload["status"] = status
        return await self._request("POST", "/api/open/order/list", payload)

    async def modify_order_price(self, order_id: str, price: dict) -> dict:
        """修改订单价格"""
        return await self._request("POST", "/api/open/order/modify/price", {
            "orderId": order_id,
            **price,
        })

    async def ship_order(self, order_id: str, shipping: dict) -> dict:
        """订单发货"""
        return await self._request("POST", "/api/open/order/ship", {
            "orderId": order_id,
            **shipping,
        })
```

**Step 4: 创建 Dockerfile**

```dockerfile
# services/gateway-service/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY pyproject.toml ./
COPY --from=xianyuflow-common:latest /wheels /wheels
RUN pip install --no-index --find-links=/wheels xianyuflow-common
RUN pip install -e .

# 复制代码
COPY app/ ./app/

EXPOSE 8000

CMD ["python", "-m", "app.main"]
```

**Step 5: Commit**

```bash
git add services/gateway-service/
git commit -m "feat(services): add gateway-service for Xianyu API integration"
```

---

## Task 3-6: 创建其他服务

由于篇幅限制，以下是其他服务的概要：

### Task 3: quote-service
- 迁移 `src/modules/quote/` 的逻辑
- 提供 `/api/v1/quotes/calculate` 端点
- 消费 `messages.received` 主题，发布 `quotes.calculated`

### Task 4: ai-service
- 实现对话状态机
- 上下文管理 (L0-L3)
- Prompt 模板管理
- 提供 `/api/v1/chat/completions` 端点

### Task 5: message-service
- WebSocket 连接池
- 消费 `quotes.calculated`，回复消息
- 发布 `messages.received`

### Task 6: order-service
- SQLAlchemy 模型
- 订单状态机
- 虚拟商品核销
- 消费 `orders.paid`

---

## Task 7: 创建 Docker Compose 开发环境

**Files:**
- Create: `services/docker-compose.yml`

```yaml
version: "3.8"

services:
  gateway-service:
    build: ./gateway-service
    ports:
      - "8001:8000"
    environment:
      - SERVICE_NAME=gateway-service
      - SERVICE_PORT=8000
      - DB_HOST=postgres
      - REDIS_HOST=redis
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - XIANYU_APP_KEY=${XIANYU_APP_KEY}
      - XIANYU_APP_SECRET=${XIANYU_APP_SECRET}
    depends_on:
      - postgres
      - redis
      - kafka

  quote-service:
    build: ./quote-service
    ports:
      - "8003:8000"
    environment:
      - SERVICE_NAME=quote-service
      - SERVICE_PORT=8000
      - DB_HOST=postgres
      - REDIS_HOST=redis
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - postgres
      - redis
      - kafka

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=xianyu
      - POSTGRES_PASSWORD=xianyu2024
      - POSTGRES_DB=xianyuflow
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  kafka:
    image: confluentinc/cp-kafka:7.5
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

volumes:
  postgres_data:
```

---

## 验证清单

Phase 2 完成后验证：

- [ ] 所有服务健康检查通过（`curl http://localhost:8001/health`）
- [ ] gRPC 服务间调用正常
- [ ] Kafka 事件流转正常
- [ ] 数据库表结构正确
- [ ] 配置文件加载正确（无全局 get_config）
- [ ] 服务启动时间 < 10s

---

## 参考

- 设计文档: `docs/superpowers/specs/2026-03-27-xianyuflow-v10-architecture-design.md`
- Phase 1 计划: `docs/superpowers/plans/2026-03-27-phase1-infrastructure.md`
