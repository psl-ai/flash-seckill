# 秒抢｜高并发活动报名与库存系统

一个完整的活动报名与库存扣减系统，展示用户认证、活动管理、Redis Lua 原子库存扣减、幂等设计、异步任务和监控告警等后端工程实践。

## 功能特性

- **用户认证与权限**：JWT 登录认证、用户注册、管理员后台
- **活动管理**：活动发布、报名、取消报名、库存调整
- **高并发库存扣减**：Redis Lua 原子预占脚本 + MySQL 唯一约束 + 库存流水，防止超卖、重复报名和重复请求
- **异步任务**：Celery 处理报名异步持久化、预约过期释放、通知和库存校准
- **可观测性**：接入 Prometheus 统计请求量、耗时及报名成功率
- **完整测试**：pytest 覆盖库存、幂等和状态流转核心场景；Locust 并发压测脚本

## 技术栈

| 层级 | 技术选型 |
|---|---|
| 后端 | Python、FastAPI、SQLAlchemy |
| 数据库 | MySQL 8.4（生产）、SQLite（本地开发） |
| 缓存与消息 | Redis、Celery、Lua 脚本 |
| 认证 | JWT |
| 监控 | Prometheus、Grafana |
| 前端 | Next.js、TypeScript |
| 部署 | Docker、Docker Compose |
| 测试 | pytest、Locust |

## 快速开始

### Docker Compose 启动（推荐）

```bash
cp .env.example .env
docker compose up --build
```

- API 文档：http://localhost:8000/docs
- 前端页面：http://localhost:3001
- Prometheus：http://localhost:9090
- Grafana：http://localhost:3000

### 本地后端开发

```bash
cd backend
pip install -r requirements.txt
$env:PYTHONPATH='.'
uvicorn app.main:app --reload
```

无需 MySQL 时可使用 SQLite：

```powershell
$env:DATABASE_URL = 'sqlite:///./miaoqiang.db'
$env:PYTHONPATH = '.'
uvicorn app.main:app --reload
```

## 并发与一致性设计

`backend/app/redis/lua/reserve_stock.lua` 提供 Redis 原子预占脚本，`backend/app/redis/keys.py` 集中维护 Key 规则。报名成功后投递 Celery 任务异步持久化，数据库唯一约束 `(activity_id,user_id)` 和 `(user_id,idempotency_key)` 防止重复落库，库存流水记录每次变更。

压测结果：本地 100 个名额，连续 3 轮模拟 1000 个用户请求，每轮均成功报名 100 次、售罄 900 次，最终库存为 0，无超卖。

## 测试

```bash
# 后端单元测试
$env:PYTHONPATH='backend'; pytest backend/tests -q

# 前端构建检查
cd frontend; npm install; npm run build

# 并发压测
locust -f loadtest/locustfile.py --headless -u 1000 -r 100 --host http://localhost:8000
```

## 项目结构

```
Flash Seckill/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── core/      # 配置、安全
│   │   ├── redis/     # Redis 库存 Lua 脚本
│   │   ├── services/   # 业务逻辑
│   │   ├── tasks/     # Celery 异步任务
│   │   └── routers/    # API 路由
│   └── tests/         # 单元测试
├── frontend/          # Next.js 前端
├── deploy/            # Prometheus/Grafana 配置
├── loadtest/          # Locust 压测脚本
└── docker-compose.yml
```
