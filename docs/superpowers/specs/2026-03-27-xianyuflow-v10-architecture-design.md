# XianyuFlow v10.0 架构升级设计文档

> 创建日期：2026-03-27
> 状态：已批准
> 作者：Claude Code

---

## 1. 项目概述

### 1.1 背景

XianyuFlow | 闲流 当前版本（v9.x）采用单体 Python 架构，随着业务增长面临以下挑战：

- `mimic_ops.py` ~3000 行，职责过重
- 全局 `get_config()` 被 24 个文件直接调用，耦合度高
- WebSocket 单连接设计，不支持多账号高并发
- AI 回复无上下文记忆，用户体验受限
- 部署依赖单机和本地文件，难以扩展

### 1.2 目标

构建云原生、高可用、可扩展的闲鱼自动化交易平台的 v10.0 版本。

### 1.3 成功标准

| 指标 | 当前 | 目标 |
|------|------|------|
| 并发账号数 | ~10 | 100+ |
| 消息延迟 | ~3s | <500ms |
| 系统可用性 | 99% | 99.9% |
| 部署时间 | 30min 手动 | 5min 自动 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    网关层 (API Gateway)                      │
│              Kong / Nginx + 限流 + 认证                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  服务层 (Kubernetes Pods)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  Message    │ │   Order     │ │   Quote     │           │
│  │   Service   │ │   Service   │ │   Service   │           │
│  │  (3 replicas)│ │ (2 replicas)│ │ (2 replicas)│           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  Virtual    │ │  Listing    │ │   AI        │           │
│  │   Goods     │ │   Service   │ │   Service   │           │
│  │  Service    │ │             │ │             │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  基础设施层                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Redis     │ │ PostgreSQL  │ │   Kafka     │           │
│  │  (Cluster)  │ │  (Primary+  │ │  (Event     │           │
│  │             │ │   Replica)  │ │   Stream)   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐                           │
│  │   Jaeger    │ │  Prometheus │                           │
│  │  (Tracing)  │ │  + Grafana  │                           │
│  └─────────────┘ └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 服务拆分

| 服务 | 职责 | 端口 | 副本数 |
|------|------|------|--------|
| `message-service` | WebSocket 管理、AI 回复、对话上下文 | 8001 | 3 |
| `order-service` | 订单处理、状态机、虚拟商品核销 | 8002 | 2 |
| `quote-service` | 物流报价计算、成本表管理 | 8003 | 2 |
| `listing-service` | 商品上架、模板渲染 | 8004 | 2 |
| `ai-service` | 大模型调用、上下文管理、Prompt 工程 | 8005 | 2 |
| `gateway-service` | 闲管家 API 集成、签名、限流 | 8006 | 2 |
| `scheduler-service` | 定时任务、轮询、改价 | 8007 | 1 |

---

## 3. 核心组件设计

### 3.1 依赖注入框架

引入 `dependency-injector` 替代全局 `get_config()`：

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # 基础设施
    db_pool = providers.Singleton(asyncpg.create_pool, dsn=config.database.dsn)
    redis = providers.Singleton(redis.asyncio.Redis,
                                host=config.redis.host,
                                port=config.redis.port)

    # 仓库层
    message_repo = providers.Factory(MessageRepository, db_pool=db_pool)
    context_store = providers.Factory(ConversationContextStore, redis=redis)

    # 服务层
    ai_client = providers.Factory(DeepSeekClient,
                                  api_key=config.ai.deepseek_api_key)
    message_service = providers.Factory(MessageService,
                                        repository=message_repo,
                                        context_store=context_store,
                                        ai_client=ai_client)
```

### 3.2 AI 上下文增强系统

四层级上下文架构：

```
┌─────────────────────────────────────────┐
│  L3: 长期记忆 (User Profile)            │
│      └─ 用户偏好、历史成交、信用评分      │
│      └─ 存储: PostgreSQL (JSONB)        │
├─────────────────────────────────────────┤
│  L2: 会话记忆 (Session Memory)          │
│      └─ 当前对话历史 (最近 20 轮)        │
│      └─ 存储: Redis (TTL: 24h)          │
├─────────────────────────────────────────┤
│  L1: 意图状态 (Intent State)            │
│      └─ 当前报价进度、待确认信息          │
│      └─ 存储: Redis (TTL: 1h)           │
├─────────────────────────────────────────┤
│  L0: 请求上下文 (Request Context)       │
│      └─ 单次消息解析结果                 │
│      └─ 内存中临时存储                   │
└─────────────────────────────────────────┘
```

**对话状态机：**

```python
class ConversationState(Enum):
    IDLE = "idle"
    EXTRACTING_ORIGIN = "extracting_origin"
    EXTRACTING_DEST = "extracting_dest"
    EXTRACTING_WEIGHT = "extracting_weight"
    CONFIRMING_COURIER = "confirming_courier"
    QUOTED = "quoted"
    LOCKED = "locked"
```

### 3.3 WebSocket 连接池

```python
class WebSocketConnectionPool:
    """闲鱼 WebSocket 连接池"""

    def __init__(self):
        self._connections: dict[str, ManagedConnection] = {}
        self._health_checker = asyncio.create_task(self._health_check_loop())

    async def get_connection(self, account_id: str) -> WebSocketClient:
        """获取或创建连接"""
        if account_id not in self._connections:
            conn = await self._create_connection(account_id)
            self._connections[account_id] = ManagedConnection(
                client=conn,
                created_at=datetime.now(),
                last_ping=datetime.now()
            )
        return self._connections[account_id].client

    async def _health_check_loop(self):
        """健康检查 + 自动重连"""
        while True:
            for account_id, conn in list(self._connections.items()):
                if not conn.client.is_connected:
                    await self._reconnect(account_id)
                elif datetime.now() - conn.last_ping > timedelta(seconds=30):
                    await conn.client.ping()
                    conn.last_ping = datetime.now()
            await asyncio.sleep(5)
```

### 3.4 事件驱动架构

Kafka 主题设计：

| 主题 | 生产者 | 消费者 | 说明 |
|------|--------|--------|------|
| `orders.paid` | order-service | virtual-goods-service, analytics-service | 订单支付事件 |
| `messages.received` | message-service | ai-service, analytics-service | 新消息事件 |
| `quotes.calculated` | quote-service | message-service | 报价完成事件 |
| `listings.published` | listing-service | analytics-service | 商品上架事件 |
| `cookies.expired` | gateway-service | message-service, scheduler-service | Cookie 过期事件 |

---

## 4. 数据存储

### 4.1 数据迁移方案

| 数据类型 | 当前 | 迁移到 | 策略 |
|---------|------|--------|------|
| 配置 | YAML + JSON | ConfigMap + etcd | 初始化脚本 |
| 订单 | SQLite | PostgreSQL | pgloader |
| Cookie | 本地文件 | HashiCorp Vault | 安全迁移工具 |
| 会话状态 | 内存 | Redis | 双写过渡 |
| 消息历史 | SQLite | PostgreSQL | 按月分表 |

### 4.2 PostgreSQL 表结构

```sql
-- 用户画像表
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    xianyu_user_id VARCHAR(64) UNIQUE NOT NULL,
    preferences JSONB DEFAULT '{}',
    transaction_history JSONB DEFAULT '[]',
    credit_score INT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 会话表
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(128) UNIQUE NOT NULL,
    account_id VARCHAR(64) NOT NULL,
    buyer_id VARCHAR(64) NOT NULL,
    current_state VARCHAR(32) DEFAULT 'idle',
    context_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 消息历史表（按月分表）
CREATE TABLE messages_2026_03 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(16) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);
```

---

## 5. 可观测性

### 5.1 结构化日志

使用 `structlog`：

```python
logger.info(
    "quote_calculated",
    origin="广东省",
    dest="浙江省",
    weight=3.0,
    price=12.5,
    latency_ms=45,
    model="deepseek-chat"
)
```

### 5.2 指标监控

Prometheus 指标定义：

```python
from prometheus_client import Counter, Histogram, Gauge

messages_received = Counter(
    'xianyu_messages_received_total',
    'Total messages received',
    ['account_id']
)

quote_calculation_duration = Histogram(
    'xianyu_quote_calculation_duration_seconds',
    'Quote calculation duration',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

ws_connection_status = Gauge(
    'xianyu_ws_connection_status',
    'WebSocket connection status (1=connected, 0=disconnected)',
    ['account_id']
)
```

### 5.3 分布式追踪

OpenTelemetry 配置：

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_message") as span:
    span.set_attribute("message.session_id", session_id)
    span.set_attribute("message.buyer_id", buyer_id)
    # ... 业务逻辑
```

---

## 6. Kubernetes 部署

### 6.1 Helm Chart 结构

```
helm/xianyuflow/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment-message.yaml
    ├── deployment-order.yaml
    ├── deployment-quote.yaml
    ├── deployment-listing.yaml
    ├── deployment-ai.yaml
    ├── deployment-gateway.yaml
    ├── deployment-scheduler.yaml
    ├── service-*.yaml
    ├── ingress.yaml
    ├── configmap.yaml
    ├── secret.yaml
    └── hpa-*.yaml
```

### 6.2 HPA 配置

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: message-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: message-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: websocket_connections
      target:
        type: AverageValue
        averageValue: "500"
```

---

## 7. 实施路线图

### Phase 1: 基础设施（4周）

- [ ] 搭建 K8s 集群（EKS/GKE/自建）
- [ ] 部署 Redis Cluster（6 节点）
- [ ] 部署 PostgreSQL（主从 + 连接池）
- [ ] 部署 Kafka（3 节点）
- [ ] 配置 CI/CD（GitHub Actions → ArgoCD）
- [ ] 部署可观测性栈（Prometheus + Grafana + Jaeger）

**交付物：**
- 基础设施 Terraform 代码
- K8s 部署 YAML
- 监控大盘配置

### Phase 2: 服务拆分（6周）

- [ ] 创建基础镜像（Python 3.12 + FastAPI）
- [ ] 拆分 `gateway-service`（闲管家 API 封装）
- [ ] 拆分 `quote-service`（物流报价）
- [ ] 拆分 `ai-service`（大模型调用）
- [ ] 拆分 `message-service`（WebSocket + AI 回复）
- [ ] 引入事件总线（Kafka）
- [ ] 服务间通信 gRPC

**交付物：**
- 6 个微服务代码仓库
- gRPC Proto 定义
- API 网关配置

### Phase 3: AI 增强（4周）

- [ ] 实现上下文层级系统
- [ ] 对话状态机重构
- [ ] 用户画像系统
- [ ] Prompt 版本管理
- [ ] A/B 测试框架

**交付物：**
- 上下文管理服务
- 用户画像 API
- Prompt 管理平台

### Phase 4: 性能优化（3周）

- [ ] WebSocket 连接池
- [ ] Redis 缓存策略
- [ ] PostgreSQL 查询优化
- [ ] 连接池调优
- [ ] 负载测试

**交付物：**
- 性能测试报告
- 优化配置文档

### Phase 5: 迁移与灰度（3周）

- [ ] 数据迁移脚本
- [ ] 双写过渡期
- [ ] 灰度发布（10% → 50% → 100%）
- [ ] 回滚方案验证
- [ ] 监控告警配置

**交付物：**
- 迁移操作手册
- 回滚脚本
- 监控告警规则

---

## 8. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 数据迁移失败 | 中 | 高 | 完整备份 + 回滚脚本 |
| 服务拆分引入 Bug | 高 | 中 | 完整测试 + 灰度发布 |
| K8s 学习成本 | 中 | 低 | 培训 + 文档 |
| 闲鱼 API 变更 | 低 | 高 | 抽象适配层 |
| 成本超支 | 中 | 中 | 分阶段投入 |

---

## 9. 附录

### 9.1 技术选型理由

| 技术 | 选择理由 |
|------|----------|
| FastAPI | 高性能异步框架，自动 API 文档 |
| PostgreSQL | JSONB 支持，复杂查询性能优秀 |
| Redis | 会话存储、缓存、Pub/Sub 一体化 |
| Kafka | 高吞吐事件流，生态系统成熟 |
| Kubernetes | 云原生标准，自动扩缩容 |
| Jaeger | OpenTelemetry 原生支持 |

### 9.2 废弃决策

以下当前组件将被废弃：

| 组件 | 原因 | 替代方案 |
|------|------|----------|
| `mimic_ops.py` | 过于庞大 | 拆分为多个 Service |
| `get_config()` | 全局状态 | 依赖注入框架 |
| SQLite | 并发限制 | PostgreSQL |
| 本地文件 Cookie | 安全性差 | HashiCorp Vault |
| 单进程 WebSocket | 无法扩展 | 连接池 + 多副本 |

---

*文档版本：v1.0*
*最后更新：2026-03-27*
