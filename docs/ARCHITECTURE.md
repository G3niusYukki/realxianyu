# XianyuFlow | 闲流架构设计文档

> 最后更新：2026-03-27
> 状态：按当前本地工作区实测校准

## 一、系统概述

XianyuFlow | 闲流（XianyuFlow | 闲流）是一个闲鱼平台自动化运营工具，提供：
- 自动消息回复与智能报价（物流/虚拟商品）
- 订单履约与虚拟商品核销
- 商品上架、擦亮、调价等运营自动化
- AI 驱动的文案生成和增长分析

**技术栈**：Python 3.12+ (asyncio) + React/Vite + SQLite

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (client/)                     │
│   React + TailwindCSS SPA，编译后静态资源由后端服务         │
│   API 调用 → /api/* HTTP Routes                           │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼───────────────────────────────────┐
│                 网关层 (src/dashboard_server.py)            │
│   BaseHTTPRequestHandler，轻量路由 + 静态文件服务           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   业务中枢 (mimic_ops.py)                   │
│   Facade 代理，分发到 Services 和 Modules                  │
└────┬──────────────┬──────────────┬──────────────┬──────────┘
     │              │              │              │
┌────▼────┐  ┌──────▼───┐  ┌─────▼─────┐  ┌────▼─────┐
│dashboard/│  │ modules/ │  │integrations│ │  cli/    │
│services/ │  │          │  │            │  │          │
│Cookie   │  │Messages  │  │Xianguanjia │  │cmd_main  │
│XGJ      │  │Orders    │  │OpenPlatform│  │cmd_orders│
│         │  │Quote     │  │            │  │cmd_module│
│         │  │Listing   │  │            │  │cmd_quote │
│         │  │VirtualGoods│ │            │  │          │
│         │  │Growth    │  │            │  │          │
│         │  │Operations│  │            │  │          │
└─────────┘  └──────────┘  └────────────┘  └──────────┘
```

---

## 三、目录结构

```
src/
├── core/                         # 核心基础设施（不可分割）
│   ├── config.py                 # YAML 配置管理（单一真相来源）
│   ├── logger.py                 # 日志基础设施
│   ├── browser_client.py         # 浏览器客户端抽象
│   ├── cookie_manager.py         # Cookie 管理
│   ├── crypto.py                 # 加密工具
│   ├── error_handler.py          # 统一异常处理
│   ├── startup_checks.py         # 启动检查
│   └── doctor.py                 # 运维诊断
│
├── modules/                      # 业务模块（各自独立）
│   ├── messages/                 # 消息 WS、长连接、回复引擎
│   │   ├── service.py            # MessagesService（消息中枢）
│   │   ├── ws_live.py            # WebSocket 实时通信
│   │   ├── reply_engine.py        # 回复引擎
│   │   ├── workflow.py            # 消息工作流
│   │   └── quote_parser.py       # 报价解析
│   │
│   ├── orders/                   # 订单履约
│   │   ├── service.py            # OrderService
│   │   └── auto_price_poller.py  # 自动改价轮询
│   │
│   ├── quote/                    # 物流报价引擎
│   │   ├── engine.py             # QuoteEngine
│   │   ├── cost_table.py         # 成本表管理
│   │   ├── route.py              # 路由解析
│   │   ├── providers.py          # 外部 API 提供方
│   │   └── setup.py              # 报价设置
│   │
│   ├── listing/                  # 商品上架
│   │   ├── service.py            # ListingService
│   │   ├── templates/            # 文案模板系统
│   │   │   ├── frames/          # 15 种样式框架
│   │   │   ├── layers/          # 内容分层
│   │   │   └── registry.py      # 模板注册表
│   │   └── publish_queue.py      # 上架队列
│   │
│   ├── virtual_goods/            # 虚拟商品核销
│   │   ├── service.py            # VirtualGoodsService
│   │   ├── store.py              # 店铺管理
│   │   ├── scheduler.py          # 调度器
│   │   └── callbacks.py          # 回调处理
│   │
│   ├── growth/                   # 增长分析
│   │   └── service.py            # GrowthService
│   │
│   ├── operations/               # 运营操作
│   │   └── service.py            # OperationsService
│   │
│   └── ticketing/                # 电影票服务
│       └── service.py            # TicketingService
│
├── integrations/                 # 外部 API 集成
│   └── xianguanjia/             # 闲管家 API
│       ├── open_platform_client.py
│       ├── virtual_supply_client.py
│       └── signing.py           # 签名算法
│
├── dashboard/                   # Dashboard 相关
│   ├── mimic_ops.py             # [精简] Facade 代理 (~3000行)
│   ├── services/                # 核心业务服务（从 mimic_ops 拆分）
│   │   ├── cookie_service.py    # CookieService
│   │   └── xgj_service.py       # XGJService
│   ├── config_service.py        # Dashboard 配置 CRUD（JSON）
│   ├── module_console.py        # 模块控制台
│   ├── repository.py            # 数据仓库
│   └── routes/                  # HTTP 路由
│       ├── accounts.py
│       ├── config.py
│       ├── messages.py
│       ├── orders.py
│       ├── products.py
│       ├── rule_suggestions.py
│       └── system.py
│
├── cli/                         # [重构后] CLI 命令包
│   ├── __init__.py              # 兼容垫片
│   ├── __main__.py              # python -m src.cli
│   ├── base.py                  # 公共辅助函数
│   ├── main.py                  # CLI 入口
│   ├── cmd_main.py              # publish/polish/price/delist...
│   ├── cmd_orders.py            # orders/virtual-goods
│   ├── cmd_module.py            # module/doctor/automation...
│   └── cmd_quote.py             # quote
│
├── dashboard_server.py          # HTTP 服务器入口（Dashboard + API + 静态资源）
├── main.py                      # 模块预加载入口（非常驻服务）
└── setup_wizard.py              # 初始化向导
```

---

## 四、配置系统

### 设计原则
- **YAML 是单一真相来源**（`config/config.yaml`）
- **JSON 是 Dashboard UI 覆盖**（`data/system_config.json`）
- **环境变量最高优先级**（`.env` / shell environment）
- **无冗余同步**：Dashboard 编辑后通过 `Config._merge_system_config()` 自动合并

### 配置合并顺序
```
config/config.yaml < data/system_config.json < .env / shell environment
```

### 关键配置文件
| 文件 | 用途 |
|------|------|
| `config/config.yaml` | 主配置（含所有运行时默认值） |
| `data/system_config.json` | Dashboard UI 持久化（敏感信息在此） |
| `.env` | 环境变量（API 密钥、凭证等） |

---

## 五、数据流

### 消息自动回复流程
```
用户发消息
    ↓
WS 连接通知 (ws_live.py)
    ↓
MessagesService.receive_message()
    ↓
ReplyEngine 生成回复（含 AI 报价）
    ↓
QuoteEngine 计算物流价格
    ↓
WS 发送回复
```

### 商品上架流程
```
CLI / Dashboard 触发
    ↓
ListingService.publish_item()
    ↓
Xianguanjia OpenPlatform API
    ↓
TemplateRegistry 生成文案
    ↓
上传图片到 OSS
    ↓
回调确认
```

### 虚拟商品核销流程
```
订单支付通知
    ↓
VirtualGoodsService.handle_order()
    ↓
卡密发货 / 自动标记已发货
    ↓
回调确认完成
```

---

## 六、前端架构 (client/)

```
client/src/
├── api/              # API 客户端层（369行，极简）
│   ├── index.ts      # 统一导出
│   ├── accounts.ts   # 账号 API
│   ├── config.ts     # 配置 API
│   ├── dashboard.ts  # Dashboard API
│   ├── listing.ts    # 商品 API
│   └── xianguanjia.ts
│
├── components/       # 通用 UI 组件
│   ├── ApiStatusPanel.tsx
│   ├── ErrorBoundary.tsx
│   ├── IntentRulesManager.tsx
│   ├── Navbar.tsx
│   ├── Pagination.tsx
│   ├── SetupGuide.tsx
│   ├── SetupWizard.tsx
│   └── UpdateBanner.tsx
│
├── contexts/         # React Context（全局状态）
│   └── StoreCategoryContext.tsx
│
├── hooks/            # 自定义 Hooks
│   └── useHealthCheck.ts
│
├── pages/            # 页面
│   ├── accounts/
│   ├── analytics/
│   ├── config/
│   ├── Dashboard.tsx
│   ├── messages/
│   ├── Orders.tsx
│   └── products/
│
├── styles/           # 全局样式
└── App.tsx           # 应用入口
```

**前端原则**：轻量 API 层 + 组件化 UI + 通过 Axios / React Context 组织状态

---

## 七、依赖注入现状

目前项目中混用了两种模式：
1. **全局函数**：`get_config()` — 被 24 个文件使用
2. **构造函数注入**：部分 Service 使用

**改进方向**：
- 逐步将 `get_config()` 替换为通过构造函数注入 `ConfigService`
- 已抽取的 Services（`CookieService`、`XGJService`）接受 `project_root` 参数

---

## 八、测试覆盖

| 模块 | 覆盖文件数 |
|------|-----------|
| `src/core/` | ~15 |
| `src/modules/messages/` | ~10 |
| `src/modules/orders/` | ~8 |
| `src/modules/quote/` | ~14 |
| `src/modules/listing/` | ~30 |
| `src/modules/virtual_goods/` | ~10 |
| `src/dashboard/` | ~15 |

**运行测试**：`./venv/bin/python -m pytest tests/ -q`
**代码规范**：先安装 `requirements-dev.txt`，再执行 `./venv/bin/python -m ruff check src/` 和 `./venv/bin/python -m ruff format src/ --check`

---

## 九、已知的架构问题与改进计划

### 已完成
- [x] `mimic_ops.py` 拆分为 Services（4241行 → 3070行）
- [x] CLI 拆分为独立模块（cli.py 2022行 → cli/ 包）
- [x] 识别并保留 ticketing/growth（存在功能依赖）
- [x] 识别并保留 templates/frames（Dashboard 使用）
- [x] 消除所有 `global` 声明（ws_live.py、service.py、ledger.py、routes/system.py 等 → 单例类）
- [x] 统一配置系统，删除 ConfigSyncService（YAML 同步是死代码，Config._merge_system_config() 已处理）

### 进行中
- [ ] `mimic_ops.py` 进一步拆分（目标：降至 2000 行以内）
- [ ] `get_config()` 全局函数逐步替换为 DI

### 待办
- [ ] 前端 API 层审视（当前 369 行，轻量，暂无明显问题）
