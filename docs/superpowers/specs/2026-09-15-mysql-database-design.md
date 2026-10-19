# 秒抢项目切换 MySQL 设计

## 目标

将秒抢项目的 Docker 默认关系型数据库从 PostgreSQL 切换为 MySQL，同时保留 SQLite 作为无外部依赖的本地测试回退。报名业务、Redis/Lua 库存预占和 Celery 任务接口保持不变。

## 方案

- 使用 SQLAlchemy 的 `mysql+pymysql` 驱动连接 MySQL 8.4。
- 将 Docker Compose 的 PostgreSQL 服务替换为 MySQL 服务，统一更新 API、Worker 和 Beat 的数据库连接及健康检查依赖。
- 保留 `DATABASE_URL` 配置入口；未设置时继续使用 `sqlite:///./miaoqiang.db`，方便运行现有单元测试。
- 为 MySQL 连接启用连接池预 ping，避免长时间空闲连接失效；SQLite 继续使用 `check_same_thread=False`。
- 保留现有表模型和唯一约束，不引入与本次目标无关的业务重构或迁移系统改造。

## 文件范围

- `backend/requirements.txt`：增加 PyMySQL 驱动。
- `backend/app/db.py`：补充 MySQL 连接池健康检查配置。
- `docker-compose.yml`：替换数据库服务、环境变量、健康检查、依赖和数据卷。
- `.env.example`：更新为 MySQL 配置，并保留 SQLite 回退说明。
- `backend/alembic.ini`：改为 MySQL 默认连接示例。
- `README.md`：更新启动说明和数据库选择说明。
- `backend/tests/test_database_config.py`：验证数据库 URL 和 Compose 配置的关键约束。

## 验证标准

1. 不设置 `DATABASE_URL` 时，现有 SQLite 核心测试可以运行。
2. 依赖列表包含 PyMySQL，默认 Compose 配置使用 MySQL 8.4，不再依赖 PostgreSQL 服务。
3. API、Worker 和 Beat 使用同一套 MySQL 数据库 URL，并依赖 MySQL 健康检查。
4. Redis/Lua 库存代码和报名业务代码没有行为变化。
5. 如果本机没有 MySQL 服务，不声称已完成真实 MySQL 集成压测；仅验证静态配置和 SQLite 回归测试。
