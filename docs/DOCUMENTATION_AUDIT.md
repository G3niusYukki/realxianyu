# Documentation Audit Report

**Project:** XianyuFlow | 闲流  
**Repository:** https://github.com/G3niusYukki/realxianyu  
**Refresh Date:** 2026-03-27

## Summary

这份文档现在只保留“文档一致性审计”的作用，不再把已经修正过的问题继续写成待办。

本轮刷新后，已明确修正的重点包括：

- 运行入口区分为 `8091` Dashboard 与 `8000` Gateway
- `8000` 不再被描述为前端页面入口
- `services/helm/xianyuflow` 不存在这一事实已回写到 README/部署文档
- `dashboard_server` 仍是当前主线入口这一事实已回写到架构/部署/API 文档
- 迁移、K8s、灰度发布相关内容已降级为“资产/计划/演练”，不再冒充默认主线

## Current High-Risk Drift Areas

### 1. 计划文档与实现的天然差异

以下文档本质上是规划，不应按“已实现”理解：

- `docs/PLAN-UI-REFACTOR.md`
- `docs/PROJECT_PLAN.md`
- `docs/PROJECT_MINDMAP_CLEAR_V1.md`

### 2. 第三方原始接入文档

`docs/xianguanjiajieruapi.md` 主要是第三方接入说明镜像。它可以作为协议参考，但不应被当成仓库内部部署文档。

### 3. 服务化资产与当前主线并存

仓库同时存在：

- `src/dashboard_server.py` 主线
- `services/` 服务化代码
- `infra/` 基础设施资产

这三者并存是当前仓库最大的文档误导源。今后新增文档时，必须先声明自己描述的是：

- 当前主线运行时
- 服务化方向
- 还是基础设施演练

## Rules For Future Updates

1. 如果文档提到端口，必须明确 `8091 / 8000 / 5173` 的职责。
2. 如果文档提到 K8s / Helm，必须先确认仓库里对应路径真的存在。
3. 如果文档提到“当前主线”，必须优先对齐 `src.dashboard_server`。
4. 如果文档是计划或审计，应显式写出“不是现状”。
