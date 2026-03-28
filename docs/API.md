# API 文档

> 当前 `main` 的运行时 API 分为两套：`8091` 的 Dashboard API 和 `8000` 的 Gateway API。

## 基本说明

- Dashboard UI + API：`http://127.0.0.1:8091`
- Gateway API：`http://127.0.0.1:8000`
- Vite `5173` 只用于前端开发，不是部署入口

当前仓库 **没有单一统一响应包裹格式**。不同路由会返回各自的 JSON 结构，因此不要假设所有接口都长成 `{ok,data,error}`。

## 一、Dashboard API (`8091`)

`src.dashboard_server` 同时托管前端静态资源和 `/api/*` 路由。

### GET /

返回 React SPA 的 `index.html`。这是浏览器应该打开的主入口。

### GET /healthz

返回 Dashboard 主服务健康状态。

示例：

```json
{
  "status": "ok",
  "timestamp": "2026-03-27T18:07:01",
  "database": "writable",
  "modules": {
    "system_running": "alive",
    "alive_count": "3",
    "total_modules": "3"
  },
  "uptime_seconds": 28139
}
```

### 常用 `/api/*` 路由

这些路由由 `src/dashboard/routes/` 注册：

- `/api/status`
- `/api/summary`
- `/api/trend`
- `/api/top-products`
- `/api/recent-operations`
- `/api/config*`
- `/api/accounts*`
- `/api/xgj/*`
- `/api/listing/*`
- `/api/logs/*`
- `/api/system/*`

如果要查具体实现，优先看：

- `src/dashboard/routes/config.py`
- `src/dashboard/routes/cookie.py`
- `src/dashboard/routes/orders.py`
- `src/dashboard/routes/products.py`
- `src/dashboard/routes/system.py`
- `src/dashboard/routes/dashboard_data.py`

## 二、Gateway API (`8000`)

`services/gateway-service` 是独立 FastAPI 服务，主要用于适配闲管家 Open Platform。

### GET /

返回网关元数据，不是前端页面。

示例：

```json
{
  "service": "gateway-service",
  "status": "healthy",
  "health": "/health",
  "docs": "/docs"
}
```

### GET /health

网关健康检查。

### GET /docs

Swagger UI。

### 当前公开业务路由

- `GET /api/v1/users/authorized`
- `GET /api/v1/products`
- `POST /api/v1/products`
- `GET /api/v1/orders`
- `POST /api/v1/orders/{order_id}/price`
- `POST /api/v1/orders/{order_id}/ship`

### 当前请求契约

网关已按当前仓库事实对齐为：

- Base URL 默认：`https://open.goofish.pro`
- 路径风格：`/api/open/*`
- Query 参数：`appid`、`timestamp`、`sign`
- 时间戳：秒级
- 兼容旧环境变量：`XGJ_APP_KEY`、`XGJ_APP_SECRET`、`XGJ_BASE_URL`

## 三、前端开发环境

前端开发时使用：

```bash
cd client
npm run dev
```

默认地址：

- `http://127.0.0.1:5173`

此时前端仍然需要后端 API，可按页面需要连接 `8091` 或 `8000`。

## 四、文档边界

这份文档只描述当前 `main` 的真实入口和高频接口，不再宣称“完整 v10 微服务 API 已全部文档化”。更细的闲管家接口参考请看：

- `docs/xianguanjiajieruapi.md`
- `docs/integrations/xianguanjia/normalized/open-platform/`
