# API 文档

> 闲鱼管家 HTTP API 完整参考

**Base URL**: `http://localhost:8091` (Python Core)

---

## 概述

当前主线有两套 HTTP 服务：

- **Python Core** (`:8091`)：核心业务接口，主要服务层
- **Node Proxy** (`:3001`)：薄代理与 webhook 验签（辅助）

前端工作台直接调用 Python 接口；Node 仅负责代理和 webhook 场景。

**内容类型**: `application/json`
**字符编码**: `UTF-8`

---

## 标准响应格式

所有 API 返回统一格式：

```json
{
  "ok": true,
  "data": { },
  "error": null
}
```

或错误时：

```json
{
  "ok": false,
  "error": "错误描述",
  "code": "ERROR_CODE"
}
```

## Python Core

### 健康与状态

#### GET /healthz

健康检查端点，返回系统整体健康状态。

**响应示例**:
```json
{
  "ok": true,
  "db": true,
  "modules": {
    "system_running": "alive",
    "alive_count": "8",
    "total_modules": "10"
  },
  "uptime_seconds": 3600,
  "generated_at": "2026-03-24T10:30:00"
}
```

---

#### GET /api/status

获取模块详细状态。

**响应示例**:
```json
{
  "ok": true,
  "status": {
    "messages": "running",
    "orders": "running",
    "virtual_goods": "stopped"
  }
}
```

---

#### GET /api/summary

获取 Dashboard 数据汇总。

---

#### GET /api/trend

获取趋势数据。

**查询参数**:
- `days` (可选): 天数范围，默认 7

---

#### GET /api/top-products

获取热门商品列表。

---

#### GET /api/recent-operations

获取最近操作记录。

### 配置与账号

#### GET /api/config

获取系统配置。

**响应示例**:
```json
{
  "ok": true,
  "config": {
    "ai": {
      "provider": "deepseek",
      "model": "deepseek-chat"
    },
    "auto_reply": {
      "enabled": true,
      "default_reply": "您好，请问有什么可以帮您？"
    }
  }
}
```

---

#### POST /api/config

更新系统配置。

**请求体**:
```json
{
  "ai": {
    "api_key": "sk-..."
  }
}
```

**响应示例**:
```json
{
  "ok": true,
  "message": "配置已更新"
}
```

---

#### GET /api/config/sections

获取可配置分区列表。

**响应示例**:
```json
{
  "ok": true,
  "sections": ["ai", "auto_reply", "notifications", "xianguanjia"]
}
```

---

#### GET /api/config/setup-progress

获取初始化完成进度。

**响应示例**:
```json
{
  "ok": true,
  "progress": {
    "completed": 4,
    "total": 6,
    "percentage": 66.7,
    "checks": {
      "store_category": true,
      "xianguanjia": true,
      "ai": true,
      "auto_reply": true,
      "notifications": false
    }
  }
}
```

---

#### GET /api/accounts

获取账号列表及状态。

---

#### POST /api/update-cookie

更新闲鱼 Cookie。

**请求体**:
```json
{
  "cookie": "_tb_token_=xxx; cookie2=xxx; ...",
  "account_id": 1
}
```

### 商品、订单与闲管家

#### GET /api/xgj/products

获取闲管家商品列表。

**查询参数**:
- `page` (可选): 页码，默认 1
- `page_size` (可选): 每页数量，默认 20

**响应示例**:
```json
{
  "ok": true,
  "products": [
    {
      "id": "12345",
      "title": "商品标题",
      "price": 100.00,
      "status": "onsale"
    }
  ],
  "total": 100
}
```

---

#### GET /api/xgj/orders

获取闲管家订单列表。

**查询参数**:
- `status` (可选): 订单状态筛选
- `page` (可选): 页码

---

#### POST /api/xgj/settings

更新闲管家设置。

**请求体**:
```json
{
  "app_key": "your_app_key",
  "app_secret": "your_app_secret",
  "auto_price": true,
  "auto_delivery": true
}
```

---

#### POST /api/xgj/retry-price

重试改价操作。

**请求体**:
```json
{
  "order_id": "order_123"
}
```

---

#### POST /api/xgj/retry-ship

重试发货操作。

**请求体**:
```json
{
  "order_id": "order_123"
}
```

---

#### POST /api/xgj/product/publish

发布商品。

**请求体**:
```json
{
  "title": "商品标题",
  "desc": "商品描述",
  "price": 100.00,
  "images": ["url1", "url2"]
}
```

---

#### POST /api/xgj/product/unpublish

下架商品。

**请求体**:
```json
{
  "product_id": "12345"
}
```

---

#### POST /api/xgj/order/modify-price

修改订单价格。

**请求体**:
```json
{
  "order_id": "order_123",
  "new_price": 90.00
}
```

---

#### POST /api/xgj/order/deliver

订单发货。

**请求体**:
```json
{
  "order_id": "order_123",
  "tracking_no": "SF1234567890",
  "courier": "SF"
}
```

---

#### POST /api/orders/callback

闲管家订单回调接口（用于 webhook）。

**请求体**: 闲管家回调原始数据

### 自动上架

- `GET /api/listing/templates`
- `POST /api/listing/preview`
- `POST /api/listing/publish`
- `GET /api/generated-image?path=...`

### 运行控制与诊断

- `POST /api/module/control`
- `GET /api/module/status`
- `GET /api/module/check`
- `GET /api/module/logs`
- `POST /api/service/control`
- `POST /api/service/recover`
- `POST /api/service/auto-fix`
- `GET /api/logs/files`
- `GET /api/logs/content`
- `GET /api/logs/realtime/stream`

### 兼容保留的 Dashboard / 运维接口

这些接口仍然存在，但不再是 React 工作台的主要入口：

- `GET /api/dashboard`
- `GET /api/virtual-goods/metrics`
- `GET /api/virtual-goods/inspect-order`
- `POST /api/virtual-goods/inspect-order`
- `GET /api/get-cookie`
- `GET /api/route-stats`
- `GET /api/export-routes`
- `GET /api/download-cookie-plugin`
- `GET /api/get-template`
- `GET /api/replies`
- `GET /api/get-markup-rules`
- `POST /api/import-cookie-plugin`
- `POST /api/parse-cookie`
- `POST /api/cookie-diagnose`
- `POST /api/import-routes`
- `POST /api/import-markup`
- `POST /api/reset-database`
- `POST /api/save-template`
- `POST /api/save-markup-rules`
- `POST /api/test-reply`

### 兼容保留的 HTML 运维页面

- `GET /`
- `GET /cookie`
- `GET /test`
- `GET /logs`
- `GET /logs/realtime`

它们是历史 Dashboard / 内部诊断界面，不是当前主工作台。

## Node Proxy

### 健康检查

- `GET /health`

### 配置代理

- `GET /api/config`
- `POST /api/config`
- `PUT /api/config`
- `GET /api/config/sections`

这些接口只是把请求转发给 Python。

### 闲管家代理 / webhook

- `POST /api/xgj/proxy`
- `POST /api/xgj/order/receive`
- `POST /api/xgj/product/receive`

说明：

- `/api/xgj/proxy` 用于透传 Open Platform 请求。
- `/api/xgj/*/receive` 会先做签名校验，再转发给 Python `/api/orders/callback` 等回调接口。

## CLI

项目仍保留：

```bash
python -m src.cli
```

它用于模块诊断和恢复，不再承担旧式 OpenClaw 主调度职责。

## 约束

- 所有前端页面都必须走真实接口。
- 不允许为了展示而在接口层返回 mock 数据。
- Python 是唯一业务真相源，Node 不是配置真相源。
- `Legacy Browser Runtime` 只作为补充链路保留，不能重新成为默认依赖。
