# 迁移指南

> 当前仓库中确实存在双写、迁移、回滚和 canary 相关资产，但它们更接近“迁移设计与实验资产”，而不是当前 `main` 默认执行的主线。

## 一、当前判断

以下文件存在：

- `scripts/migrate_data.py`
- `scripts/rollback.sh`
- `k8s/canary-deployment.yaml`
- `services/common/xianyuflow_common/dual_write.py`

但当前 `main` 的默认本地运行方式仍然是：

- SQLite + `src.dashboard_server`
- 可选的 `gateway-service`

因此，本文件应该被理解为：

- 迁移准备说明
- 未来服务化/数据库切换的参考
- 运维演练材料

而不是“现在就推荐所有用户执行”的标准部署步骤。

## 二、什么时候需要看这份文档

- 你在评估 SQLite → PostgreSQL
- 你要理解仓库里为什么存在 dual-write 资产
- 你在做本地 infra 演练
- 你准备验证回滚和 canary 预案

如果你只是要把项目跑起来，请先看：

- `README.md`
- `docs/DEPLOYMENT.md`

## 三、当前可用资产

### 数据迁移

```bash
python scripts/migrate_data.py --help
```

### 应急回滚

```bash
./scripts/rollback.sh --help
```

### Canary 样例

```bash
cat k8s/canary-deployment.yaml
```

## 四、执行前的现实检查

在当前仓库里做迁移演练前，先确认：

1. 你是否真的在使用 PostgreSQL，而不是默认 SQLite 主链路
2. 你是否已经启用了本地 infra 依赖栈
3. 你是否接受这条链路仍偏向实验/演练，而不是稳定生产模板

## 五、建议流程

### 仅做演练

1. 先备份 `data/*.db`
2. 用 `infra/scripts/setup-local.sh` 起依赖
3. 单独执行迁移脚本
4. 校验结果
5. 不直接替换当前主线默认运行方式

### 真正做切换前

1. 补齐实际读写路径梳理
2. 确认 Dashboard 主线是否已经接受目标数据库
3. 准备回滚方案
4. 单独记录演练结果

## 六、当前不应宣称的状态

以下说法在当前 `main` 中不应直接成立：

- “Phase 5 零停机迁移已经是默认主线”
- “当前所有服务已经跑在 PostgreSQL 上”
- “canary 与灰度发布是现成生产方案”

这些内容更适合作为规划和资产储备，而不是既成事实。
