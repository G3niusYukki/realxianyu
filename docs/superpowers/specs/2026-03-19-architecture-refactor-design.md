# 闲鱼管家架构重构设计

> 日期：2026-03-19
> 状态：已批准
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
- [ ] 提取 `CookieService` → `services/cookie_service.py`
- [ ] 提取 `ConfigSyncService` → `services/config_sync_service.py`
- [ ] 提取 `ProductService` → `services/product_service.py`
- [ ] 提取 `QuoteService` → `services/quote_service.py`
- [ ] 提取 `OperationService` → `services/operation_service.py`
- [ ] 原 `mimic_ops.py` 降为 Facade 代理（保留接口兼容）
- [ ] 每个服务补充行为测试

### 阶段 3：统一配置系统
- [ ] YAML 作为单一真相来源
- [ ] 迁移 `system_config.json` 到 `config.yaml`
- [ ] 移除 `_sync_system_config_to_yaml` 同步逻辑
- [ ] 移除/降级 `config_service.py`

### 阶段 4：消除全局状态
- [ ] `global _ws_transport_instance` → `WebSocketTransportManager` 单例
- [ ] `global _active_service` → `MessageServiceRegistry` 显式注册
- [ ] 替换 `get_config()` 全局函数 → 依赖注入 `ConfigService`
- [ ] 全程测试通过

### 阶段 5：拆分 CLI
- [ ] `cli.py` → `cli/` 包（base + 4个命令模块）
- [ ] 公共参数解析抽取到 `base.py`
- [ ] 删除原 `cli.py`

### 阶段 6：前端审视 + 文档
- [ ] 审查 `client/src/api/` 冗余 API
- [ ] 审查 `contexts/` 全局状态
- [ ] 新建 `docs/ARCHITECTURE.md`
- [ ] 更新 `README.md`
- [ ] 新建 `CLAUDE.md`

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

- 所有现有测试继续通过（回归测试）
- 每个新服务独立可导入、可测试
- 无 `global` 声明残留
- 无两套配置系统并存
- `mimic_ops.py` 降至 1000 行以内（Facade 模式）
- `cli.py` 拆分完毕，原文件删除
- 文档与代码结构一致
