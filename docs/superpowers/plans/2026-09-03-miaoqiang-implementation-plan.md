# 秒抢系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个可本地运行、可并发压测、具备 Redis 原子库存、异步任务、幂等、限流、RBAC、监控和前端页面的活动报名系统。

**Architecture:** FastAPI 提供统一 REST API，SQLAlchemy 连接 PostgreSQL（测试可切换 SQLite），Redis 承担热点缓存、限流和 Lua 原子预占，Celery + Redis 处理异步持久化、过期释放和校准，Next.js 前端调用真实 API，Prometheus/Grafana 采集监控。

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL 16, Redis 7, Celery, JWT, bcrypt, pytest, pytest-asyncio, httpx, Ruff, mypy, Next.js, TypeScript, Docker Compose, Prometheus, Grafana, Locust.

## Global Constraints

- 报名扣库存必须由 Redis Lua 原子脚本完成，不能使用 Python 层库存判断作为并发控制。
- PostgreSQL 使用事务、CHECK 约束和唯一约束作为最终一致性兜底。
- 相同幂等键重放返回原始结果，不得重复扣库存或创建报名。
- 所有接口使用统一响应/错误格式并携带 request_id。
- 不提交真实密码、密钥或 Token；性能数据只报告实际测试结果。

### Task 1: Backend Core

**Files:** `backend/app/**`, `backend/tests/**`, `backend/pyproject.toml`

实现配置、模型、认证、活动/库存/报名 API、Redis Lua、限流、Celery 任务、Prometheus 指标和单元/接口测试。验收：`pytest backend/tests -q`。

### Task 2: Frontend App

**Files:** `frontend/**`

实现 Next.js + TypeScript 页面、认证状态、自动刷新 Token、报名 loading/错误状态、管理员页面和真实 API 客户端。验收：`npm run build`。

### Task 3: Deployment And Observability

**Files:** `docker-compose.yml`, `.env.example`, `deploy/**`, `README.md`

提供 api/worker/beat/postgres/redis/prometheus/grafana/frontend 服务、健康检查、启动顺序、监控配置、API 文档和运行说明。

### Task 4: Load Test And Final Verification

**Files:** `loadtest/locustfile.py`, `backend/tests/test_concurrency.py`

提供库存 100、1000 并发报名脚本和结果采集逻辑；运行 pytest、ruff、mypy、前端构建，记录真实结果和限制。
