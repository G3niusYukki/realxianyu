# 🤝 贡献指南

感谢你对 xianyu-openclaw 项目的兴趣！我们欢迎所有形式的贡献。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境](#开发环境)
- [提交规范](#提交规范)
- [代码审查](#代码审查)
- [发布流程](#发布流程)

---

## 🎯 行为准则

参与本项目即表示你同意：
- 尊重所有参与者
- 接受建设性批评
- 以项目最佳利益为出发点
- 遵守开源社区的基本礼仪

---

## 🚀 如何贡献

### 报告 Bug

在提交 bug 报告前，请先：
1. 搜索现有 Issues，避免重复报告
2. 使用最新的 main 分支进行测试
3. 提供最小可复现步骤

**Bug 报告模板：**

```markdown
**描述**
清晰简洁地描述 bug

**复现步骤**
1. 进入 '...'
2. 点击 '...'
3. 看到错误

**预期行为**
描述你期望发生什么

**截图**
如果适用，添加截图

**环境信息**
- 版本: [e.g. v6.3.4]
- Python: [e.g. 3.12.0]
- 操作系统: [e.g. macOS 14.0]
```

### 功能建议

**功能请求模板：**

```markdown
**功能描述**
清晰描述你想要的功能

**使用场景**
描述这个功能会在什么场景下使用

**可能的实现方案**
如果你有想法，可以描述如何实现

**替代方案**
描述你考虑过的其他解决方案
```

### 提交代码

1. **Fork** 本仓库
2. **Clone** 你的 fork
   ```bash
   git clone https://github.com/YOUR_USERNAME/xianyu-openclaw.git
   cd xianyu-openclaw
   ```
3. **添加上游仓库**
   ```bash
   git remote add upstream https://github.com/G3niusYukki/xianyu-openclaw.git
   ```
4. **创建功能分支**
   ```bash
   git checkout -b feature/amazing-feature
   # 或
   git checkout -b fix/bug-description
   ```
5. **提交更改**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **保持同步**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
7. **推送到你的 fork**
   ```bash
   git push origin feature/amazing-feature
   ```
8. **创建 Pull Request**

---

## 💻 开发环境

### 环境要求

- Python 3.12+
- Docker 20.10+
- Git

### 本地开发设置

```bash
# 1. 克隆仓库
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw

# 2. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 安装 pre-commit 钩子
pre-commit install

# 5. 运行测试
pytest tests/ -v

# 6. 运行 lint
ruff check src/
ruff format --check src/
```

### 代码质量工具

| 工具 | 用途 | 命令 |
|------|------|------|
| ruff | Lint 和格式化 | `ruff check src/` `ruff format src/` |
| pytest | 测试 | `pytest tests/ -v` |
| mypy | 类型检查 | `mypy src/` |
| bandit | 安全扫描 | `bandit -r src/` |

---

## 📝 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

### 提交类型

| 类型 | 描述 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能）|
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖更新 |
| `ci` | CI/CD 配置 |
| `security` | 安全修复 |

### 示例

```bash
# 新功能
feat: add auto-reply template customization

# Bug 修复
fix: resolve cookie expiration detection issue

# 文档更新
docs: update API documentation for orders module

# 性能优化
perf: optimize message deduplication algorithm

# 破坏性变更
feat!: change config file format to YAML

# 带作用域的提交
fix(messaging): handle null content in reply generation
```

### Pull Request 规范

**PR 标题格式：**
```
类型: 简短描述

例如：
feat: add support for multiple AI providers
fix: resolve memory leak in WebSocket client
docs: update deployment guide for Windows
```

**PR 描述模板：**

```markdown
## 描述
<!-- 描述这个 PR 做了什么 -->

## 相关 Issue
<!-- 关联的 Issue，例如 Fixes #123 -->

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 破坏性变更
- [ ] 文档更新

## 测试
<!-- 描述你如何测试这些变更 -->

## 检查清单
- [ ] 代码遵循项目编码规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 所有测试通过
- [ ] 本地 lint 通过
```

---

## 🔍 代码审查

所有代码变更都需要经过审查才能合并。

### 审查标准

- **功能正确性** - 代码是否按预期工作
- **测试覆盖** - 是否有足够的测试
- **代码质量** - 是否遵循项目规范
- **文档** - 相关文档是否更新
- **性能** - 是否引入性能问题
- **安全性** - 是否考虑安全问题

### 审查流程

1. 创建 PR 后，CI 会自动运行测试
2. 维护者会进行代码审查
3. 根据反馈进行修改
4. 获得至少 1 个 Approval 后可以合并

---

## 📦 发布流程

### 版本号规范

我们使用 [SemVer](https://semver.org/lang/zh-CN/) 语义化版本：

- `MAJOR` - 不兼容的 API 变更
- `MINOR` - 向下兼容的功能新增
- `PATCH` - 向下兼容的问题修复

### 发布检查清单

- [ ] 所有测试通过
- [ ] 更新 CHANGELOG.md
- [ ] 更新版本号
- [ ] 创建 Git 标签
- [ ] 创建 GitHub Release
- [ ] 更新 Docker 镜像

---

## 💡 开发建议

### 代码风格

- 遵循 PEP 8 规范
- 使用类型注解
- 编写清晰的文档字符串
- 保持函数简洁（不超过 50 行）

### 测试

- 为新功能编写测试
- 保持测试简单明了
- 使用有意义的测试名称
- 覆盖边界情况

### 文档

- 更新 README 中的相关部分
- 为公共 API 添加文档字符串
- 更新用户指南（如适用）

---

## 🆘 需要帮助？

- 查看 [文档](docs/)
- 加入 [Discussions](https://github.com/G3niusYukki/xianyu-openclaw/discussions)
- 创建 [Issue](https://github.com/G3niusYukki/xianyu-openclaw/issues)

---

感谢你的贡献！🎉
