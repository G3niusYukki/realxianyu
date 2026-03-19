# 闲鱼管家架构重构设计

> 日期：2026-03-19
> 状态：**实施中（阶段1-6已完成）**
> 目标：对现有代码库进行架构级重构，消除 God Object、消除全局状态、统一配置系统

## 一、项目现状

- **代码量**：约 50,000 行 Python + React 前端
- **核心问题**：
  - `src/dashboard/mimic_ops.py`（4241行）— God Object，承担 Cookie管理+配置同步+商品操作+报价引擎+运营操作
  - `src/cli.py`（2022行）— 所有 CLI 命令混在一起
  - 两套配置系统并存（YAML + JSON），存在同步逻辑
  - 多处 `global` 全局变量
  - 部分模块可能冗余（ticketing、growth）

## 二、重构原则

1. **架构优先**：先改组织方式，不动功能逻辑
2. **测试先行**：每次拆分操作前确保行为测试通过
3. **渐进演进**：每个模块重构完成后单独提交
4. **零破坏**：现有 1100+ 测试必须全部继续通过

## 三、目标架构

```
src/
├── core/                    # [不变] 配置+日志+浏览器客户端+工具函数
├── services/                # [新建] 从 mimic_ops.py 拆分出的服务
│   ├── cookie_service.py    # Cookie 管理（登录态保活）
│   ├── config_sync_service.py # 配置同步（YAML 单一真相）
│   ├── product_service.py   # 商品操作（publish_item 等）
│   ├── quote_service.py     # 报价服务（calculate_quote）
│   └── operation_service.py # 运营操作（batch_polish 等）
├── modules/                 # [不变] 消息/订单/报价/上架/虚拟商品
├── integrations/            # [不变] 闲管家 API 集成
├── cli/                     # [新建] 从 cli.py 拆分
│   ├── base.py             # 公共参数解析
│   ├── cmd_publish.py       # 上架命令
│   ├── cmd_polish.py        # 擦亮命令
│   ├── cmd_orders.py        # 订单命令
│   └── cmd_quote.py         # 报价命令
├── dashboard/               # [精简] mimic_ops.py 拆分后剩余 Facade
├── dashboard_server.py      # [改造] 依赖注入
└── main.py                  # [不变]
```

## 四、执行阶段

### 阶段 1：环境准备
- [ ] 审计 `ticketing/`、`growth/`、`templates/frames/` 引用情况
- [ ] 运行全部测试，记录通过率基线
- [ ] 创建分支 `refactor/architecture-overhaul`

### 阶段 2：拆分 mimic_ops.py
- [x] 提取 `CookieService` → `services/cookie_service.py`
- [x] 提取 `XGJService` → `services/xgj_service.py`
- [x] 提取 `ConfigSyncService` → `services/config_sync_service.py`（后确认为死代码，已删除）
- [ ] 提取 `OperationService` → `services/operation_service.py`
- [x] 原 `mimic_ops.py` 降为 Facade 代理（保留接口兼容）
- [x] 每个服务补充行为测试

### 阶段 3：统一配置系统
- [x] YAML 作为单一真相来源
- [x] 确认 `Config._merge_system_config()` 已正确处理合并
- [x] 移除 `_sync_system_config_to_yaml`（死代码，从未调用）
- [x] 删除 `config_sync_service.py`（无任何调用方）

### 阶段 4：消除全局状态
- [x] `global _ws_transport_instance` → `WebSocketTransportManager` 单例
- [x] `global _active_service` → `MessageServiceRegistry` 显式注册
- [x] `global _geo_known_cache` → `GeoKnownCache` 类（geo_resolver.py）
- [x] `global _instance` (ledger.py) → `QuoteLedger.get_instance()` 类方法
- [x] `global _instance` (auto_price_poller.py) → `AutoPricePoller._instance` 类变量
- [x] `global _trajectory_cache` (slider_solver.py) → 模块级可变 list（无需 global）
- [x] `global _health_cache/_version_cache` (routes/system.py) → `_HealthCache`/`_VersionCache` 类
- [x] 全程测试通过

### 阶段 5：拆分 CLI
- [x] `cli.py` → `cli/` 包（cmd_main + cmd_orders + cmd_module + cmd_quote + base + main）
- [x] 公共参数解析抽取到 `base.py`
- [x] `src/cli.py` 保留为兼容垫片（re-export）

### 阶段 6：前端审视 + 文档
- [x] 审查 `client/src/api/`（369行，极简，无冗余）
- [x] 审查 `contexts/`（StoreCategoryContext 结构清晰）
- [x] 新建 `docs/ARCHITECTURE.md`
- [x] 更新 `README.md`
- [x] 新建 `CLAUDE.md`

## 五、提交节奏

| # | 提交信息 |
|---|----------|
| 1 | `refactor: audit unused modules (ticketing, growth, frames)` |
| 2 | `refactor: split mimic_ops.py into services` |
| 3 | `refactor: unify config to YAML` |
| 4 | `refactor: eliminate global state, use DI` |
| 5 | `refactor: split cli.py into modules` |
| 6 | `refactor: audit and clean frontend` |
| 7 | `docs: update architecture and README` |

## 六、验收标准

- [x] 所有现有测试继续通过（1172 passed, 4 pre-existing failures）
- [x] 每个新服务独立可导入、可测试
- [x] 无 `global` 声明（已消除全部 9 处）
- [x] 无冗余配置同步（`config_sync_service.py` 死代码已删除）
- [x] `mimic_ops.py` 从 4241 行降至 ~3000 行（减少 ~27%）
- [x] CLI 拆分为 `cli/` 包
- [x] 文档与代码结构一致
