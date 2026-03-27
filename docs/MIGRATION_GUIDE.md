# XianyuFlow v10 Phase 5: Migration & Rollback Guide

本文档详细说明 XianyuFlow v10 的数据迁移和灰度发布流程。

## 概述

Phase 5 实现零停机迁移：
1. **数据迁移**: SQLite → PostgreSQL
2. **双写过渡**: 新旧数据库同时写入
3. **灰度发布**: 逐步切换流量
4. **应急回滚**: 快速回退到稳定版本

---

## 迁移流程

### 阶段 1: 准备 (Day -1)

```bash
# 1. 备份现有数据
cp data/orders.db data/orders.db.backup.$(date +%Y%m%d)

# 2. 部署 PostgreSQL（已在 Phase 1 完成）
./infra/scripts/setup-local.sh

# 3. 验证 PostgreSQL 连接
kubectl port-forward svc/postgresql 5432:5432 -n xianyuflow
psql -h localhost -U xianyu -d xianyuflow -c "SELECT 1"
```

### 阶段 2: 双写启动 (Day 0)

```bash
# 1. 更新应用配置，启用双写模式
# 修改 config.yaml:
#   database:
#     write_mode: dual_write
#     read_mode: sqlite_only

# 2. 重启应用
kubectl rollout restart deployment/message-service -n xianyuflow

# 3. 验证双写正常工作
kubectl logs -f deployment/message-service -n xianyuflow | grep "dual_write"
```

### 阶段 3: 数据迁移 (Day 0-1)

```bash
# 1. 执行数据迁移（后台运行）
nohup python scripts/migrate_data.py \
  --source sqlite:///data/orders.db \
  --target postgresql://xianyu:xianyu2024@localhost:5432/xianyuflow \
  > migration.log 2>&1 &

# 2. 监控迁移进度
tail -f migration.log

# 3. 验证迁移结果
python scripts/migrate_data.py --validate
```

### 阶段 4: 渐进切换 (Day 1-3)

```bash
# Day 1: 10% 读流量切换到 PostgreSQL
# 修改 config.yaml: read_mode: sqlite_fallback

# Day 2: 50% 读流量
# 观察错误率和延迟

# Day 3: 100% 读流量切换到 PostgreSQL
# 修改 config.yaml: read_mode: pg_fallback
```

### 阶段 5: 完成迁移 (Day 4)

```bash
# 1. 停止写入 SQLite
# 修改 config.yaml: write_mode: pg_only

# 2. 验证所有写入都到了 PostgreSQL
kubectl logs -f deployment/message-service -n xianyuflow | grep "pg_only"

# 3. 清理 SQLite 相关代码（可选）
# 等待一个稳定期后再执行
```

---

## 灰度发布

### 使用原生 K8s Canary

```bash
# 1. 部署 canary 版本
kubectl apply -f k8s/canary-deployment.yaml

# 2. 初始流量 10% 到 canary
kubectl annotate ingress/message-service-ingress \
  nginx.ingress.kubernetes.io/canary-weight="10" \
  -n xianyuflow

# 3. 监控指标
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# 访问 http://localhost:3000

# 4. 逐步增加流量
kubectl annotate ingress/message-service-ingress \
  nginx.ingress.kubernetes.io/canary-weight="25" \
  -n xianyuflow

# 5. 完成发布
kubectl scale deployment/message-service-stable --replicas=0 -n xianyuflow
kubectl annotate ingress/message-service-ingress \
  nginx.ingress.kubernetes.io/canary- -n xianyuflow
```

### 灰度检查清单

- [ ] Error rate < 0.1%
- [ ] P99 latency < 500ms
- [ ] CPU usage < 80%
- [ ] Memory usage < 80%
- [ ] Business metrics normal (orders, messages)

---

## 应急回滚

### 场景 1: 应用故障

```bash
# 快速回滚到上一个版本
./scripts/rollback.sh message-service --force

# 或者回滚所有服务
./scripts/rollback.sh all --force
```

### 场景 2: 数据库问题

```bash
# 1. 立即切换回 SQLite 读取
# 修改 config.yaml: read_mode: sqlite_only

# 2. 停止写入 PostgreSQL
# 修改 config.yaml: write_mode: sqlite_only

# 3. 重启应用
kubectl rollout restart deployment/message-service -n xianyuflow

# 4. 修复 PostgreSQL 问题
# ...

# 5. 重新执行迁移
```

### 场景 3: 数据不一致

```bash
# 1. 比较数据一致性
python -c "
from services.common.xianyuflow_common.dual_write import DualWriteManager
import asyncio

async def check():
    manager = DualWriteManager(
        'data/orders.db',
        'postgresql://xianyu:xianyu2024@localhost:5432/xianyuflow'
    )
    await manager.initialize()
    result = await manager.compare_data('orders')
    print(result)
    await manager.close()

asyncio.run(check())
"

# 2. 修复不一致数据
# 根据比较结果手动修复或使用数据修复脚本
```

---

## 故障排查

### 迁移失败

```bash
# 查看迁移日志
tail -n 100 migration.log

# 检查失败的行
python scripts/migrate_data.py --table orders --dry-run

# 单独迁移特定表
python scripts/migrate_data.py --table orders
```

### 双写不一致

```bash
# 启用详细日志
export DUAL_WRITE_DEBUG=1

# 查看写入差异
kubectl logs -f deployment/message-service | grep "write_diff"
```

### 性能问题

```bash
# 检查 PostgreSQL 慢查询
kubectl exec -it postgresql-0 -n xianyuflow -- psql -U xianyu -c "
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# 检查连接池状态
kubectl exec -it deployment/message-service -n xianyuflow -- wget -qO- http://localhost:8000/metrics | grep db_connections
```

---

## 最佳实践

1. **Always backup**: 迁移前始终备份 SQLite 数据库
2. **Test in staging**: 先在测试环境演练整个流程
3. **Monitor continuously**: 迁移期间保持监控
4. **Keep rollback ready**: 确保随时可以回滚
5. **Communicate**: 迁移期间通知团队成员

---

## 相关脚本

| 脚本 | 用途 |
|------|------|
| `scripts/migrate_data.py` | 数据迁移 |
| `scripts/rollback.sh` | 应急回滚 |
| `k8s/canary-deployment.yaml` | 灰度发布配置 |

---

## 联系方式

迁移期间如有问题，请联系：
- 技术负责人: [TODO]
- 运维值班: [TODO]
