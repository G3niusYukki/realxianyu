# 用户指南

这份文档给第一次接触本项目的使用者看，重点解释：这个系统现在能做什么、怎么启动、每天怎么用。

---

## 1. 这个项目现在能帮你做什么？

当前版本的 Xianyu OpenClaw 不是单一功能脚本，而是一套完整的闲鱼卖家自动化工作台，主要覆盖：

- 买家消息自动回复
- 自动报价与缺参追问
- 议价识别与跟进
- 订单同步、售后跟进、实物物流发货
- 虚拟商品回调处理与调度
- 闲管家开放平台接入
- Cookie 健康检查
- 可视化配置中心与状态面板

如果你只想快速理解它：

> **它是一套把“消息、报价、订单、履约、配置、监控”放在一起的闲鱼自动化后台。**

---

## 2. 你需要准备什么？

| 项目 | 说明 |
|------|------|
| 电脑 / 服务器 | Windows、macOS、Linux 均可 |
| Python 3.10+ | Python 核心后端 |
| Node.js 18+ | 前端与 Node API |
| 浏览器 | Chrome / Edge，方便 Cookie 获取 |
| 闲鱼 Cookie | 登录凭证 |
| AI API Key | 自动回复 / 内容生成 |
| 闲管家 AppKey / Secret | 如需开放平台能力 |

---

## 3. 安装与启动

### 最简单的方法

```bash
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw
cp .env.example .env

# macOS / Linux
./start.sh

# Windows
start.bat
```

启动后访问：

| 服务 | 地址 |
|------|------|
| 前端工作台 | http://localhost:5173 |
| Python Dashboard | http://localhost:8091 |
| Node 健康检查 | http://localhost:3001/health |
| Python 健康检查 | http://localhost:8091/healthz |

---

## 4. `.env` 里要填什么？

最低限度建议这样配置：

```bash
XIANYU_COOKIE_1=your_cookie_here

AI_PROVIDER=deepseek
AI_API_KEY=your_api_key
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

XGJ_APP_KEY=
XGJ_APP_SECRET=
```

说明：

- `XIANYU_COOKIE_1`：闲鱼登录态
- `AI_*`：业务 AI 配置
- `XGJ_*`：闲管家配置

---

## 5. 如何获取 Cookie？

1. 打开 Chrome / Edge 并登录闲鱼
2. 按 F12 打开开发者工具
3. 进入 Network
4. 刷新页面
5. 选择任意一个 goofish 请求
6. 在 Request Headers 中复制整行 Cookie
7. 填入 `.env` 的 `XIANYU_COOKIE_1`

如果后续失效，重新复制并更新即可。

---

## 6. 日常会用到哪些页面？

### 前端工作台（`http://localhost:5173`）

适合日常使用：

- 系统配置
- Cookie 管理
- AI 服务设置
- 闲管家设置
- 订单和消息相关页面
- 模块状态查看

### Python Dashboard（`http://localhost:8091`）

适合运维与高级调试：

- 健康状态
- Dashboard API
- 模块状态
- 回调与配置状态

---

## 7. 当前版本有哪些值得注意的新能力？

### 闲管家控制面板

当前版本已经把闲管家配置放进 Dashboard，支持：

- AppKey / AppSecret 保存
- 自动改价开关
- 自动发货开关
- 支付后自动触发开关

### 订单回调

现在支持订单支付后回调入口：

```text
/api/orders/callback
```

这让订单同步和自动履约链路更完整。

### 手动重试

Dashboard 中已加入：

- API 改价手动重试
- API 发货手动重试

### 模块化运行

可以把售前、运营、售后拆开运行，更适合长期值守。

---

## 8. 常用命令

### 做一次全量体检

```bash
python -m src.cli doctor --strict
```

### 查看模块状态

```bash
python -m src.cli module --action status --target all
```

### 启动售前模块

```bash
python -m src.cli module --action start --target presales --mode daemon --background
```

### 查看模块日志

```bash
python -m src.cli module --action logs --target all --tail-lines 100
```

### 检查报价能力

```bash
python -m src.cli quote --action health
```

---

## 9. 常见问题

### 9.1 页面打不开

先检查三个服务是否启动。

```bash
curl http://localhost:3001/health
curl http://localhost:8091/healthz
```

### 9.2 AI 不回复

检查：

- `AI_API_KEY` 是否有效
- `AI_BASE_URL` 是否可访问
- Cookie 是否过期

### 9.3 Cookie 过期

重新登录闲鱼，复制新的 Cookie，再重启服务。

### 9.4 闲管家链路不生效

优先确认：

- `XGJ_APP_KEY`
- `XGJ_APP_SECRET`
- 回调路径是否可达
- Dashboard 中对应开关是否已启用

### 9.5 想分模块运行

直接使用 `src.cli module` 子命令即可，不需要自己写守护脚本。

---

## 10. 更新项目

```bash
git pull origin main
```

然后重新执行：

- 本地：`./start.sh` 或 `start.bat`
- Docker：`docker compose down && docker compose up -d --build`

---

## 11. 安全提醒

- Cookie 和 API Key 不要泄露
- 回调地址对外暴露时要配合反向代理和访问控制
- 自动回复内容要遵守平台规则
- 频繁操作前建议先在测试环境验证

---

## 12. 你接下来应该看什么？

- 想快速跑起来：看 [QUICKSTART.md](QUICKSTART.md)
- 想了解整体能力：看 [README.md](README.md)
- 想部署到长期环境：看 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- 想看版本变化：看 [CHANGELOG.md](CHANGELOG.md)

---

**文档线版本：7.2.0**
