# CLAUDE.md — 闲鱼管家 (Xianyu Guanjia)

## 项目概述

闲鱼平台自动化运营工具：自动消息回复、智能报价、订单履约、商品上架、虚拟商品核销。

**技术栈**：Python 3.12+ (asyncio) + React/Vite + SQLite
**远端**：`https://github.com/G3niusYukki/realxianyu`

## 目录结构

```
src/
├── core/            # 核心基础设施（配置、日志、浏览器客户端）
├── services/        # 从 mimic_ops 拆分的服务（cookie/xgj/config_sync）
├── modules/         # 业务模块（messages/orders/quote/listing/virtual_goods/...）
├── integrations/    # 闲管家 API 集成
├── dashboard/        # Dashboard（mimic_ops.py Facade + routes/）
├── dashboard/services/  # 已从 mimic_ops 拆分的服务
├── cli/             # CLI 命令包（cmd_main/cmd_orders/cmd_module/cmd_quote）
└── main.py          # 程序入口
```

## 关键文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/dashboard/mimic_ops.py` | ~3070 | Facade 代理，分发到 services/ 和 modules/ |
| `src/cli/main.py` | - | CLI 入口 |
| `src/core/config.py` | - | 配置管理（YAML 单一真相来源） |
| `src/dashboard/config_service.py` | - | Dashboard JSON 配置 CRUD |

## 配置系统

- **YAML**（`config/config.yaml`）是单一真相来源
- **JSON**（`data/system_config.json`）是 Dashboard UI 覆盖
- `.env` 是环境变量（最高优先级）
- 无需手动同步，Dashboard 编辑后通过 `Config._merge_system_config()` 自动合并

## 关键约束

1. **不要在 `mimic_ops.py` 中添加新业务逻辑** — 应该添加到对应的 `modules/` 或 `services/` 中
2. **不要使用 `global` 声明** — 使用单例类或依赖注入
3. **配置优先读 YAML** — 新配置项应添加到 `config.yaml`，不要创建新的配置源
4. **测试必须通过** — 所有 PR 必须通过 `pytest tests/ -q`

## 运行命令

```bash
# 安装依赖
pip install -r requirements.txt
cd client && npm install && npm run build && cd ..

# 启动后端
python -m src.main

# 运行测试
./venv/bin/python -m pytest tests/ -q

# 代码规范检查
ruff check src/ && ruff format src/
```

## 测试文件命名约定

- `test_模块名_cov100.py` — 100% 覆盖率测试
- `test_模块名_full.py` — 完整功能测试
- `test_模块名_more.py` — 扩展测试

## 常见 import 模式

```python
from src.core.config import get_config
from src.modules.messages.service import MessagesService
from src.modules.quote.engine import QuoteEngine
from src.dashboard.mimic_ops import MimicOps
```
