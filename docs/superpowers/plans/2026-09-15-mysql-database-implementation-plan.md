# MySQL Database Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将秒抢项目的 Docker 默认关系型数据库切换为 MySQL，同时保留 SQLite 本地测试回退。

**Architecture:** 继续使用 SQLAlchemy 统一访问模型层，通过 `DATABASE_URL` 选择数据库方言。Docker Compose 使用 MySQL 8.4，并让 API、Celery Worker 和 Beat 共享同一 MySQL 服务；Redis/Lua 仍负责热点库存预占，数据库继续保存活动、报名、幂等和库存流水。

**Tech Stack:** Python、FastAPI、SQLAlchemy 2、MySQL 8.4、PyMySQL、SQLite、Docker Compose、pytest、Ruff。

## Global Constraints

- MySQL 连接串统一使用 `mysql+pymysql://`。
- 未设置 `DATABASE_URL` 时继续使用 `sqlite:///./miaoqiang.db`。
- 不修改报名接口、库存服务、Redis Lua 脚本和 Celery 任务行为。
- 不新增真实 MySQL 压测数据；本机未启动 MySQL 时只验证配置和 SQLite 回归测试。
- 项目无 Git 仓库，不执行提交；每个任务完成后进行文件状态和测试核验。

---

### Task 1: Add MySQL Configuration Regression Tests

**Files:**
- Create: `backend/tests/test_database_config.py`

**Interfaces:**
- Consumes: `backend/requirements.txt`, `.env.example`, `docker-compose.yml` and the database engine factory exposed by `backend/app/db.py`.
- Produces: Regression tests that fail before the MySQL configuration is implemented and pass afterward.

- [ ] **Step 1: Write the failing tests**

Create tests covering the requested behavior:

```python
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]


def test_pymysql_driver_is_declared():
    requirements = (PROJECT_ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8")
    assert "PyMySQL" in requirements


def test_compose_uses_mysql_as_default_database():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "mysql:8.4" in compose
    assert "mysql+pymysql://app:app@mysql:3306/miaoqiang" in compose
    assert "postgres:" not in compose


def test_env_example_exposes_mysql_settings():
    env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "DATABASE_URL=mysql+pymysql://app:app@mysql:3306/miaoqiang" in env_example
    assert "MYSQL_DATABASE=miaoqiang" in env_example


def test_mysql_engine_enables_connection_health_check():
    from app.db import create_database_engine

    engine = create_database_engine("mysql+pymysql://app:app@mysql:3306/miaoqiang")
    try:
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()
```

- [ ] **Step 2: Run the tests to verify they fail for the expected reason**

Run from `D:\python\秒抢`:

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests/test_database_config.py -q
```

Expected: FAIL because `PyMySQL`, MySQL Compose values and `create_database_engine` are not present yet.

- [ ] **Step 3: Check the failure is a missing implementation failure**

Confirm the failures point to the absent MySQL configuration or engine factory, not to a syntax error or an incorrect test import. Do not change the tests to make the existing implementation pass.

- [ ] **Step 4: Verify the test file is the only new test artifact**

Run:

```powershell
Get-ChildItem backend/tests -Force | Select-Object Name
```

Expected: `test_database_config.py` is present and no generated database or cache file is added by this task.


### Task 2: Adapt the SQLAlchemy Engine and Python Dependency

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/db.py`

**Interfaces:**
- Consumes: `settings.database_url` from `backend/app/core/config.py`.
- Produces: `create_database_engine(database_url: str)` and the module-level `engine` used by the existing application.

- [ ] **Step 1: Add the MySQL driver dependency**

Add this line to `backend/requirements.txt` without removing the existing PostgreSQL driver:

```text
PyMySQL>=1.1
```

- [ ] **Step 2: Implement the minimal engine factory**

Update `backend/app/db.py` so engine construction is centralized:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings


def create_database_engine(database_url: str):
    connect_args = {'check_same_thread': False} if database_url.startswith('sqlite') else {}
    engine_options = {'pool_pre_ping': True} if database_url.startswith(('mysql', 'postgresql')) else {}
    return create_engine(database_url, connect_args=connect_args, **engine_options)


engine = create_database_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Run the new tests to verify the minimal implementation passes**

Run:

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests/test_database_config.py -q
```

Expected: the engine-health-check test and any currently satisfied configuration tests pass; Compose and environment tests remain red until Task 3.

- [ ] **Step 4: Run the existing service tests**

Run:

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests/test_core.py -q
```

Expected: existing inventory, idempotency, JWT and state-transition tests pass using the SQLite fallback.


### Task 3: Switch Docker, Environment Examples and Documentation to MySQL

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `backend/alembic.ini`
- Modify: `README.md`

**Interfaces:**
- Consumes: `create_database_engine`, `DATABASE_URL` and the existing MySQL regression tests.
- Produces: A Docker deployment whose API, Worker and Beat services use MySQL 8.4 by default.

- [ ] **Step 1: Replace the PostgreSQL Compose service**

Change the database service to MySQL 8.4 with `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, port `3306`, volume `mysqldata:/var/lib/mysql`, and a `mysqladmin ping` health check. Update API, Worker and Beat to use `mysql+pymysql://app:app@mysql:3306/miaoqiang`, depend on `mysql` being healthy, and replace the `pgdata` volume with `mysqldata`.

- [ ] **Step 2: Update the environment example**

Replace PostgreSQL variables with:

```text
DATABASE_URL=mysql+pymysql://app:app@mysql:3306/miaoqiang
MYSQL_DATABASE=miaoqiang
MYSQL_USER=app
MYSQL_PASSWORD=app
MYSQL_ROOT_PASSWORD=root
```

Keep the existing Redis, Celery, JWT, monitoring and frontend variables unchanged.

- [ ] **Step 3: Align the Alembic connection example**

Change `backend/alembic.ini` to:

```ini
sqlalchemy.url = mysql+pymysql://app:app@mysql:3306/miaoqiang
```

Do not add migration files because this project currently initializes tables with `Base.metadata.create_all(engine)` and has no Alembic script directory.

- [ ] **Step 4: Update README startup and database wording**

Change the project description to `FastAPI + MySQL/SQLite + Redis/Celery`, document MySQL as the Docker default, and retain this local SQLite example:

```powershell
$env:DATABASE_URL = 'sqlite:///./miaoqiang.db'
$env:PYTHONPATH = '.'
uvicorn app.main:app --reload
```

State that MySQL is used by Compose while SQLite remains a lightweight fallback for local tests.

- [ ] **Step 5: Run the configuration tests**

Run:

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests/test_database_config.py -q
```

Expected: all MySQL configuration tests pass.

- [ ] **Step 6: Validate Compose syntax when Docker is available**

Run:

```powershell
docker compose config --quiet
```

Expected: exit code 0. If Docker is unavailable, report that limitation and use the configuration tests plus manual inspection of rendered service references.


### Task 4: Full Regression and Static Verification

**Files:**
- Verify: `backend/app/db.py`, `backend/tests/test_database_config.py`, `docker-compose.yml`, `.env.example`, `backend/alembic.ini`, `README.md`

**Interfaces:**
- Consumes: all changes from Tasks 1-3.
- Produces: Evidence that SQLite fallback behavior remains intact and the MySQL deployment configuration is internally consistent.

- [ ] **Step 1: Run all backend tests**

Run:

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests -q
```

Expected: existing targeted tests and the new configuration tests pass. Any unrelated pre-existing environment failure must be recorded rather than hidden.

- [ ] **Step 2: Run Ruff**

Run:

```powershell
ruff check backend/app backend/tests
```

Expected: exit code 0.

- [ ] **Step 3: Check database references**

Run:

```powershell
rg -n "postgres:|postgresql|pgdata|POSTGRES_|mysql:8\.4|mysql\+pymysql|mysqldata|MYSQL_" . -g '!frontend/node_modules' -g '!backend/__pycache__'
```

Expected: PostgreSQL references are absent from active default deployment configuration; MySQL references exist in Compose, `.env.example`, dependencies and docs. Existing PostgreSQL driver support in `requirements.txt` may remain because it does not affect the MySQL default.

- [ ] **Step 4: Verify the final file state**

Run:

```powershell
git -C 'D:\python\秒抢' status --short
```

Expected: the listed modified and new files are limited to the MySQL migration scope. Since the directory is not a Git repository, report the command failure and list the exact files checked instead.
