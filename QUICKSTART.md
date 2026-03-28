# 快速开始

5 分钟内启动 XianyuFlow | 闲流。

---

## 快速开始（Docker）

    git clone https://github.com/G3niusYukki/realxianyu.git && cd realxianyu
    cp .env.example .env   # 编辑填写必要配置
    docker-compose up -d
    # 访问 http://localhost:8091

---

## 前提条件

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.12+ | 后端运行时 |
| Node.js | 18+ | 构建 React 前端 |
| Chrome / Edge | 任意版本 | Cookie 自动获取需要本机浏览器 |

---

## 启动步骤

### 第 1 步：克隆项目

```bash
git clone https://github.com/G3niusYukki/realxianyu.git
cd realxianyu
```

### 第 2 步：安装依赖

```bash
# Python 依赖
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 前端依赖 & 构建
cd client && npm install && npm run build && cd ..
```

> Windows 用 `venv\Scripts\activate` 替代 `source venv/bin/activate`。

### 第 3 步：配置

```bash
cp .env.example .env
```

编辑 `.env`，填入必要参数：

- **`XIANYU_COOKIE_1`** — 闲鱼 Cookie（必须，见下方获取方法）
- **AI 相关** — `AI_PROVIDER` / `AI_API_KEY` / `AI_MODEL`（可选，也可稍后在管理面板配置）

### 第 4 步：启动

```bash
python -m src.dashboard_server --host 127.0.0.1 --port 8091
```

Dashboard 地址：**http://localhost:8091**

### 第 5 步：验证

```bash
curl http://127.0.0.1:8091/healthz
python -m src.cli doctor --skip-quote
```

---

## 获取闲鱼 Cookie

1. 用 Chrome 打开 https://www.goofish.com 并登录
2. 按 **F12** → **Network** 标签 → **F5** 刷新页面
3. 点击任意请求 → **Request Headers** → 找到 `Cookie:` 行
4. 复制全部 Cookie → 粘贴到 `.env` 的 `XIANYU_COOKIE_1=`

Cookie 有效期 7-30 天，过期后通过管理面板在线更新。

---

## 首次使用

1. 打开 http://localhost:8091 → Dashboard
2. 账户页 → 粘贴闲鱼 Cookie 或使用自动获取
3. 系统配置 → AI 配置 → 选择 provider 并填入 API Key
4. 消息页 → 对话沙盒 → 测试自动回复效果
5. 确认无误后 → 开启自动回复

### AI 配置推荐

| 提供商 | 模型 | 说明 |
|--------|------|------|
| 百炼千问 (Qwen) | qwen-plus-latest | **推荐** 中文电商，国内直连 |
| DeepSeek | deepseek-chat | 通用场景，国内直连 |
| OpenAI | gpt-4o-mini | 英文/多语言，需代理 |

---

## 国内环境

```bash
# pip 使用阿里云源
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# npm 使用 npmmirror
npm config set registry https://registry.npmmirror.com
```

AI 服务推荐使用国内供应商（百炼千问、DeepSeek），无需外网。

---

## 辅助脚本

| 脚本 | 说明 |
|------|------|
| `scripts/unix/doctor.sh` | 系统诊断 |
| `scripts/unix/dashboard.sh` | 启动 Dashboard |
| `scripts/install-launchd.sh` | macOS 开机自启服务 |
| `scripts/backup_data.sh` | 数据备份 |
| `scripts/update.sh` | 更新项目 |

---

## 常见问题

### 端口被占用

```bash
lsof -ti :8091 | xargs kill -9
```

### Cookie 失效

1. 保持本机 Chrome 登录闲鱼
2. 通过管理面板 → 账户页手动更新
3. 多次失败可能需要在闲鱼 App 完成安全验证

### npm install 失败

```bash
node -v                    # 确认 >= 18
npm cache clean --force
npm install
```

### doctor 提示 5173 未监听

这是前端开发代理端口，不影响生产运行。只要 `http://localhost:8091/healthz` 正常且 `client/dist/` 已构建，就可以继续使用。

---

## 下一步

- 详细使用指南：[USER_GUIDE.md](USER_GUIDE.md)
- 完整功能说明：[README.md](README.md)
- 生产部署：[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- CLI 命令参考：`python -m src.cli --help`
- 参与开发：[CONTRIBUTING.md](CONTRIBUTING.md)
