# 部署指南

> XianyuFlow | 闲流 (realxianyu) 生产部署完整方案

---

## 部署方式概览

| 方式 | 适用场景 | 难度 | 依赖 |
|------|---------|------|------|
| **手动部署** | 通用方案 | ⭐ | Python 3.12+ / Node.js 18+ |
| **macOS 后台服务** | Mac 开机自启 | ⭐ | macOS + Python 3.12+ |
| **后台守护运行** | 生产环境 7×24 运行 | ⭐⭐ | Python 3.12+ / Node.js 18+ |

---

## 最小依赖清单

### 必备条件

| 项目 | 说明 | 获取方式 |
|------|------|---------|
| **闲鱼 Cookie** | 登录凭证 | 浏览器 F12 复制，或启动后在管理面板自动获取 |
| **AI API Key** | 自动回复需要 | 推荐 [DeepSeek](https://platform.deepseek.com)（价格低、效果好） |
| **闲管家凭证** | 订单/发货/改价 | [闲管家开放平台](https://open.goofish.pro) 注册应用获取 |

### 可选服务

| 项目 | 说明 | 推荐度 |
|------|------|--------|
| CookieCloud 浏览器扩展 | Cookie 自动同步，防止失效中断 | ⭐⭐⭐ 强烈推荐 |
| 飞书/企微 Webhook | 异常告警通知 | ⭐⭐ 推荐 |
| 阿里云 OSS | 商品图片上传 | ⭐ 按需 |
| BitBrowser 指纹浏览器 | 降低风控概率 | ⭐ 按需 |

---

## 方式一：手动部署（通用方案）

```bash
git clone https://github.com/G3niusYukki/realxianyu.git
cd realxianyu

# 1. Python 环境
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. 前端构建
cd client && npm install && npm run build && cd ..

# 3. 配置
cp .env.example .env
# 编辑 .env 填入 Cookie、AI Key 等

# 4. 启动
python -m src.main
```

Dashboard 地址：**http://localhost:8091**

> 国内环境使用阿里云镜像：`pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`

---

## 方式二：macOS 后台服务

```bash
# 安装（开机自启）
bash scripts/install-launchd.sh

# 卸载
bash scripts/uninstall-launchd.sh
```

使用 macOS LaunchAgent 管理，崩溃自动重启。日志在 `logs/launchd-*.log`。

---

## 方式三：后台守护运行（生产环境）

```bash
# nohup 方式
nohup python -m src.main > logs/app.log 2>&1 &
echo $! > .pid

# 停止
kill $(cat .pid)
```

或使用 systemd（Linux）创建服务单元，实现自动重启和日志管理。

---

## 生产上线清单

### 必做项

- [ ] 填写 `.env` 中的 3 项必填配置（Cookie、AI Key、闲管家凭证）
- [ ] 启动后在管理面板完成首次配置向导
- [ ] 运行 `python -m src.cli doctor` 确认所有关键检查通过
- [ ] 安装 CookieCloud 浏览器扩展，配置 Cookie 自动同步
- [ ] 在「消息 → 对话沙盒」测试自动回复效果
- [ ] 确认报价引擎正常（上传成本表或配置成本 API）

### 推荐项

- [ ] 配置飞书/企微告警 Webhook
- [ ] 设置 `APP_ENV=production`
- [ ] 使用进程守护或 nohup 保证高可用
- [ ] 配置定期数据备份
- [ ] 如对外暴露，在前面加 Nginx 反向代理 + HTTPS

### 安全项

- [ ] 不要在公网直接暴露 8091 端口，使用反向代理
- [ ] 设置独立的 `ENCRYPTION_KEY` 环境变量
- [ ] 生产环境确认 `quote.providers.remote.allow_mock=false`
- [ ] 使用非 root 用户运行

---

## 反向代理配置（Nginx + HTTPS）

如需对外访问或配置域名，建议在本地服务前加一层 Nginx：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Python 后端 (Dashboard + API + 静态资源)
    location / {
        proxy_pass http://127.0.0.1:8091;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API 路由 (如果需要在根路径区分)
    location /api/ {
        proxy_pass http://127.0.0.1:8091;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
    }

    }
```

---

## 数据备份与恢复

### 关键数据文件

| 路径 | 内容 | 重要性 |
|------|------|--------|
| `data/agent.db` | 订单、消息、商品数据 | ⭐⭐⭐ |
| `data/system_config.json` | 管理面板配置 | ⭐⭐⭐ |
| `data/workflow.db` | 消息工作流状态 | ⭐⭐ |
| `data/quote_costs/` | 报价成本表 | ⭐⭐ |
| `.env` | 环境变量配置 | ⭐⭐⭐ |
| `config/config.yaml` | 主配置文件 | ⭐⭐ |

### 手动备份

```bash
# 创建备份
tar -czf backup-$(date +%Y%m%d).tar.gz data/ .env config/config.yaml

# 恢复
tar -xzf backup-20260317.tar.gz
```

### 定时备份（cron）

```bash
# 每天凌晨 2 点备份
0 2 * * * cd /path/to/realxianyu && tar -czf data/backups/backup-$(date +\%Y\%m\%d).tar.gz data/agent.db data/system_config.json data/workflow.db .env
```

---

## 更新升级

```bash
git pull origin main
pip install -r requirements.txt
cd client && npm install && npm run build && cd ..
python -m src.main
```

---

## 故障排查

### 服务无法启动

```bash
# 检查端口占用
lsof -ti:8091 | xargs kill -9   # macOS/Linux
netstat -ano | findstr "8091"          # Windows
```

### Cookie 失效

1. 管理面板「账户管理」→ 点击「自动获取」
2. 或手动从浏览器 F12 复制新 Cookie 粘贴
3. 如已配置 CookieCloud，在浏览器扩展中点击「同步」即可

### 系统诊断

```bash
# 完整诊断
python -m src.cli doctor --strict

# 跳过报价检查（快速诊断）
python -m src.cli doctor --skip-quote
```

### AI 回复异常

1. 检查 AI API Key 是否有效
2. 检查 AI 服务商是否有余额
3. 在管理面板「系统配置 → AI」中测试连接

---

## 架构说明

```
┌─────────────────────────────────────┐
│  浏览器  →  http://localhost:8091   │
└───────────────┬─────────────────────┘
                │
    ┌───────────┴───────────┐
    │  Python 后端 (:8091)  │
    │  ┌───────────────┐   │
    │  │ 静态资源服务   │   │  ← React 构建产物 (client/dist)
    │  │ (Dashboard UI)│   │
    │  └───────┬───────┘   │
    │          │           │
    │  ┌───────┴───────┐   │
    │  │ API 路由       │   │
    │  │ /api/*         │   │
    │  └───────┬───────┘   │
    │          │           │
    │  ┌───────┴───────┐   │
    │  │ 业务模块       │   │
    │  │ ┌───┐ ┌───┐   │   │
    │  │ │WS │ │AI │   │   │  WebSocket → 闲鱼消息
    │  │ │监听│ │回复│   │   │  HTTP → 闲管家 API
    │  │ └───┘ └───┘   │   │  SQLite → 本地存储
    │  │ ┌───┐ ┌───┐   │   │
    │  │ │报价│ │订单│   │   │
    │  │ │引擎│ │履约│   │   │
    │  │ └───┘ └───┘   │   │
    │  └───────────────┘   │
    └───────────────────────┘
```

**说明：**
- Python 后端运行在 **8091** 端口，同时提供 API 和静态资源服务
- React 前端构建后位于 `client/dist/`，由 Python 后端直接托管
- 无需单独的 Node.js 服务运行前端

---

## 获取帮助

- [README.md](../README.md) — 项目概览和功能介绍
- [SECURITY.md](../SECURITY.md) — 安全最佳实践
- [GitHub Issues](https://github.com/G3niusYukki/realxianyu/issues) — 问题反馈
