# ⚡ 快速入门

5 分钟快速上手 xianyu-openclaw。

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- AI 服务 API Key
- 闲鱼账号 Cookie

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw
```

### 2. 配置环境

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下必需配置：

```bash
# AI 服务（任选其一）
OPENAI_API_KEY=sk-xxx
# 或
DEEPSEEK_API_KEY=sk-xxx

# 闲鱼 Cookie
XIANYU_COOKIE_1=your_cookie_here

# 加密密钥（自动生成或自定义）
ENCRYPTION_KEY=your_secure_key

# 飞书通知（可选）
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
```

### 3. 启动服务

```bash
docker compose up -d
```

### 4. 验证运行

```bash
# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f

# 健康检查
curl http://localhost:8080/healthz
```

### 5. 访问 Dashboard

打开浏览器访问：http://localhost:8080

## 🔧 常用命令

### 启动/停止

```bash
# 启动
docker compose up -d

# 停止
docker compose down

# 重启
docker compose restart

# 查看日志
docker compose logs -f
```

### 诊断工具

```bash
# 一键诊断
python -m src.cli doctor

# 严格模式诊断
python -m src.cli doctor --strict

# 跳过特定检查
python -m src.cli doctor --skip-gateway
```

### 模块管理

```bash
# 启动售前模块
python -m src.cli module --name pre_sales --action start

# 停止模块
python -m src.cli module --name pre_sales --action stop

# 查看状态
python -m src.cli module --name pre_sales --action status

# 重启模块
python -m src.cli module --name pre_sales --action restart
```

## 🐛 常见问题

### 1. 容器启动失败

**问题：** `docker compose up` 报错

**解决：**
```bash
# 检查端口占用
lsof -i :8080

# 检查 Docker 状态
docker ps

# 查看详细日志
docker compose logs openclaw-gateway
```

### 2. Cookie 失效

**问题：** 提示 Cookie 过期

**解决：**
1. 重新获取 Cookie
2. 更新 `.env` 文件
3. 重启服务：`docker compose restart`

### 3. AI 服务报错

**问题：** AI 生成内容失败

**解决：**
1. 检查 API Key 是否正确
2. 检查余额是否充足
3. 查看网络连接

## 📚 下一步

- 📖 [完整使用指南](USER_GUIDE.md)
- 🏗️ [部署文档](docs/DEPLOYMENT.md)
- 🔌 [API 文档](docs/API.md)

## 💡 提示

- 首次启动可能需要 1-2 分钟
- 建议先在小号上测试
- 定期检查日志和告警

---

**遇到问题？** 查看 [FAQ](#) 或创建 [Issue](https://github.com/G3niusYukki/xianyu-openclaw/issues)。
