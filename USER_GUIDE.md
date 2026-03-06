# 用户指南

这份文档面向第一次使用当前项目的卖家或运营人员。

## 1. 这个工具能做什么

- 读取工作台状态、Cookie 健康、消息摘要和订单摘要
- 用 AI 生成商品标题、描述和模板图
- 通过闲管家接口创建商品、上架、下架、改价、发货
- 管理账号、Cookie、自动化模块和系统配置
- 查看真实运行日志和部分诊断结果

它不是聊天式 OpenClaw 助手，也不依赖 OpenClaw Gateway 作为默认运行前提。

## 2. 你需要准备什么

- 一台能联网的电脑
- 一个能正常登录的闲鱼账号
- 从浏览器复制出的闲鱼 Cookie
- 一个 AI API Key
- 一个闲管家 Open Platform 应用的 `AppKey/AppSecret`

## 3. 获取 Cookie

1. 打开 `https://www.goofish.com` 并登录。
2. 按 `F12` 打开开发者工具。
3. 切到 `Network`。
4. 刷新页面并点开任意请求。
5. 复制请求头里的整段 `Cookie`。
6. 写入 `.env` 的 `XIANYU_COOKIE_1`，或在前端 `店铺管理` 页面更新。

## 4. 安装和启动

macOS / Linux：

```bash
cp .env.example .env
./start.sh
```

Windows：

```bat
copy .env.example .env
start.bat
```

如果是第一次运行，脚本会创建 Python 虚拟环境并安装前后端依赖。

## 5. 打开页面

- 前端工作台：`http://localhost:5173`
- Python 核心：`http://localhost:8091`
- Node 代理：`http://localhost:3001`

## 6. 页面怎么用

`工作台`
- 看整体状态、Cookie 健康、消息摘要、订单摘要和近期操作。
- 顶部有首次使用配置引导，会检查 Node、Python、AI、闲管家和 Cookie。

`商品管理`
- 查询商品列表。
- 执行上架 / 下架。

`AI 智能自动上架`
- 选择模板，填写商品名和价格。
- 生成文案和预览图。
- 发布到闲管家。

`订单中心`
- 查询订单。
- 待付款订单可改价。
- 待发货订单可发货。

`消息中心`
- 查看真实消息状态和 `presales` 日志。
- 当前不提供本地模拟“手动发送”。

`店铺管理`
- 更新 Cookie。
- 查看账号健康度。
- 启停自动化模块。

`系统配置`
- 配置 AI。
- 配置闲管家。
- 配置自动化运行参数。

`数据分析`
- 查看趋势数据和热门商品。

## 7. 常见问题

### 页面能打开，但多数功能报错

优先检查：

- Python 是否启动：`http://localhost:8091/healthz`
- Node 是否启动：`http://localhost:3001/health`
- `.env` 是否填写了真实值

### 看不到商品或订单

通常是闲管家配置不完整：

- `XGJ_APP_KEY`
- `XGJ_APP_SECRET`
- `XGJ_BASE_URL`

### 自动上架能生成文案，但发布失败

常见原因：

- 闲管家商品接口未授权
- OSS 配置不完整
- 商品参数不满足目标类目要求
- 闲管家账号与 Cookie 对应店铺不一致

### 消息中心为什么没有“手动发送”

这是刻意设计。当前页面只展示真实消息状态和日志，避免引入本地伪发送或 mock 交互。

### Node 关掉后还能不能用

大多数核心数据和主工作台仍以 Python 为主，但推荐保留 Node 一起运行：

- 前端首次配置引导会检查 Node 健康
- webhook 验签和闲管家透传由 Node 负责

## 8. Docker 版

```bash
docker compose up -d --build
docker compose logs -f
```

这会启动 React、Node 和 Python 三个服务。
