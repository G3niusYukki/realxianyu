# 快速开始指南

> 🚀 5分钟内启动你的闲鱼 AI 助手

---

## 📋 环境要求

在开始之前，请确保你已准备好：

| 需求 | 说明 | 是否必须 |
|------|------|---------|
| **Docker** | 20.10+ 版本 | ✅ 必须 |
| **Docker Compose** | 随 Docker Desktop 安装 | ✅ 必须 |
| **AI API Key** | Anthropic / OpenAI / Moonshot / MiniMax / ZAI 任选一个 | ✅ 必须 |
| **闲鱼 Cookie** | 从浏览器获取的登录凭证 | ✅ 必须 |
| **Python 3.10+** | 仅在使用 Lite 模式时需要 | ❌ 可选 |

---

## 🚀 三步启动

### 第 1 步：克隆项目

```bash
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw
```

### 第 2 步：配置环境

```bash
# 复制环境变量模板
cp .env.example .env
```

编辑 `.env` 文件，填入以下必需信息：

```bash
# === 网关 AI 配置（至少填一个）===
ANTHROPIC_API_KEY=sk-ant-api03-...          # Anthropic Claude
OPENAI_API_KEY=sk-...                       # OpenAI
MOONSHOT_API_KEY=sk-...                     # Moonshot (Kimi)
MINIMAX_API_KEY=...                         # MiniMax
ZAI_API_KEY=...                             # 智谱 ZAI

# === OpenClaw 网关配置 ===
OPENCLAW_GATEWAY_TOKEN=your-secret-token    # 任意自定义密钥
OPENCLAW_WEB_PORT=8080                      # Web 界面端口
AUTH_PASSWORD=changeme                      # 登录密码
AUTH_USERNAME=admin                         # 登录用户名

# === 闲鱼 Cookie ===
XIANYU_COOKIE_1=your_cookie_here            # 主账号 Cookie
XIANYU_COOKIE_2=                            # 第二个账号（可选）

# === 业务文案 AI（可选，推荐 DeepSeek）===
AI_PROVIDER=deepseek
AI_API_KEY=sk-...
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
```

**获取闲鱼 Cookie 的方法：**

1. 用 Chrome 打开 [https://www.goofish.com](https://www.goofish.com) 并登录
2. 按 **F12** 打开开发者工具
3. 切换到 **Network（网络）** 标签
4. 按 **F5** 刷新页面
5. 点击任意一个请求
6. 在右侧 **Request Headers** 中找到 `Cookie:` 一行
7. 全部复制并粘贴到 `.env` 文件中

### 第 3 步：启动服务

```bash
docker compose up -d
```

等待约 30 秒，让服务完全启动。

---

## 🪟 Windows 一键部署（推荐小白用户）

如果你使用 Windows，可以直接使用图形化工具，无需命令行：

### 方式 1：下载 EXE 工具

1. 访问 [Releases 页面](https://github.com/G3niusYukki/xianyu-openclaw/releases/latest)
2. 下载 `xianyu-openclaw-launcher.zip`
3. 解压到任意位置（如桌面）
4. 双击 `xianyu-openclaw-launcher.exe`
5. 按向导步骤操作：
   - **第 1 步**：检测 Docker 安装
   - **第 2 步**：选择 AI 服务并填入 API Key
   - **第 3 步**：设置登录密码
   - **第 4 步**：粘贴闲鱼 Cookie
   - **第 5 步**：一键启动

### 方式 2：使用批处理脚本

```bat
# 快速启动（安装 + 检查 + 启动）
scripts\windows\quickstart.bat

# 或使用菜单式启动器
scripts\windows\launcher.bat
```

---

## ✅ 验证启动

### 1. 检查容器状态

```bash
docker compose ps
```

应该看到 `xianyu-openclaw` 容器处于 `Up (healthy)` 状态。

### 2. 访问 Web 界面

打开浏览器访问：**http://localhost:8080**

- 用户名：`admin`（或你在 `.env` 中设置的 `AUTH_USERNAME`）
- 密码：你在 `.env` 中设置的 `AUTH_PASSWORD`

### 3. 网关配对（首次启动可能需要）

如果看到 `pairing required` 提示，运行：

```bash
# 查看配对请求
docker compose exec -it openclaw-gateway openclaw devices list

# 批准配对（将 <requestId> 替换为实际的请求 ID）
docker compose exec -it openclaw-gateway openclaw devices approve <requestId>
```

---

## 🎯 快速测试

登录 Web 界面后，尝试以下对话命令：

```
你: 帮我发布一个 iPhone 15 Pro，价格 5999，95新
AI: ✅ 已发布！标题：【自用出】iPhone 15 Pro 256G 原色钛金属 95新
    链接：https://www.goofish.com/item/xxx
```

```
你: 擦亮所有商品
AI: ✅ 已擦亮 23 件商品
```

```
你: 今天卖得怎么样？
AI: 📊 今日浏览 1,247 | 想要 89 | 成交 12 | 营收 ¥38,700
```

---

## 🔧 故障排查

### 问题 1：Docker 未运行

**症状**：`Cannot connect to the Docker daemon`

**解决**：
- Windows/macOS：打开 Docker Desktop 应用
- Linux：`sudo systemctl start docker`

### 问题 2：端口 8080 被占用

**症状**：`Bind for 0.0.0.0:8080 failed: port is already allocated`

**解决**：
1. 修改 `.env` 文件中的 `OPENCLAW_WEB_PORT`，例如改为 `8081`
2. 重新启动：`docker compose up -d`

### 问题 3：Cookie 失效

**症状**：无法获取闲鱼数据，或提示认证失败

**解决**：
1. 重新获取闲鱼 Cookie（有效期通常 7-30 天）
2. 更新 `.env` 文件
3. 重启服务：`docker compose restart`

### 问题 4：AI 服务报错

**症状**：AI 回复异常或超时

**解决**：
1. 检查 API Key 是否正确
2. 检查 API Key 余额是否充足
3. 查看网关日志：`docker compose logs -f openclaw-gateway`

---

## 📊 查看运行状态

### 诊断工具

```bash
# 运行完整诊断
python -m src.cli doctor --strict

# 检查模块状态
python -m src.cli module --action status --target all
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志（实时）
docker compose logs -f openclaw-gateway

# 查看最近 100 行
docker compose logs --tail 100
```

### 数据看板

启动独立的数据看板：

```bash
python -m src.dashboard_server --port 8091
```

然后访问：**http://localhost:8091**

---

## 🛑 停止服务

```bash
# 停止服务（保留数据）
docker compose down

# 停止服务并删除数据（谨慎使用）
docker compose down -v
```

---

## 📚 下一步

- 📖 **详细使用指南**：查看 [USER_GUIDE.md](USER_GUIDE.md)
- 🚀 **生产部署**：查看 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- 🔧 **CLI 命令参考**：查看 [docs/API.md](docs/API.md)
- 🛠️ **参与开发**：查看 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 💡 提示

- **首次启动**：可能需要 1-2 分钟下载 Docker 镜像
- **Cookie 更新**：定期更新 Cookie 以避免失效
- **备份数据**：定期备份 `data/` 目录
- **监控告警**：配置飞书 webhook 接收告警通知

---

<p align="center">
  遇到问题？查看 <a href="USER_GUIDE.md">详细用户指南</a> 或提交 <a href="https://github.com/G3niusYukki/xianyu-openclaw/issues">Issue</a>
</p>
