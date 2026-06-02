# 08 — 首页仪表盘 + 操作日志

> **依赖:** 07-asset-flows
> **目标:** 首页统计卡片 + 待办提醒 + 快捷入口 + 操作日志查询。

---

## Task 1: 后端统计 API

新增 `GET /api/dashboard/stats` 返回资产总数、闲置、已派发、借用中数量。
新增 `GET /api/dashboard/recent-assets` 返回最近新增的 5 条资产。
新增 `GET /api/operation-logs` 分页查询操作日志。

---

## Task 2: 前端 Dashboard.vue

4 个统计卡片 + 最近资产列表 + 快捷入口按钮（参照原型 dashboard.html）。
