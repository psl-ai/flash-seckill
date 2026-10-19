# 秒抢｜高并发活动报名与库存系统

一个可本地运行的 FastAPI + MySQL/SQLite + Redis/Celery + Next.js 示例项目，展示活动发布、报名、库存扣减、幂等和异步任务等后端工程实践。

Docker Compose 默认使用 MySQL 8.4 持久化业务数据；本地无外部数据库时，可以使用 SQLite 作为轻量测试回退。

## 启动

```bash
cp .env.example .env
docker compose up --build
```

API 文档：`http://localhost:8000/docs`；前端：`http://localhost:3001`；Prometheus：`http://localhost:9090`；Grafana：`http://localhost:3000`。

无需 Docker 的后端开发启动：

```bash
cd backend
pip install -r requirements.txt
$env:PYTHONPATH='.'
uvicorn app.main:app --reload
```

无需 MySQL 时，可在 `backend` 目录使用 SQLite：

```powershell
$env:DATABASE_URL = 'sqlite:///./miaoqiang.db'
$env:PYTHONPATH = '.'
uvicorn app.main:app --reload
```

## 测试

```bash
$env:PYTHONPATH='backend'; pytest backend/tests -q
ruff check backend/app
cd frontend; npm install; npm run build
locust -f loadtest/locustfile.py --headless -u 1000 -r 100 --host http://localhost:8000
```

当前仓库内置单元测试覆盖 JWT、状态流转、库存原子语义、重复报名和幂等冲突。Locust 脚本用于真实环境测量吞吐、成功率和 P95，不能在未启动依赖时伪造结果。

## 并发与一致性说明

`backend/app/redis/lua/reserve_stock.lua` 提供可直接加载到 Redis 的原子预占脚本，`backend/app/redis/keys.py` 集中维护 Key 规则；本地单元测试仍使用线程安全 `InventoryService`，便于无 Redis 环境快速验证。报名成功后会投递 `persist_registration` Celery 任务，未启动 broker 时保留 queued 记录并由后续任务重试。数据库唯一约束 `(activity_id,user_id)` 和 `(user_id,idempotency_key)` 防止重复落库，库存流水记录每次变更。

为控制秋招项目复杂度，仍保留以下边界：真实 Redis 客户端接入、Alembic 版本迁移、分布式限流中间件、任务状态表持久化和完整 RBAC 审计可作为后续迭代；当前代码已提供对应模块入口和接口，便于面试时继续展开。

## 目录

`backend/app` 后端 API、模型和服务；`frontend/src/app` 用户/管理员页面；`deploy` Prometheus/Grafana 配置；`loadtest` 并发脚本。
