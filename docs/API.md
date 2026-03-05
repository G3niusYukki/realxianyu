# API 文档

> 🔧 xianyu-openclaw CLI 命令参考

---

## 📋 概述

xianyu-openclaw 通过 **CLI（命令行接口）** 与 OpenClaw Gateway 交互。OpenClaw 的 Skills 通过 `bash` 工具调用 CLI 命令，所有命令返回结构化的 JSON 数据。

### 调用方式

```bash
python -m src.cli <command> [options]
```

或进入项目目录后：

```bash
cd /home/node/.openclaw/workspace && python -m src.cli <command> [options]
```

### 输出格式

所有命令默认输出 **JSON** 格式：

```json
{
  "success": true|false,
  "data": { ... },
  "message": "操作结果描述",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

### 退出码

| 退出码 | 含义 |
|-------|------|
| `0` | 成功 |
| `1` | 一般错误 |
| `2` | 配置错误 |
| `3` | 网络错误 |
| `4` | 认证错误 |

---

## 🏗️ 命令结构

### 全局选项

```bash
python -m src.cli --help              # 显示帮助信息
python -m src.cli --version           # 显示版本号
python -m src.cli --verbose           # 详细输出模式
```

### 命令模式

```bash
python -m src.cli <module> [--action <action>] [options]
```

**模块列表：**
- `publish` - 商品发布
- `polish` - 擦亮商品
- `price` - 价格管理
- `delist`/`relist` - 上下架管理
- `analytics` - 数据分析
- `accounts` - 账号管理
- `messages` - 消息处理
- `orders` - 订单管理
- `compliance` - 合规检查
- `growth` - 增长实验
- `ai` - AI 管理
- `doctor` - 系统诊断
- `automation` - 自动化配置
- `module` - 模块管理

---

## 📦 商品发布命令

### `publish` - 发布商品

发布新商品到闲鱼，支持 AI 自动生成文案。

**用法：**

```bash
python -m src.cli publish \
  --title "商品标题" \
  --price 5999 \
  [--description "商品描述"] \
  [--original-price 6999] \
  [--category "数码手机"] \
  [--images path/to/img1.jpg path/to/img2.jpg] \
  [--tags "95新 国行 配件齐全"]
```

**参数：**

| 参数 | 必填 | 说明 | 示例 |
|-----|------|------|------|
| `--title` | ✅ | 商品标题（10-30字） | `"iPhone 15 Pro 256G 95新"` |
| `--price` | ✅ | 售价（数字） | `5999` |
| `--description` | ❌ | 商品描述 | `"自用闲置..."` |
| `--original-price` | ❌ | 原价 | `6999` |
| `--category` | ❌ | 分类 | `"数码手机"` |
| `--images` | ❌ | 图片路径（空格分隔） | `img1.jpg img2.jpg` |
| `--tags` | ❌ | 标签（空格分隔） | `"95新 国行"` |

**示例：**

```bash
python -m src.cli publish \
  --title "【自用出】iPhone 15 Pro 256G 原色钛金属 95新" \
  --price 5999 \
  --description "自用出闲置 iPhone 15 Pro，256GB，原色钛金属，95新成色，无磕碰无划痕，配件齐全。" \
  --category "数码手机" \
  --tags "95新 国行 配件齐全 iPhone"
```

**成功响应：**

```json
{
  "success": true,
  "data": {
    "product_id": "7123456789012345678",
    "product_url": "https://www.goofish.com/item/7123456789012345678",
    "title": "【自用出】iPhone 15 Pro 256G 原色钛金属 95新",
    "price": 5999,
    "status": "published",
    "created_at": "2026-03-05T10:30:00Z"
  },
  "message": "✅ 商品发布成功！",
  "timestamp": "2026-03-05T10:30:05Z"
}
```

**错误响应：**

```json
{
  "success": false,
  "data": null,
  "message": "发布失败：价格不能为负数",
  "error_code": "INVALID_PRICE",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

## ✨ 运营管理命令

### `polish` - 擦亮商品

擦亮商品以提高曝光率。

**用法：**

```bash
# 擦亮所有商品
python -m src.cli polish --all [--max 50]

# 擦亮指定商品
python -m src.cli polish --id <item_id>
```

**参数：**

| 参数 | 必填 | 说明 | 示例 |
|-----|------|------|------|
| `--all` | 条件 | 擦亮所有商品（与 --id 二选一） | - |
| `--id` | 条件 | 指定商品 ID | `"7123456789012345678"` |
| `--max` | ❌ | 最大擦亮数量 | `50` |

**示例：**

```bash
# 擦亮所有商品（最多 50 个）
python -m src.cli polish --all --max 50
```

**成功响应：**

```json
{
  "success": true,
  "data": {
    "polished_count": 23,
    "skipped_count": 0,
    "failed_count": 0,
    "items": [
      {
        "id": "7123456789012345678",
        "title": "iPhone 15 Pro",
        "status": "polished"
      }
    ]
  },
  "message": "✅ 已擦亮 23 件商品",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

### `price` - 修改价格

修改商品价格。

**用法：**

```bash
python -m src.cli price --id <item_id> --price <new_price>
```

**参数：**

| 参数 | 必填 | 说明 | 示例 |
|-----|------|------|------|
| `--id` | ✅ | 商品 ID | `"7123456789012345678"` |
| `--price` | ✅ | 新价格 | `4999` |

**示例：**

```bash
python -m src.cli price \
  --id "7123456789012345678" \
  --price 4999
```

**成功响应：**

```json
{
  "success": true,
  "data": {
    "item_id": "7123456789012345678",
    "old_price": 5999,
    "new_price": 4999,
    "title": "iPhone 15 Pro"
  },
  "message": "✅ 价格已更新为 ¥4999",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

### `delist` - 下架商品

将商品下架。

**用法：**

```bash
python -m src.cli delist --id <item_id>
```

**示例：**

```bash
python -m src.cli delist --id "7123456789012345678"
```

**成功响应：**

```json
{
  "success": true,
  "data": {
    "item_id": "7123456789012345678",
    "status": "delisted"
  },
  "message": "✅ 商品已下架",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

### `relist` - 重新上架

将已下架的商品重新上架。

**用法：**

```bash
python -m src.cli relist --id <item_id>
```

**示例：**

```bash
python -m src.cli relist --id "7123456789012345678"
```

**成功响应：**

```json
{
  "success": true,
  "data": {
    "item_id": "7123456789012345678",
    "status": "active"
  },
  "message": "✅ 商品已重新上架",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

## 📊 数据分析命令

### `analytics` - 数据分析

查看店铺运营数据。

**用法：**

```bash
python -m src.cli analytics --action <action> [options]
```

**Actions：**

| Action | 说明 | 参数 |
|--------|------|------|
| `dashboard` | 仪表盘数据 | - |
| `daily` | 日报 | `--date YYYY-MM-DD` |
| `trend` | 趋势分析 | `--days 7` |
| `export` | 导出数据 | `--format csv` |

**示例 1：查看仪表盘**

```bash
python -m src.cli analytics --action dashboard
```

**响应：**

```json
{
  "success": true,
  "data": {
    "overview": {
      "total_items": 45,
      "active_items": 38,
      "today_views": 1247,
      "today_wants": 89,
      "today_orders": 12,
      "today_revenue": 38700
    },
    "trend": {
      "dates": ["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05"],
      "views": [1100, 1150, 1200, 1180, 1247],
      "orders": [8, 10, 11, 9, 12]
    },
    "top_items": [
      {
        "id": "7123456789012345678",
        "title": "iPhone 15 Pro",
        "views": 456,
        "wants": 23
      }
    ]
  },
  "message": "✅ 数据获取成功",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

**示例 2：查看日报**

```bash
python -m src.cli analytics --action daily --date 2026-03-04
```

**示例 3：导出趋势数据**

```bash
python -m src.cli analytics --action export --days 30 --format csv
```

---

## 👤 账号管理命令

### `accounts` - 账号管理

管理闲鱼账号。

**用法：**

```bash
python -m src.cli accounts --action <action>
```

**Actions：**

| Action | 说明 |
|--------|------|
| `list` | 列出所有账号 |
| `health` | 检查账号健康状态 |
| `refresh-cookie` | 刷新 Cookie |

**示例 1：列出账号**

```bash
python -m src.cli accounts --action list
```

**响应：**

```json
{
  "success": true,
  "data": {
    "accounts": [
      {
        "id": "account_1",
        "username": "卖家小王",
        "status": "active",
        "cookie_expires": "2026-03-25T10:30:00Z",
        "items_count": 45
      }
    ]
  },
  "message": "✅ 找到 1 个账号",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

**示例 2：健康检查**

```bash
python -m src.cli accounts --action health
```

---

## 💬 消息与客服命令

### `messages` - 消息处理

自动化消息回复和工作流。

**用法：**

```bash
python -m src.cli messages --action <action> [options]
```

**Actions：**

| Action | 说明 | 参数 |
|--------|------|------|
| `auto-reply` | 自动回复 | `--limit 20`, `--dry-run` |
| `auto-workflow` | 自动工作流 | `--dry-run` |
| `workflow-stats` | 工作流统计 | `--window-minutes 60` |

**示例 1：自动回复（干运行）**

```bash
python -m src.cli messages \
  --action auto-reply \
  --limit 20 \
  --dry-run
```

**示例 2：工作流统计**

```bash
python -m src.cli messages \
  --action workflow-stats \
  --window-minutes 60
```

**响应：**

```json
{
  "success": true,
  "data": {
    "window_minutes": 60,
    "processed": 45,
    "replied": 42,
    "quoted": 38,
    "avg_reply_time_ms": 2500,
    "success_rate": 0.98
  },
  "message": "✅ 统计完成",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

## 📦 订单管理命令

### `orders` - 订单管理

处理订单相关操作。

**用法：**

```bash
python -m src.cli orders --action <action> [options]
```

**Actions：**

| Action | 说明 | 参数 |
|--------|------|------|
| `upsert` | 更新或插入订单 | `--order-id`, `--status`, `--session-id` |
| `deliver` | 发货 | `--order-id`, `--item-type` |
| `trace` | 追踪订单 | `--order-id` |

**示例 1：更新订单状态**

```bash
python -m src.cli orders \
  --action upsert \
  --order-id "O20260305001" \
  --status "已付款" \
  --session-id "S20260305001"
```

**示例 2：虚拟商品发货**

```bash
python -m src.cli orders \
  --action deliver \
  --order-id "O20260305001" \
  --item-type virtual
```

**示例 3：追踪订单**

```bash
python -m src.cli orders \
  --action trace \
  --order-id "O20260305001"
```

**响应：**

```json
{
  "success": true,
  "data": {
    "order_id": "O20260305001",
    "status": "已发货",
    "timeline": [
      {"time": "2026-03-05T09:00:00Z", "event": "下单"},
      {"time": "2026-03-05T09:05:00Z", "event": "付款"},
      {"time": "2026-03-05T09:10:00Z", "event": "发货"}
    ]
  },
  "message": "✅ 订单追踪完成",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

## 🛡️ 合规与增长命令

### `compliance` - 合规检查

内容合规性检查。

**用法：**

```bash
python -m src.cli compliance --action <action> [options]
```

**Actions：**

| Action | 说明 | 参数 |
|--------|------|------|
| `check` | 检查内容合规性 | `--content`, `--account-id`, `--session-id` |
| `replay` | 回放审计日志 | `--blocked-only`, `--limit` |

**示例：**

```bash
python -m src.cli compliance \
  --action check \
  --content "加我微信聊" \
  --account-id "account_1" \
  --session-id "S20260305001"
```

---

### `growth` - 增长实验

A/B 测试和漏斗分析。

**用法：**

```bash
python -m src.cli growth --action <action> [options]
```

**Actions：**

| Action | 说明 | 参数 |
|--------|------|------|
| `assign` | 分配实验组 | `--experiment-id`, `--subject-id`, `--variants` |
| `funnel` | 漏斗分析 | `--days`, `--bucket` |

**示例：**

```bash
python -m src.cli growth \
  --action funnel \
  --days 7 \
  --bucket day
```

---

## 🔧 系统管理命令

### `doctor` - 系统诊断

全面系统健康检查。

**用法：**

```bash
python -m src.cli doctor [--strict] [--skip-gateway] [--skip-quote]
```

**选项：**

| 选项 | 说明 |
|------|------|
| `--strict` | 严格模式（生产环境推荐） |
| `--skip-gateway` | 跳过网关检查 |
| `--skip-quote` | 跳过报价系统检查 |

**示例：**

```bash
# 完整检查
python -m src.cli doctor --strict
```

**响应：**

```json
{
  "success": true,
  "data": {
    "checks": {
      "docker": {"status": "ok", "message": "Docker 运行正常"},
      "python": {"status": "ok", "message": "Python 3.10.12"},
      "cookie": {"status": "ok", "message": "Cookie 有效"},
      "gateway": {"status": "ok", "message": "Gateway 连接正常"},
      "ai_provider": {"status": "ok", "message": "DeepSeek API 可访问"}
    },
    "passed": 5,
    "failed": 0,
    "warnings": 0
  },
  "message": "✅ 所有检查通过",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

### `automation` - 自动化配置

配置自动化和告警。

**用法：**

```bash
python -m src.cli automation --action <action> [options]
```

**Actions：**

| Action | 说明 | 参数 |
|--------|------|------|
| `setup` | 配置自动化 | `--enable-feishu`, `--feishu-webhook` |
| `status` | 查看状态 | - |
| `test-feishu` | 测试飞书告警 | - |

**示例：**

```bash
python -m src.cli automation \
  --action setup \
  --enable-feishu \
  --feishu-webhook "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx"
```

---

### `module` - 模块管理

管理业务模块（售前/运营/售后）。

**用法：**

```bash
python -m src.cli module --action <action> --target <target> [options]
```

**Actions：**

| Action | 说明 |
|--------|------|
| `check` | 检查模块 |
| `status` | 查看状态 |
| `start` | 启动模块 |
| `stop` | 停止模块 |
| `recover` | 恢复模块 |
| `logs` | 查看日志 |
| `cookie-health` | Cookie 健康检查 |

**Targets：**

| Target | 说明 |
|--------|------|
| `all` | 所有模块 |
| `presales` | 售前模块（消息回复、报价） |
| `operations` | 运营模块（擦亮、调价） |
| `aftersales` | 售后模块（订单处理） |

**示例 1：启动售前模块**

```bash
python -m src.cli module \
  --action start \
  --target presales \
  --mode daemon \
  --limit 20 \
  --interval 5
```

**示例 2：查看所有模块状态**

```bash
python -m src.cli module \
  --action status \
  --target all \
  --window-minutes 60
```

**示例 3：恢复模块**

```bash
python -m src.cli module \
  --action recover \
  --target presales \
  --stop-timeout 6
```

---

### `ai` - AI 管理

管理 AI 服务和查看成本统计。

**用法：**

```bash
python -m src.cli ai --action <action>
```

**Actions：**

| Action | 说明 |
|--------|------|
| `cost-stats` | 查看 AI 调用成本统计 |

**示例：**

```bash
python -m src.cli ai --action cost-stats
```

**响应：**

```json
{
  "success": true,
  "data": {
    "total_calls": 1234,
    "total_cost_cny": 45.67,
    "providers": {
      "deepseek": {"calls": 800, "cost": 25.50},
      "anthropic": {"calls": 434, "cost": 20.17}
    }
  },
  "message": "✅ 统计完成",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

## 📋 输出格式规范

### 成功响应

```json
{
  "success": true,
  "data": { ... },           // 业务数据，结构因命令而异
  "message": "操作描述",      // 人类可读的消息
  "timestamp": "ISO8601"     // UTC 时间戳
}
```

### 错误响应

```json
{
  "success": false,
  "data": null,              // 或部分数据
  "message": "错误描述",      // 错误详情
  "error_code": "ERROR_CODE", // 错误代码
  "timestamp": "ISO8601"
}
```

### 常见错误代码

| 错误代码 | 说明 | 解决方案 |
|---------|------|---------|
| `INVALID_PARAMS` | 参数错误 | 检查参数格式和必填项 |
| `AUTH_FAILED` | 认证失败 | 检查 Cookie 是否过期 |
| `RATE_LIMITED` | 请求过快 | 降低请求频率 |
| `NETWORK_ERROR` | 网络错误 | 检查网络连接 |
| `AI_SERVICE_ERROR` | AI 服务错误 | 检查 API Key 和余额 |
| `ITEM_NOT_FOUND` | 商品不存在 | 检查商品 ID |

---

## 💡 使用示例

### 完整工作流：发布商品并监控

```bash
# 1. 检查系统状态
python -m src.cli doctor --strict

# 2. 发布商品
python -m src.cli publish \
  --title "iPhone 15 Pro 256G" \
  --price 5999 \
  --tags "95新 国行"

# 3. 查看数据
python -m src.cli analytics --action dashboard

# 4. 擦亮商品
python -m src.cli polish --all --max 50
```

### 自动化客服工作流

```bash
# 启动售前模块
python -m src.cli module \
  --action start \
  --target presales \
  --mode daemon

# 查看工作流统计
python -m src.cli messages \
  --action workflow-stats \
  --window-minutes 60
```

---

## 📚 相关文档

- 🚀 **快速开始**：[QUICKSTART.md](../QUICKSTART.md)
- 🐳 **部署指南**：[DEPLOYMENT.md](DEPLOYMENT.md)
- 📖 **用户指南**：[USER_GUIDE.md](../USER_GUIDE.md)

---

<p align="center">
  需要更多帮助？提交 <a href="https://github.com/G3niusYukki/xianyu-openclaw/issues">Issue</a>
</p>
